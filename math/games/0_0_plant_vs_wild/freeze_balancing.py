"""Gèle une version de balancing et en extrait huit Books représentatifs.

POURQUOI CE SCRIPT EXISTE
-------------------------
`math/.gitignore` ignore tout `**/library/**` : la lookup table, les books
publiés, les force records et `math_config.json` ne sont PAS versionnés. Seules
leurs sources le sont. On ne peut donc pas « pointer » la LUT de V4 dans Git —
il faut l'identifier par son empreinte, et pouvoir vérifier plus tard qu'elle
n'a pas bougé.

Le nom de version vit dans `VERSION` : une nouvelle version de balancing se
gèle en changeant cette constante, pas en dupliquant le script.

Ce fichier répond aux trois questions du gel :

    Quels fichiers définissent cette version ?   -> `sources`, versionnés
    Quelle LUT correspond à V4 ?                -> `artefacts`, par empreinte
    Quels Books correspondent à cette LUT ?     -> `books`, extraits ici

EXTRACTION, PAS SIMULATION
--------------------------
`make_books.py` REJOUE des spins pour fabriquer ses books canoniques. Ce
script ne rejoue rien : il LIT la population réellement pondérée par la LUT V4
et en prélève huit books tels quels. Aucun payout, aucun event, aucun plafond
n'est fabriqué — un book extrait est bit pour bit celui que le RGS servirait.

Pour chaque criteria on retient le book le PLUS COURT, pour garder le playback
lisible en debug.

    python games/0_0_plant_vs_wild/freeze_balancing.py     (depuis math/)
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, "canonical_books")

#: Version gelée par ce script. Elle nomme le fichier de gel ET le préfixe des
#: Books extraits : aucun mélange de versions n'est possible dans le dossier.
VERSION = "V5"
PREFIX = VERSION.lower()
FREEZE_FILE = os.path.join(OUTPUT_DIR, f"BALANCING_{VERSION}.json")

#: Fichiers VERSIONNÉS qui définissent le candidat. Les régénérer à partir de
#: ceux-ci doit redonner la même LUT : c'est ce que leurs empreintes garantissent.
SOURCE_FILES = [
    "game_config.py",
    "game_optimization.py",
    "game_override.py",
    "game_executables.py",
    "game_calculations.py",
    "game_events.py",
    "gamestate.py",
    "reels/BR0.csv",
    "reels/BR1.csv",
    "reels/FR0.csv",
    "reels/FR1.csv",
]

#: Le nom du criteria, tel que l'optimizer le nomme, et le nom du fichier
#: produit. L'ordre est celui des fences : `wincap` d'abord, attrape-tout à la
#: fin — voir `game_optimization.py`.
CRITERIA_FILES = [
    ("WINCAP", f"{PREFIX}-wincap"),
    ("FREEGAME_MEGA", f"{PREFIX}-freegame-mega"),
    ("FREEGAME_HIGH", f"{PREFIX}-freegame-high"),
    ("FREEGAME_MEDIUM_LONG", f"{PREFIX}-freegame-medium-long"),
    ("FREEGAME_MEDIUM", f"{PREFIX}-freegame-medium"),
    ("FREEGAME_LOW", f"{PREFIX}-freegame-low"),
    ("ZERO", f"{PREFIX}-zero"),
    ("BASEGAME", f"{PREFIX}-basegame"),
]


def file_hash(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_books(path):
    decompressor = zstandard.ZstdDecompressor()
    with open(path, "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    yield json.loads(line)
        if buffer.strip():
            yield json.loads(buffer)


def classify(book, bucket_of, wincap_hundredths):
    """Fence à laquelle ce book appartient.

    MÊME ordre de décision que l'optimizer : le plafond d'abord (fence à payout
    exact, traitée en premier), puis les buckets Bonus, puis le zéro, puis
    l'attrape-tout. Un book ne peut donc pas tomber dans deux fences.
    """
    if book["payoutMultiplier"] >= wincap_hundredths:
        return "WINCAP"
    key = bucket_of.get(book["id"])
    if key is not None:
        bucket, retrigger = key
        if bucket == "medium":
            return "FREEGAME_MEDIUM_LONG" if retrigger == "yes" else "FREEGAME_MEDIUM"
        return f"FREEGAME_{bucket.upper()}"
    if book["payoutMultiplier"] == 0:
        return "ZERO"
    return "BASEGAME"


def main():
    config = GameConfig()
    wincap_hundredths = int(round(config.wincap * 100))

    lut_path = os.path.join(config.publish_path, "lookUpTable_base_0.csv")
    books_path = os.path.join(config.publish_path, "books_base.jsonl.zst")
    force_path = os.path.join(config.library_path, "forces", "force_record_base.json")
    for path in (lut_path, books_path, force_path):
        if not os.path.exists(path):
            raise SystemExit(
                f"artefact V4 absent : {path}\n"
                "Ces fichiers ne sont pas versionnés. Régénère-les avec :\n"
                "  python games/0_0_plant_vs_wild/run.py --base 100000 --bonus 5000 --optimize"
            )

    # Le bucket se relit sur le force record : MÊME source que celle que
    # l'optimizer a interrogée, pas un recalcul parallèle qui pourrait diverger.
    bucket_of = {}
    with open(force_path, encoding="utf-8") as handle:
        for entry in json.load(handle):
            keys = {k["name"]: k["value"] for k in entry["search"]}
            if "bucket" in keys:
                for book_id in entry["bookIds"]:
                    bucket_of[book_id] = (keys["bucket"], keys.get("retrigger"))

    shortest = {}
    total = 0
    for book in read_books(books_path):
        total += 1
        criteria = classify(book, bucket_of, wincap_hundredths)
        # Hors `ZERO`, on ne retient qu'un book qui PAIE. Le bucket faible
        # commence a 0x — un Bonus peut se declencher sans rien rapporter — et un
        # tel book serait indiscernable de `ZERO` en playback, donc inutile pour
        # valider l'affichage du gain. C'est un critere de CHOIX, pas une
        # retouche : le book retenu reste extrait tel quel.
        if criteria != "ZERO" and book["payoutMultiplier"] == 0:
            continue
        current = shortest.get(criteria)
        if current is None or len(book["events"]) < len(current["events"]):
            shortest[criteria] = book

    missing = [name for name, _ in CRITERIA_FILES if name not in shortest]
    if missing:
        raise SystemExit(f"aucun book pour : {missing}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    selected = []
    for criteria, filename in CRITERIA_FILES:
        book = shortest[criteria]
        with open(os.path.join(OUTPUT_DIR, filename + ".json"), "w", encoding="utf-8") as handle:
            json.dump(book, handle, indent=1)
            handle.write("\n")
        selected.append(
            {
                "name": filename,
                "criteria": criteria,
                "simId": book["id"],
                "events": len(book["events"]),
                "payoutMultiplier": book["payoutMultiplier"],
            }
        )
        print(
            f"{criteria:22} sim {book['id']:6}  {len(book['events']):4} events  "
            f"payout {book['payoutMultiplier'] / 100:.2f}x  -> {filename}.json"
        )

    freeze = {
        "version": f"BALANCING_{VERSION}",
        "status": "FROZEN_FOR_INTEGRATION",
        "mode": "base",
        "population": total,
        "sources": {name: file_hash(os.path.join(HERE, name)) for name in SOURCE_FILES},
        "artefacts": {
            "lookUpTable_base_0.csv": file_hash(lut_path),
            "books_base.jsonl.zst": file_hash(books_path),
            "force_record_base.json": file_hash(force_path),
        },
        "books": selected,
    }
    with open(FREEZE_FILE, "w", encoding="utf-8") as handle:
        json.dump(freeze, handle, indent=1)
        handle.write("\n")

    # Fusion dans l'index : `make_books.py` et ce script écrivent tous deux dans
    # `canonical_books/`, chacun ne touchant qu'à ses propres entrées.
    index_path = os.path.join(OUTPUT_DIR, "index.json")
    index = {"gameId": config.game_id, "books": []}
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as handle:
            index = json.load(handle)
    # Aucune version n'en cotoie une autre : les entrees d'une version
    # precedente disparaissent de l'index en meme temps que ses fichiers.
    kept = [b for b in index.get("books", []) if not b["name"].split("-")[0].startswith("v")]
    index["books"] = kept + [
        {"name": b["name"], "events": b["events"], "payoutMultiplier": b["payoutMultiplier"]}
        for b in selected
    ]
    with open(index_path, "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=1)
        handle.write("\n")

    print(f"\n{len(selected)} books {VERSION} extraits de {total} books")
    print(f"gel écrit : {os.path.relpath(FREEZE_FILE, HERE)}")


if __name__ == "__main__":
    main()
