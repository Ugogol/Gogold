"""Aide au calcul des allocations de fences — OUTIL DE DÉVELOPPEMENT.

L'optimizer ne peut pas atteindre un `av_win` que sa population ne contient pas.
Ce script confronte donc chaque cible au PERCENTILE qu'elle occupe réellement
dans les Books de sa fence : une cible au 50e percentile est neutre, une cible
au 95e oblige l'optimizer à écraser toute la fence sur son extrémité haute.

Il ne décide rien et n'écrit rien. Il dit seulement ce qui est atteignable.

    python games/0_0_plant_vs_wild/plan_fences.py
"""

import json
import os
import sys
from bisect import bisect_left
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402

#: Profil visé. Fréquence du Bonus, puis part de chaque bucket DANS les Bonus.
BONUS_HIT = 78.0
SHARES = {"low": 0.70, "medium": 0.19, "medium_long": 0.01, "high": 0.08, "mega": 0.02}

#: Base Game : fréquence et RTP. Le reste du budget va au Bonus.
BASEGAME_HIT = 12.5
WINCAP_RTP = 0.001


def read_population():
    config = GameConfig()
    force_path = os.path.join(config.library_path, "forces", "force_record_base.json")
    bucket_of = {}
    with open(force_path, encoding="utf-8") as handle:
        for entry in json.load(handle):
            keys = {k["name"]: k["value"] for k in entry["search"]}
            if "bucket" in keys:
                for book_id in entry["bookIds"]:
                    bucket_of[book_id] = (keys["bucket"], keys.get("retrigger"))

    payouts = defaultdict(list)
    decompressor = zstandard.ZstdDecompressor()
    with open(os.path.join(config.publish_path, "books_base.jsonl.zst"), "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                book = json.loads(line)
                payout = book["payoutMultiplier"] / 100.0
                if payout >= config.wincap:
                    payouts["wincap"].append(payout)
                    continue
                key = bucket_of.get(book["id"])
                if key is not None:
                    name, retrigger = key
                    if name == "medium":
                        name = "medium_long" if retrigger == "yes" else "medium"
                    payouts[name].append(payout)
                elif payout > 0:
                    payouts["basegame"].append(payout)
    for values in payouts.values():
        values.sort()
    return config, payouts


def percentile_of(values, target):
    """Part des Books de la fence en dessous de la cible."""
    return bisect_left(values, target) / len(values) * 100 if values else float("nan")


def main():
    config, payouts = read_population()
    basegame_rtp = float(sys.argv[1]) if len(sys.argv) > 1 else 0.16
    averages = {
        "low": float(sys.argv[2]) if len(sys.argv) > 2 else 8.0,
        "medium": float(sys.argv[3]) if len(sys.argv) > 3 else 35.0,
        "medium_long": float(sys.argv[4]) if len(sys.argv) > 4 else 45.0,
        "high": float(sys.argv[5]) if len(sys.argv) > 5 else 195.0,
    }

    rows = []
    allocated = basegame_rtp + WINCAP_RTP
    for name in ("low", "medium", "medium_long", "high"):
        hr = BONUS_HIT / SHARES[name]
        rtp = averages[name] / hr
        allocated += rtp
        rows.append((name, hr, rtp, averages[name]))

    mega_hr = BONUS_HIT / SHARES["mega"]
    mega_rtp = config.rtp - allocated
    mega_avg = mega_rtp * mega_hr
    rows.append(("mega", mega_hr, mega_rtp, mega_avg))
    rows.append(("basegame", BASEGAME_HIT, basegame_rtp, basegame_rtp * BASEGAME_HIT))
    rows.append(("wincap", config.wincap / WINCAP_RTP, WINCAP_RTP, config.wincap))

    print(f"Budget RTP {config.rtp}   Bonus 1/{BONUS_HIT:.0f}   Base 1/{BASEGAME_HIT}\n")
    print(f"{'fence':13} {'1 sur':>9} {'rtp':>9} {'av_win vise':>12} "
          f"{'mediane pop':>12} {'moyenne pop':>12} {'percentile':>11}")
    total_rtp = 0.0
    for name, hr, rtp, av_win in rows:
        values = payouts.get(name, [])
        total_rtp += rtp
        median = values[len(values) // 2] if values else float("nan")
        mean = sum(values) / len(values) if values else float("nan")
        pct = percentile_of(values, av_win)
        flag = "" if pct <= 90 else "   <<< tres haut"
        print(f"{name:13} {hr:9.1f} {rtp:9.6f} {av_win:12.2f} "
              f"{median:12.2f} {mean:12.2f} {pct:10.1f}%{flag}")
    print(f"{'SOMME':13} {'':>9} {total_rtp:9.6f}")

    prob = sum(1 / (BONUS_HIT / s) for s in SHARES.values()) + 1 / BASEGAME_HIT
    print(f"\nparis payants {prob*100:.2f} %   ->  paris perdants {(1-prob)*100:.2f} %")

    # Retrigger : impose par la forme, sauf pour `medium_long` qui le pilote.
    rates = {"low": 3.02, "medium": 0.0, "medium_long": 100.0, "high": 79.81, "mega": 98.48}
    retrigger = sum(SHARES[n] * rates[n] for n in SHARES)
    print(f"retrigger attendu (avant effet de l'optimizer) : {retrigger:.2f} %")


if __name__ == "__main__":
    main()
