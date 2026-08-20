# Gogold Definition of Done

Deux personnes différentes doivent pouvoir regarder la même tâche et arriver à la
même conclusion : **DONE** ou **NOT DONE**.

Ne suffisent jamais à eux seuls :

```text
« ça marche chez moi »   « l'image est exportée »
« le build passe »       « j'ai vu l'animation une fois »
```

---

## How to use this document

1. Choisir **une** des quatre DoD selon le contenu réel de la PR.
2. Ne parcourir que les critères applicables.
3. Marquer `N/A` ce qui ne concerne pas la tâche, avec une justification courte
   si ce n'est pas évident.
4. Un relecteur confirme.

Une tâche normale utilise quelques critères. La grosse matrice ne sert qu'à une
release candidate.

### Étiquettes

| | Signification |
| --- | --- |
| **[STAKE]** | Contrat de plateforme, vérifiable dans le SDK intégré ou la doc officielle |
| **[GOGOLD]** | Règle interne de qualité — ne jamais la présenter comme une exigence Stake |
| **[CONDITIONAL]** | Ne s'applique que si la tâche est réellement concernée |

### Sources

Les items **[STAKE]** de ce document sont vérifiés dans le code réellement
intégré (`packages/state-shared`, `packages/rgs-requests`,
`packages/components-shared`) et dans le README du Web SDK.

> ⚠️ La page officielle *Approval Guidelines* de `stake-engine.com/docs` n'a pas
> pu être consultée (application JavaScript, contenu non servi). Tout ce qui
> concerne la **soumission** — politique d'assets finaux, exigences mobiles
> formelles, petite vue — est donc marqué **[GOGOLD]** et devra être reconfirmé
> contre la documentation officielle avant la première soumission. Voir
> *What "Done" does NOT mean*.

---

## 1. Code Task DoD

Pour une modification de code sans rendu de jeu nouveau : refactor, outillage,
correction, configuration.

```text
[ ] le périmètre demandé est implémenté
[ ] aucun changement hors périmètre                              [GOGOLD]
[ ] Stake First respecté : aucune primitive Stake dupliquée      [GOGOLD]
[ ] types cohérents ; aucun `any` ni cast ajouté sans commentaire [GOGOLD]
[ ] le build pertinent passe
[ ] les tests pertinents passent
[ ] les checks CI obligatoires passeraient (voir docs/CI.md)
[ ] aucune nouvelle erreur console causée par ce changement
[ ] `git diff` relu ligne à ligne                                [GOGOLD]
```

**[CONDITIONAL]**

```text
[ ] code DEV absent du build de production        si la tâche touche du code DEV
[ ] documentation mise à jour                     si une règle permanente change
[ ] story Storybook                               si le changement a un rendu
                                                  visuel qu'une story clarifie
```

**Si la tâche touche `packages/`** — trois critères de plus :

```text
[ ] besoin de partage réellement démontré (pas « ça pourrait resservir ») [GOGOLD]
[ ] responsabilité du package claire, et ce qu'il ne fait pas est écrit   [GOGOLD]
[ ] impact vérifié sur les apps qui l'utilisent
```

**Si la tâche touche du code upstream Stake** : voir
`.claude/rules/stake-upstream.md` — divergence justifiée, diff minimal, documentée.

### Typecheck et lint

Ne **pas** exiger « 0 erreur `svelte-check` » ni « 0 erreur lint » : la baseline
Stake en contient déjà, documentées dans `docs/CI.md`. Le critère est :

```text
[ ] aucune nouvelle erreur directement introduite, lorsque vérifiable
```

---

## 2. Asset DoD

Un asset traverse **trois états distincts**. Ne pas les confondre.

```text
ART COMPLETE            l'intention artistique est validée
        ↓
READY FOR INTEGRATION   l'export est techniquement conforme
        ↓
INTEGRATED              l'asset est dans le jeu et vérifié à l'écran
```

### ART COMPLETE

```text
[ ] style cohérent avec la direction artistique du jeu           [GOGOLD]
[ ] lisible en petit (mobile) et en grand (desktop)              [GOGOLD]
[ ] master conservé, séparé de la livraison                      [GOGOLD]
```

### READY FOR INTEGRATION

```text
[ ] nommage conforme à docs/ASSETS.md                            [GOGOLD]
[ ] format d'export runtime correct (docs/ASSET_PIPELINE.md)     [GOGOLD]
[ ] dimensions adaptées à la cellule/au rôle, sans surdimensionnement
[ ] alpha propre, aucune frange sombre
[ ] marge transparente raisonnable, aucun recadrage aberrant
[ ] aucun master (.psd, .aep, .blend, .wav…) dans static/assets/
[ ] `node tooling/assets/check-assets.mjs <dir>` PASS
[ ] poids relevé et jugé acceptable pour ce qu'il apporte
```

**[CONDITIONAL]**

```text
[ ] atlas/spritesheet valide, lisible par PixiJS       si atlas
[ ] frames au même canvas, même origine, zero-paddées  si animation
[ ] aucun clipping en bord de cellule                  si symbole/cellule
[ ] aucun halo / bleeding d'atlas                      si atlas
```

### INTEGRATED

```text
[ ] déclaré dans assets.ts (ou l'index correspondant)
[ ] rendu vérifié à l'écran, dans le jeu ou dans Storybook
[ ] aucune texture manquante, aucun carré blanc/magenta
[ ] aucun saut entre deux états d'un même élément
```

**[CONDITIONAL]** — pour un symbole :

```text
[ ] inspectable dans Storybook : rendu `static` + tous les états implémentés
```

> Règle de `docs/STORYBOOK.md` : un symbole n'est pas visuellement intégré tant
> qu'il n'est pas inspectable dans Storybook. Il ne doit jamais falloir lancer
> cinquante spins pour vérifier son rendu.

> Un PNG qui existe n'est pas un asset terminé. Un asset qui n'a jamais été
> regardé à l'écran n'est pas `INTEGRATED`.

---

## 3. Gameplay Feature DoD

Pour une mécanique ou un comportement de jeu. Plus exigeant qu'une tâche de code.

### Définition

```text
[ ] le comportement attendu est écrit avant l'implémentation     [GOGOLD]
[ ] les couches concernées sont identifiées : Math / frontend / les deux
```

### Math — **[CONDITIONAL]**, seulement si la feature a une logique Math

```text
[ ] configuration/source versionnée, artefacts régénérés et non édités à la main
[ ] tests Math pertinents PASS
[ ] volume de simulation suffisant pour l'objectif de CETTE feature
[ ] indicateurs contrôlés selon le besoin : RTP, distribution, fréquence
[ ] max win vérifié                                    si la feature peut l'atteindre
[ ] contrat d'events compatible avec le frontend
```

> Si la feature n'a aucune logique Math, écrire `N/A` — ne pas inventer une
> partie Math pour remplir la case.

### Frontend

```text
[ ] aucun calcul du résultat côté client                          [STAKE]
[ ] chaîne respectée : book → bookEvent → handler → emitterEvent → composant
[ ] tous les bookEvents produits par la feature ont un handler
[ ] chaque handler se termine quand son étape visuelle est terminée
```

### Vérification

```text
[ ] scénarios normaux joués
[ ] scénarios rares atteignables de façon reproductible          [GOGOLD]
[ ] entrée dans la feature testée
[ ] sortie de la feature testée
[ ] build PASS, tests pertinents PASS
```

**[CONDITIONAL]**

```text
[ ] story Storybook isolée     REQUISE pour tout bookEvent à effet visuel
[ ] scénario Debug Panel       si le cas est rare ou la séquence longue
[ ] replay du même round       si la reproductibilité est nécessaire au diagnostic
```

> `docs/STORYBOOK.md` fixe la règle : **un bookEvent à effet visuel n'est pas
> terminé tant qu'il n'a pas handler + rendu intégré + story isolée
> fonctionnelle.** La DoD ne l'assouplit pas. Un bookEvent sans effet visuel
> propre (event d'état, snapshot de reprise) est `N/A`.

Un scénario Debug pointe toujours vers un **vrai Book** — aucun résultat fabriqué
côté frontend (`.claude/rules/debug.md`).

### Cas limites — `APPLICABLE` / `N/A`

Ne pas tous les cocher systématiquement : ne retenir que ceux que la feature peut
réellement rencontrer.

```text
premier event · dernier event · valeur minimale · valeur maximale
max win · enchaînement de plusieurs events
transition base → bonus · transition bonus → base
round interrompu puis repris
resize / changement d'orientation pendant une animation longue
```

### Viewports — voir *Device / viewport matrix*

```text
[ ] DEV CHECK effectué sur les viewports applicables
```

---

## 4. Game / Release Candidate DoD

Pour une **slot entière** candidate à la sortie. C'est la seule DoD qui utilise
les matrices complètes.

### Frontend

```text
[ ] build de production PASS                                      [STAKE]
[ ] le build est un site statique autonome                        [STAKE]
[ ] aucune ressource runtime externe (police, image, audio, CDN)  [STAKE]
[ ] aucune ressource manquante : aucune 404, aucune texture absente
[ ] UI fonctionnelle et lisible sur tous les devices de la matrice release
[ ] solde, mise et gain affichés de façon cohérente entre eux
```

> **[STAKE]** « You can use anything as long as it compiles to a static website »
> — README du Web SDK. Notre `config-svelte` utilise `adapter-static`.

### RGS

Vérifié dans `packages/components-shared/src/components/Authenticate.svelte` et
`packages/rgs-requests`.

```text
[ ] les niveaux de mise viennent de /wallet/authenticate          [STAKE]
    minBet · maxBet · stepBet · defaultBetLevel · betLevels
[ ] aucune valeur de mise hardcodée                               [STAKE]
[ ] les flags jurisdiction reçus sont respectés                   [STAKE]
[ ] un round actif retourné par authenticate est repris, pas redémarré [STAKE]
[ ] end-round appelé : sans lui, pas de payout                    [STAKE]
```

Ne pas recopier la liste des flags jurisdiction dans une checklist : elle
évoluera. Le critère est « respecter la configuration reçue ». Les flags
actuellement présents dans notre baseline sont dans
`packages/state-shared/src/stateConfig.svelte.ts`.

### Bet Replay — **[STAKE]**

Contrat observé dans notre baseline : paramètres d'URL `replay`, `game`,
`version`, `mode`, `event`, `amount`, `rgs_url`, et endpoint
`GET /bet/replay/{game}/{version}/{mode}/{event}`.

```text
[ ] Replay testé sur des scénarios représentatifs :
      base · feature/bonus · résultat rare ou important   (ceux qui existent)
```

> Le Debug Panel local **ne teste pas** le Bet Replay : il rejoue un book local
> sans RGS. Le replay Stake interroge le RGS et exige une session réelle
> (`docs/DEBUG_PANEL.md`).

### Math

```text
[ ] version Math précisément identifiée (commit / configuration)
[ ] publish files générés par le workflow, jamais édités à la main
[ ] tests Math PASS
[ ] indicateurs validés selon les objectifs du jeu
[ ] le frontend gère tous les bookEvents que le math peut produire
```

Ce dernier point mérite attention : un event émis par le Math et absent du
`bookEventHandlerMap` passe inaperçu jusqu'à ce qu'il sorte en production.

### Gameplay

```text
[ ] base game complet
[ ] toutes les features du jeu
[ ] bonus / free spins                                     si le jeu en a
[ ] scénarios rares importants
[ ] max win                                                si atteignable
```

### QA — voir les deux matrices plus bas

```text
[ ] matrice devices release parcourue, statuts renseignés
[ ] matrice de scénarios parcourue : ALWAYS complet
[ ] audio : ON/OFF, mute, changement d'onglet, retour
[ ] interruption et reprise
[ ] resize et changement d'orientation
```

### Production

```text
[ ] Debug Panel absent du build         `node tooling/ci/check-production-build.mjs`
[ ] fixtures DEV absentes du build
[ ] aucun secret, token, sessionID ni URL privée
[ ] checks CI obligatoires PASS
[ ] version du jeu identifiable
```

### Assets finaux — **[GOGOLD]**

```text
[ ] aucun asset provenant d'un sample Stake utilisé comme contenu final
```

Les assets de `apps/lines` sont un sample technique, pas un standard de qualité
publiable. À reconfirmer contre les *Approval Guidelines* avant soumission.

---

## Device / viewport matrix

Nous sommes trois. Pas de matrice de 25 téléphones.

### DEV CHECK — pendant le développement

Pour toute modification à rendu visuel :

```text
[ ] desktop landscape        navigateur de développement
[ ] mobile portrait          viewport simulé accepté à ce stade
[ ] mobile landscape         si le jeu le supporte
[ ] petite vue / popout      largeur réduite
```

> Un viewport Chrome simulé ne remplace pas un appareil réel : il ne reproduit ni
> les performances GPU, ni le comportement audio, ni les gestes système. Il
> suffit pour du développement, pas pour valider une release.

### RELEASE CHECK — pour une slot candidate

| Cible | Statut à renseigner |
| --- | --- |
| Desktop Chrome | requis |
| Desktop Edge (ou autre Chromium pertinent) | requis |
| Desktop Safari macOS | `AVAILABLE` / `NOT AVAILABLE` / `EXTERNAL TEST REQUIRED` |
| iPhone Safari — **appareil réel** | `AVAILABLE` / `NOT AVAILABLE` / `EXTERNAL TEST REQUIRED` |
| Android Chrome — **appareil réel** | `AVAILABLE` / `NOT AVAILABLE` / `EXTERNAL TEST REQUIRED` |
| Petite vue / popout | requis |
| Portrait et landscape | selon le support du jeu |

Au moins **un iOS réel et un Android réel** sont la cible d'une release QA. Si
l'équipe n'en dispose pas, écrire `EXTERNAL TEST REQUIRED` — pas `N/A`, et ne pas
déclarer la release QA complète.

Cette matrice est une **[GOGOLD]** : c'est ce que Gogold décide de vérifier, pas
une liste de certification Stake.

---

## Required scenario matrix

Trois niveaux. Une slot complète parcourt les trois ; une feature ne parcourt que
ce qui la concerne.

### ALWAYS — toute slot complète

```text
round de base normal
round gagnant
round sans gain
mise minimum
mise maximum
changement de mise
audio ON / OFF
resize
reprise d'un round actif                    lorsque testable
Bet Replay
```

> Plusieurs de ces points exigent une vraie session Stake (reprise de round,
> Bet Replay, niveaux de mise réels). Ils appartiennent à la phase QA avec
> environnement Stake, pas au développement local.

### IF SUPPORTED — seulement si le jeu **et** la jurisdiction l'autorisent

```text
turbo · autoplay · fullscreen · buy feature · slam stop / skip
```

> Ne jamais écrire « turbo obligatoire » : les flags de jurisdiction peuvent le
> désactiver. Le critère est « se comporte correctement, activé comme désactivé ».

### IF RELEVANT — selon le jeu

```text
entrée bonus · sortie bonus · free spins · cascade/tumble
multiplicateur · état sticky · feature persistante
max win · anticipation · longue chaîne d'animations
```

Le Debug Panel doit permettre d'atteindre rapidement ces cas quand une fixture
pertinente existe (`docs/DEBUG_PANEL.md`).

### Erreurs réseau

```text
Code Task     seulement si le changement touche networking / session / erreurs
Release       interruption de connexion, refresh, reprise de round actif,
              lorsque l'environnement de test le permet
Autres codes  IF RELEVANT
```

Ne pas exiger le test de chaque code d'erreur RGS sur chaque tâche.

---

## Automated vs manual

Ne pas refaire à la main ce que la CI vérifie déjà.

### Automatisé par la CI (`docs/CI.md`)

```text
build de production                    validation des assets
tests Math                             sécurité production (code DEV absent)
mesure des tailles                     lint et typecheck (informatifs)
```

### Manuel — irremplaçable

```text
rendu visuel            appareil mobile réel      audio
orientation et resize   Bet Replay                comportement d'une feature
UX                      cohérence artistique
```

> Une case cochée dans une PR ne prouve rien par elle-même. Elle engage la
> personne qui la coche. Ce qui est automatisable doit être automatisé ; le reste
> repose sur une vérification honnête et un relecteur.

---

## Bug severity

| Niveau | Exemples |
| --- | --- |
| **BLOCKER** | impossible de jouer · round impossible à terminer · résultat affiché incohérent avec le book · erreur RGS critique · crash · asset essentiel absent |
| **MAJOR** | feature importante incorrecte · UI principale inutilisable sur un device supporté · animation ou transition cassée nuisant à la compréhension · audio majeur cassé |
| **MINOR** | petit défaut visuel · timing légèrement imparfait · cosmétique sans impact gameplay |

### Règle de sortie

```text
Tâche standard        aucun BLOCKER ni MAJOR causé par cette tâche
Release candidate     0 BLOCKER · 0 MAJOR
MINOR                 corrigés, ou explicitement acceptés et tracés
```

Aucun outil de ticketing n'est imposé : un MINOR accepté doit simplement être
écrit quelque part de retrouvable (issue, note de PR).

---

## Review rule

Pour une modification importante :

```text
AUTEUR ≠ VALIDATEUR FINAL
```

Au moins une autre personne doit pouvoir lire la PR, reproduire le test
essentiel, et confirmer la DoD applicable. Si le relecteur ne peut pas reproduire
le scénario important, la PR n'est pas prête — c'est souvent le signe qu'un
scénario Debug ou une story manque.

Pour une correction triviale (typo, commentaire, renommage local), une relecture
simple suffit. Ne pas créer de bureaucratie.

---

## What "Done" does NOT mean

**DONE ≠ prêt à soumettre à Stake.**

```text
Definition of Done          utilisée pendant toute la production
Stake Submission Checklist  étape dédiée, plus tard, par jeu
```

Certaines exigences Stake sont intégrées tôt dans cette DoD — statique, niveaux
de mise, jurisdiction, reprise de round, Bet Replay — précisément pour ne pas les
découvrir à la fin. Cela ne remplace pas la pré-soumission officielle.

Avant la première soumission, reconfirmer contre les *Approval Guidelines*
officielles tout ce qui est marqué **[GOGOLD]** dans la DoD release, en
particulier : exigences mobiles formelles, petite vue / popout, et politique sur
les assets de sample.

Ce document ne crée aucun outil, aucun bot, aucun framework QA et aucun job CI.
Il ne remplace ni `docs/CI.md`, ni `docs/ASSET_PIPELINE.md`, ni
`docs/STORYBOOK.md`, ni `docs/DEBUG_PANEL.md` : il indique quand les appliquer.
