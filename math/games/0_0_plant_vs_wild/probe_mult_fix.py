"""Impact du correctif « un seul cran par résolution » — OUTIL DE DÉVELOPPEMENT.

Comparaison APPARIÉE : les mêmes graines sont jouées deux fois, une fois avec la
règle corrigée, une fois avec l'ancienne. Les plateaux tirés sont donc
identiques et seule l'évolution des multiplicateurs diffère — l'écart mesuré est
l'effet du correctif, pas du bruit Monte-Carlo.

Rien n'est écrit sur disque : ni books, ni lookup table. La population
BALANCING_V4 déjà générée reste intacte.

    python games/0_0_plant_vs_wild/probe_mult_fix.py 3000
"""

import os
import statistics
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig, MAX_POSITION_MULT  # noqa: E402
from game_events import update_grid_event  # noqa: E402
from gamestate import GameState  # noqa: E402


def ancienne_regle(self):
    """La boucle telle qu'elle était : un doublement PAR CONNEXION."""
    if self.win_data["totalWin"] <= 0:
        return
    for win in self.win_data["wins"]:
        for pos in win["positions"]:
            current = self.position_multipliers[pos["reel"]][pos["row"]]
            doubled = 2 if current == 0 else current * 2
            self.position_multipliers[pos["reel"]][pos["row"]] = min(doubled, MAX_POSITION_MULT)
    update_grid_event(self)


def jouer(criteria, rounds, forcer_bonus, ancienne=False):
    config = GameConfig()
    state = GameState(config)
    betmode = [b for b in config.bet_modes if b.get_name() == "base"][0]
    state.betmode = "base"
    state.criteria = criteria
    conditions = dict(betmode.get_distribution_conditions(criteria))
    conditions["force_freegame"] = forcer_bonus
    state.get_current_distribution_conditions = lambda: conditions
    state.get_current_betmode_distributions = lambda: type(
        "D", (), {"get_win_criteria": staticmethod(lambda: None)}
    )()
    if ancienne:
        state.update_grid_mults = ancienne_regle.__get__(state)

    payouts = []
    for sim in range(rounds):
        state.sim = sim
        state.run_spin(sim, sim)
        payouts.append(min(state.final_win, config.wincap))
    return payouts


def comparer(titre, criteria, rounds, forcer_bonus):
    avant = jouer(criteria, rounds, forcer_bonus, ancienne=True)
    apres = jouer(criteria, rounds, forcer_bonus, ancienne=False)

    moy_avant, moy_apres = statistics.mean(avant), statistics.mean(apres)
    changes = sum(1 for a, b in zip(avant, apres) if a != b)
    plafond_avant = sum(1 for p in avant if p >= 10000)
    plafond_apres = sum(1 for p in apres if p >= 10000)

    print(f"\n{titre}  ({rounds} rounds, mêmes graines)")
    print(f"   gain moyen   avant {moy_avant:10.2f}x   après {moy_apres:10.2f}x   "
          f"ratio {moy_apres / moy_avant if moy_avant else 0:.3f}")
    print(f"   médiane      avant {statistics.median(avant):10.2f}x   "
          f"après {statistics.median(apres):10.2f}x")
    print(f"   maximum      avant {max(avant):10.2f}x   après {max(apres):10.2f}x")
    print(f"   rounds au plafond  avant {plafond_avant}   après {plafond_apres}")
    print(f"   rounds dont le gain change : {changes} ({changes / rounds * 100:.1f} %)")


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    comparer("BASE GAME", "basegame", rounds, forcer_bonus=False)
    comparer("BONUS forcé", "freegame", rounds, forcer_bonus=True)


if __name__ == "__main__":
    main()
