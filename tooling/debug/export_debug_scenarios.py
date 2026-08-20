#!/usr/bin/env python3
"""Exporte un petit jeu de books de développement pour le Debug Panel.

LECTURE SEULE sur les sorties du Math SDK. N'écrit jamais dans math/.

Entrées   : math/games/<id>/library/forces/force_record_<mode>.json  (critère -> bookIds)
            math/games/<id>/library/publish_files/books_<mode>.jsonl.zst
Sortie    : un fichier TypeScript contenant quelques books par scénario.

Usage :
    python tooling/debug/export_debug_scenarios.py \
        --math-game math/games/0_0_lines \
        --config apps/lines/src/dev/debugScenarios.config.json \
        --out apps/lines/src/dev/debugScenarios.generated.ts

Déterministe : à configuration et simulations identiques, la sortie est identique
(les books retenus sont les premiers par ordre d'ID croissant).
"""

import argparse
import io
import json
import sys
from pathlib import Path

import zstandard


def load_force_record(game_dir: Path, mode: str) -> list:
    """Charge le force record d'un mode : liste de {search, timesTriggered, bookIds}."""
    path = game_dir / "library" / "forces" / f"force_record_{mode}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Force record absent : {path}\n"
            f"Lancer d'abord la simulation : python games/{game_dir.name}/run.py"
        )
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def find_book_ids_by_force(force_record: list, search: dict) -> list:
    """Retourne les bookIds des entrées dont le `search` contient tous les critères."""
    wanted = {str(key): str(value) for key, value in search.items()}
    matches = []
    for entry in force_record:
        criteria = {item["name"]: str(item["value"]) for item in entry.get("search", [])}
        if all(criteria.get(key) == value for key, value in wanted.items()):
            matches.extend(entry.get("bookIds", []))
    return sorted(set(matches))


def iter_books(game_dir: Path, mode: str):
    """Itère les books d'un mode depuis le .jsonl.zst, sans tout charger en mémoire."""
    path = game_dir / "library" / "publish_files" / f"books_{mode}.jsonl.zst"
    if not path.exists():
        raise FileNotFoundError(f"Books absents : {path}")
    decompressor = zstandard.ZstdDecompressor()
    with open(path, "rb") as raw, decompressor.stream_reader(raw) as stream:
        for line in io.TextIOWrapper(stream, encoding="utf-8"):
            line = line.strip()
            if line:
                yield json.loads(line)


def matches_payout(book: dict, select: dict) -> bool:
    """Sélection par magnitude de gain — lit un champ déjà calculé par le Math."""
    payout = book.get("payoutMultiplier", 0)
    if "min" in select and payout < select["min"]:
        return False
    if "max" in select and payout > select["max"]:
        return False
    if "hasEvent" in select:
        types = {event.get("type") for event in book.get("events", [])}
        if select["hasEvent"] not in types:
            return False
    if "withoutEvent" in select:
        types = {event.get("type") for event in book.get("events", [])}
        if select["withoutEvent"] in types:
            return False
    return True


def collect_for_mode(game_dir: Path, mode: str, scenarios: list, limit: int) -> dict:
    """Un seul passage sur les books du mode, pour tous ses scénarios."""
    force_record = None
    wanted_ids = {}

    for scenario in scenarios:
        select = scenario["select"]
        if select["type"] == "force":
            if force_record is None:
                force_record = load_force_record(game_dir, mode)
            ids = find_book_ids_by_force(force_record, select["search"])
            if not ids:
                raise ValueError(
                    f"Scénario '{scenario['id']}' : aucun book pour {select['search']}"
                )
            wanted_ids[scenario["id"]] = set(ids[: limit * 4])

    collected = {scenario["id"]: [] for scenario in scenarios}

    for book in iter_books(game_dir, mode):
        for scenario in scenarios:
            bucket = collected[scenario["id"]]
            if len(bucket) >= limit:
                continue
            select = scenario["select"]
            if select["type"] == "force":
                if book["id"] in wanted_ids[scenario["id"]]:
                    bucket.append(book)
            elif matches_payout(book, select):
                bucket.append(book)
        if all(len(books) >= limit for books in collected.values()):
            break

    return collected


def render_typescript(scenarios: list, books_by_scenario: dict, sources: dict) -> str:
    """Génère le module TypeScript. Books sérialisés en JSON compact."""
    entries = []
    for scenario in scenarios:
        books = books_by_scenario[scenario["id"]]
        payload = json.dumps(books, separators=(",", ":"), ensure_ascii=False)
        entries.append(
            "\t{\n"
            f"\t\tid: {json.dumps(scenario['id'])},\n"
            f"\t\tlabel: {json.dumps(scenario['label'], ensure_ascii=False)},\n"
            f"\t\tmode: {json.dumps(scenario['mode'])},\n"
            f"\t\tbooks: {payload} as unknown as DebugBook[],\n"
            "\t},"
        )

    header = "\n".join(f"//   {mode}: {path}" for mode, path in sorted(sources.items()))

    return f"""// GÉNÉRÉ AUTOMATIQUEMENT — NE PAS ÉDITER À LA MAIN.
//
// Produit par tooling/debug/export_debug_scenarios.py depuis les sorties du Math SDK :
{header}
//
// Régénérer : voir tooling/debug/README.md
// Ces données sont du matériel de développement : elles ne sont jamais chargées
// dans un build de production (voir docs/DEBUG_PANEL.md).

export type DebugBook = {{
\tid: number;
\tpayoutMultiplier: number;
\tevents: unknown[];
}};

export type DebugScenario = {{
\tid: string;
\tlabel: string;
\tmode: string;
\tbooks: DebugBook[];
}};

export const debugScenarios: DebugScenario[] = [
{chr(10).join(entries)}
];
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--math-game", required=True, help="ex: math/games/0_0_lines")
    parser.add_argument("--config", required=True, help="config de scénarios du jeu")
    parser.add_argument("--out", required=True, help="fichier TypeScript à écrire")
    args = parser.parse_args()

    game_dir = Path(args.math_game).resolve()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    scenarios = config["scenarios"]
    limit = int(config.get("booksPerScenario", 2))

    modes = sorted({scenario["mode"] for scenario in scenarios})
    books_by_scenario = {}
    sources = {}

    for mode in modes:
        mode_scenarios = [s for s in scenarios if s["mode"] == mode]
        print(f"mode '{mode}' : {len(mode_scenarios)} scénario(s)…")
        books_by_scenario.update(collect_for_mode(game_dir, mode, mode_scenarios, limit))
        sources[mode] = f"{game_dir.name}/library/publish_files/books_{mode}.jsonl.zst"

    for scenario in scenarios:
        books = books_by_scenario[scenario["id"]]
        if not books:
            raise ValueError(f"Scénario '{scenario['id']}' : aucun book trouvé.")
        ids = ", ".join(str(book["id"]) for book in books)
        mults = ", ".join(str(book["payoutMultiplier"]) for book in books)
        print(f"  {scenario['id']:<24} books [{ids}]  payout [{mults}]")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_typescript(scenarios, books_by_scenario, sources), encoding="utf-8"
    )
    size_kb = out_path.stat().st_size / 1024
    print(f"\nÉcrit : {out_path}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
