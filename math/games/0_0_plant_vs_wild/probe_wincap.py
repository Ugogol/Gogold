"""Sonde de faisabilite du criteria `wincap` — OUTIL DE DEVELOPPEMENT.

Question unique : en forcant le Bonus sur les bandes WCAP, a quelle frequence
un round atteint-il le plafond ? C'est ce qui decide si le quota `wincap` est
generable, et c'est la mesure que l'etape 21 demande avant de choisir une
frequence de Max Win.

    python games/0_0_plant_vs_wild/probe_wincap.py 300 WCAP
"""

import os
import statistics
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    reelset = sys.argv[2] if len(sys.argv) > 2 else "WCAP"

    config = GameConfig()
    state = GameState(config)
    betmode = [b for b in config.bet_modes if b.get_name() == "base"][0]
    state.betmode = "base"
    state.criteria = "freegame"
    # On se place dans les conditions EXACTES du criteria vise, en ne changeant
    # que le reelset du Bonus : c'est la seule variable etudiee.
    conditions = dict(betmode.get_distribution_conditions("freegame"))
    conditions["reel_weights"] = {
        config.basegame_type: {"BR0": 1},
        config.freegame_type: {reelset: 1},
    }
    conditions["force_freegame"] = True
    state.get_current_distribution_conditions = lambda: conditions
    state.get_current_betmode_distributions = lambda: type(
        "D", (), {"get_win_criteria": staticmethod(lambda: None)}
    )()

    payouts = []
    start = time.time()
    for sim in range(rounds):
        state.sim = sim
        state.run_spin(sim, sim)
        payouts.append(state.final_win)

    elapsed = time.time() - start
    payouts.sort()
    capped = sum(1 for p in payouts if p >= config.wincap)
    buckets = Counter()
    for p in payouts:
        for name, low in ((">=10000x", 10000), (">=5000x", 5000), (">=2500x", 2500),
                          (">=1000x", 1000), (">=500x", 500), (">=100x", 100)):
            if p >= low:
                buckets[name] += 1
                break
        else:
            buckets["<100x"] += 1

    print(f"reelset Bonus        {reelset}")
    print(f"rounds forces        {rounds}   ({elapsed:.1f} s, {rounds/elapsed:.1f} rounds/s)")
    print(f"payout median        {statistics.median(payouts):.1f}x")
    print(f"payout moyen         {statistics.mean(payouts):.1f}x")
    print(f"payout max           {max(payouts):.1f}x")
    print(f"rounds au plafond    {capped}  ({capped/rounds*100:.2f} %)")
    for name in (">=10000x", ">=5000x", ">=2500x", ">=1000x", ">=500x", ">=100x", "<100x"):
        print(f"   {name:10} {buckets.get(name, 0):5d}")


if __name__ == "__main__":
    main()
