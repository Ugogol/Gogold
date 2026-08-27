"""Mise en forme lisible de la baseline.

Aucun calcul : tous les chiffres viennent de `baseline_report.json`. Séparé de
`analyse_baseline.py` pour que la mesure et sa présentation restent distinctes.
"""

WIN_BUCKET_LABELS = [
    "0x",
    ">0x-1x",
    "1x-2x",
    "2x-5x",
    "5x-10x",
    "10x-25x",
    "25x-50x",
    "50x-100x",
    "100x-500x",
    "500x+",
]


def pct(value):
    return f"{value * 100:.2f} %"


def render(report, probe):
    base = report["modes"]["base"]
    bonus = report["modes"]["bonus"]
    bg = base["basegame"]
    fg = bonus["freegame"]

    out = []
    add = out.append

    add("# PLANT VS WILD - baseline mesuree")
    add("")
    add("> Ce document **mesure** le jeu tel qu'il est. Il ne valide rien et ne fixe aucun")
    add("> objectif. La paytable est `TEST_ONLY` et les parametres de balancing ne sont pas")
    add("> decides : les chiffres ci-dessous decrivent un point de depart, pas une cible.")
    add("")
    add(
        f"Genere par `analyse_baseline.py` - {report['simulations']['base']['wagers']} wagers base, "
        f"{report['simulations']['bonus']['wagers']} wagers bonus."
    )
    add(f"Reproductible : {report['simulations']['base']['seeding']}")
    add("")

    add("## Base Game")
    add("")
    add("| | |")
    add("| --- | --- |")
    add(f"| OBSERVED_RTP | **{base['observed_rtp']:.2f}** ({base['observed_rtp'] * 100:.0f} %) |")
    add(
        f"| hit rate | {pct(1 - base['sdk']['prob_no_win'])} - 1 spin sur "
        f"{base['sdk']['hit_rate']:.2f} |"
    )
    add(f"| spins sans gain | {pct(base['sdk']['prob_no_win'])} |")
    add(f"| gain moyen | {base['sdk']['average_win']:.2f}x |")
    add(f"| gain median (P50) | {base['payout_percentiles_in_bet_multiples']['P50']}x |")
    add(
        f"| gain max observe | {base['max_observed_win_in_bet_multiples']}x (plafond, atteint "
        f"1 fois sur {base['sdk']['max_win_hit_rate']:.0f}) |"
    )
    add(f"| cascades / spin | moyenne {bg['cascades']['average']}, max {bg['cascades']['max']} |")
    add("")

    add("### Cascades (Base Game)")
    add("")
    add("| cascades | spins |")
    add("| --- | --- |")
    for key, label in (("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4+")):
        add(f"| {label} | {bg['cascades']['distribution'].get(key, 0)} |")
    add("")

    add("## Wild")
    add("")
    add(
        f"Present dans **{pct(bg['wild']['frequency'])}** des spins de base "
        f"({bg['wild']['at_reveal']} au reveal, {bg['wild']['from_refill']} arrives par un refill)."
    )
    add("")
    add("| connexions dans le spin | Base | Free Spins |")
    add("| --- | --- | --- |")
    for key, label in (("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4+")):
        add(
            f"| {label} | {bg['wild']['connections_per_spin'].get(key, 0)} | "
            f"{fg['wild']['connections_per_spin'].get(key, 0)} |"
        )
    add("")

    add("## Multipliers")
    add("")
    add("Nombre de fois qu'une case atteint chaque palier.")
    add("")
    add("| palier | Base Game | Free Spins (mode bonus) |")
    add("| --- | --- | --- |")
    for level in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096):
        add(
            f"| x{level} | {bg['multiplier_peaks'].get(str(level), 0)} | "
            f"{fg['multiplier_peaks'].get(str(level), 0)} |"
        )
    add("")
    add(
        f"Part du payout venant des multiplicateurs de case : "
        f"**{pct(base['rtp_contribution']['position_multipliers_share'])}** en mode base, "
        f"**{pct(bonus['rtp_contribution']['position_multipliers_share'])}** en mode bonus."
    )
    add("")

    add("## Bonus")
    add("")
    add("| | mode base | mode bonus |")
    add("| --- | --- | --- |")
    add(
        f"| declenchement | 1 wager sur {base['bonus']['one_in']} "
        f"({pct(base['bonus']['trigger_frequency'])}) | achete |"
    )
    add(f"| Free Spins moyens | {base['bonus']['average_total_fs']} | {bonus['bonus']['average_total_fs']} |")
    add(f"| gain moyen | {base['bonus']['average_win']}x | {bonus['bonus']['average_win']}x |")
    add(f"| gain median | {base['bonus']['median_win']}x | {bonus['bonus']['median_win']}x |")
    add(f"| gain max | {base['bonus']['max_win']}x | {bonus['bonus']['max_win']}x |")
    add(
        f"| retriggers / Bonus | {base['bonus']['retriggers']['average']} | "
        f"{bonus['bonus']['retriggers']['average']} |"
    )
    add("")
    add(
        f"Retriggers (mode bonus) : {bonus['bonus']['retriggers']['zero']} Bonus sans, "
        f"{bonus['bonus']['retriggers']['one']} avec 1, "
        f"{bonus['bonus']['retriggers']['two_or_more']} avec 2 ou plus."
    )
    add("")

    add("## Features")
    add("")
    if probe:
        add("Frequence observee en simulation normale : **0**. `DEAD_SPIN_FEATURE_WEIGHTS` vaut")
        add("`none` seul - aucune frequence n'est decidee, donc aucune feature ne part.")
        add("")
        add(
            f"Les valeurs ci-dessous viennent d'une **sonde** ({probe['wagers']} wagers) qui force"
        )
        add("une feature sur chaque dead spin eligible. Elles disent ce que rapporte une feature")
        add("*quand elle part*, pas a quelle frequence elle devrait partir.")
        add("")
        add(
            f"Dead spins eligibles : **{pct(probe['eligible_dead_spin_rate_per_free_spin'])}** "
            f"des Free Spins."
        )
        add("")
        add("| feature | activations | gain moyen apres | median | max | sans gain |")
        add("| --- | --- | --- | --- | --- | --- |")
        for name, label in (("rage", "Rage"), ("wildSnake", "Wild Snake"), ("wildSplit", "Wild Split")):
            entry = probe["features"][name]
            add(
                f"| {label} | {entry['activations']} | {entry['average_win_after_x']}x | "
                f"{entry['median_win_after_x']}x | {entry['max_win_after_x']}x | "
                f"{pct(entry['share_without_win'])} |"
            )
        snake = probe["snake"]
        add("")
        add(
            f"Wild Snake - trajet moyen {snake['average_path_length']} cases "
            f"(max {snake['max_path_length']}), Low {pct(snake['low_share'])} / "
            f"High {pct(snake['high_share'])}, dont H4 {pct(snake['h4_share'])}."
        )
        add("Ces proportions refletent les poids uniformes actuels, pas un choix de design.")
    else:
        add("Sonde non executee - lancer `probe_features.py`.")
    add("")

    add("## Distribution des gains")
    add("")
    add("| bucket | mode base | mode bonus |")
    add("| --- | --- | --- |")
    for label in WIN_BUCKET_LABELS:
        add(
            f"| {label} | {pct(base['win_distribution'][label]['share'])} | "
            f"{pct(bonus['win_distribution'][label]['share'])} |"
        )
    add("")

    add("## Indicateurs de volatilite")
    add("")
    add("Mesures du SDK (`utils.rgs_verification`), pas un score maison.")
    add("")
    add("| | mode base | mode bonus |")
    add("| --- | --- | --- |")
    add(f"| ecart-type | {base['sdk']['std_dev']} | {bonus['sdk']['std_dev']} |")
    add(f"| asymetrie | {base['sdk']['skew']} | {bonus['sdk']['skew']} |")
    add(
        f"| kurtosis excedentaire | {base['sdk']['excess_kurtosis']} | "
        f"{bonus['sdk']['excess_kurtosis']} |"
    )
    for key in ("P50", "P90", "P95", "P99", "P99.9"):
        add(
            f"| {key} | {base['payout_percentiles_in_bet_multiples'][key]}x | "
            f"{bonus['payout_percentiles_in_bet_multiples'][key]}x |"
        )
    add("")

    add("## Contribution au payout")
    add("")
    add("| mecanique | mode base | mode bonus |")
    add("| --- | --- | --- |")
    add(
        f"| Base Game | {pct(base['rtp_contribution']['basegame_share'])} | "
        f"{pct(bonus['rtp_contribution']['basegame_share'])} |"
    )
    add(
        f"| Free Spins | {pct(base['rtp_contribution']['freegame_share'])} | "
        f"{pct(bonus['rtp_contribution']['freegame_share'])} |"
    )
    add(
        f"| Multiplicateurs de case | {pct(base['rtp_contribution']['position_multipliers_share'])} | "
        f"{pct(bonus['rtp_contribution']['position_multipliers_share'])} |"
    )
    add("| Wild | NON_ISOLABLE | NON_ISOLABLE |")
    add("| Features | 0 (desactivees) | 0 (desactivees) |")
    add("")
    add("> La part du Wild n'est pas isolable : il cree des connexions qui n'existeraient pas")
    add("> sans lui et en agrandit d'autres. La separer demanderait de rejouer chaque spin")
    add("> sans Wild - ce serait un autre jeu, pas une mesure.")
    add("")

    return "\n".join(out) + "\n"
