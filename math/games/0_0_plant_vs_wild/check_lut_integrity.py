"""Contrôle exhaustif Book ↔ lookup table — OUTIL DE DÉVELOPPEMENT.

Il répond à une seule question, sans tolérance : la lookup table publiée
décrit-elle EXACTEMENT les books produits par le Math ?

C'est le garde-fou contre le défaut connu de l'optimizer Stake, qui peut écrire
dans la lookup table des payouts absents des simulations. Un tel écart rendrait
la publication invalide.

    python games/0_0_plant_vs_wild/check_lut_integrity.py base

Sortie : 0 si tout concorde, 1 sinon.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402


def read_books(path):
    """Lit les books compressés et renvoie {id: payoutMultiplier} (en centièmes)."""
    decompressor = zstandard.ZstdDecompressor()
    payouts = {}
    with open(path, "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    book = json.loads(line)
                    payouts[int(book["id"])] = int(book["payoutMultiplier"])
        if buffer.strip():
            book = json.loads(buffer)
            payouts[int(book["id"])] = int(book["payoutMultiplier"])
    return payouts


def read_lut(path):
    """Lit la lookup table publiée : [(id, weight, payout)]."""
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            sim_id, weight, payout = line.strip().split(",")
            rows.append((int(sim_id), int(weight), int(float(payout))))
    return rows


def check(mode: str) -> int:
    config = GameConfig()
    lut_path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
    book_path = os.path.join(config.publish_path, f"books_{mode}.jsonl.zst")

    for path in (lut_path, book_path):
        if not os.path.exists(path):
            print(f"absent : {path}")
            return 1

    books = read_books(book_path)
    rows = read_lut(lut_path)

    missing_ids = []
    payout_mismatch = []
    for sim_id, _weight, payout in rows:
        if sim_id not in books:
            missing_ids.append(sim_id)
        elif books[sim_id] != payout:
            payout_mismatch.append((sim_id, books[sim_id], payout))

    lut_payouts = {payout for _, _, payout in rows}
    book_payouts = set(books.values())
    synthetic = sorted(lut_payouts - book_payouts)

    # Le RTP d'un bet mode est sa moyenne de payout RAPPORTEE A SON COUT
    # (`calculate_rtp` du SDK). Diviser seulement par 100 donnait un RTP de 96
    # pour le Bonus Buy, qui coute 100x : juste au facteur pres, faux a lire.
    cost = next(b.get_cost() for b in config.bet_modes if b.get_name() == mode)
    total_weight = sum(weight for _, weight, _ in rows)
    weighted_rtp = (
        sum(weight * payout for _, weight, payout in rows) / total_weight / 100.0 / cost
        if total_weight
        else 0.0
    )

    print(f"mode                  {mode}   (cout {cost:.0f}x)")
    print(f"lignes LUT            {len(rows)}")
    print(f"books                 {len(books)}")
    print(f"sim_id manquants      {len(missing_ids)}")
    print(f"payouts divergents    {len(payout_mismatch)}")
    print(f"payouts synthetiques  {len(synthetic)}")
    print(f"somme des poids       {total_weight}")
    print(f"WEIGHTED LUT RTP      {weighted_rtp:.6f}")

    for sim_id, book_payout, lut_payout in payout_mismatch[:10]:
        print(f"   sim {sim_id} : book {book_payout} != lut {lut_payout}")
    for payout in synthetic[:10]:
        print(f"   payout synthetique absent des books : {payout}")

    ok = not missing_ids and not payout_mismatch and not synthetic
    print("INTEGRITE             " + ("OK" if ok else "ECHEC"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(check(sys.argv[1] if len(sys.argv) > 1 else "base"))
