# Gogold Debug Panel

Atteindre un round précis en quelques secondes, au lieu d'attendre qu'il sorte au
hasard.

Dans le sample, le MAX WIN représente **0.11 % des rounds** : environ 900 spins
d'attente en moyenne. Avec le panel, deux clics.

---

## Purpose

```text
jeu complet en DEV
   ↓ choisir un scénario
   ↓ injecter un book Math réel
   ↓ observer tout le round
   ↓ REPLAY : exactement le même book
```

Le panel est une **télécommande de développement**. Il ne calcule rien.

---

## Storybook vs Debug Panel

Deux outils, deux usages. Ne pas les fusionner.

| [Storybook](STORYBOOK.md) | Debug Panel |
| --- | --- |
| un symbole, un composant | un round complet |
| un état visuel isolé | une séquence complète |
| un bookEvent isolé | un cas rare reproductible |
| un book local dans un canvas de story | le vrai jeu en DEV |
| — | diagnostic runtime (FPS, viewport) |
| — | replay exact du même book |

Storybook valide **une pièce**. Le Debug Panel valide **le round**.

---

## Stake foundation

Ce que Stake fournit déjà, et que nous réutilisons tel quel :

| Brique | Rôle |
| --- | --- |
| `utils-book` → `createPlayBookUtils` | `playBookEvent` / `playBookEvents`, séquencement des events |
| `apps/<game>/src/game/utils.ts` → `playBet` | point d'entrée que la machine XState appelle dans `onPlayGame` |
| `bookEventHandlerMap` | dispatch event → rendu |
| `utils-event-emitter` | emitterEvents vers les composants |
| force records du Math SDK | critère → bookIds |

### Ce que Stake ne fournit pas

| Question | Réponse |
| --- | --- |
| Debug Panel officiel ? | **non** — aucun dossier/composant debug dans la baseline |
| UI de sélection de force ? | **non** |
| Lecture d'un book local ? | **oui, partiellement** — les stories appellent `playBet` avec des fixtures locales |
| Mécanisme de replay ? | **oui, mais pas pour le dev** — `?replay=true` + `/bet/replay/...` interroge le **RGS** pour rejouer un round passé réel. Session obligatoire. |
| Format `force.json` ? | **oui** — produit par le Math SDK |
| Correspondance critère → book IDs ? | **oui** — `force_record_<mode>.json` |

Le replay Stake et le Debug Panel ne se recouvrent pas : l'un rejoue un round
**joué en production** depuis le RGS, l'autre rejoue un book **local** sans
session.

---

## Force files

Produits par la simulation, dans `math/games/<id>/library/forces/` :

```text
force.json                vocabulaire des critères disponibles par mode
force_record_base.json    critère -> bookIds  (657 entrées pour 0_0_lines)
force_record_bonus.json
```

Structure d'une entrée :

```json
{
  "search": [
    { "name": "gametype", "value": "basegame" },
    { "name": "kind",     "value": "3" },
    { "name": "symbol",   "value": "scatter" }
  ],
  "timesTriggered": 662,
  "bookIds": [2, 38, 51, ...]
}
```

C'est **le** mécanisme Stake de correspondance critère → résultats. Gogold ne
construit pas de second système de forces.

> Les force records couvrent les critères de **forme de gain** (`gametype`,
> `kind`, `symbol`, `mult`). Ils ne décrivent pas la **magnitude** d'un round
> (aucun gain, gros gain, max win). Pour ces cas, la sélection se fait sur le
> `payoutMultiplier` déjà calculé du book — c'est de la sélection, pas du calcul.

---

## Debug scenario lifecycle

```text
MATH
  math/games/<id>/run.py
        ↓
force/book outputs
  library/forces/force_record_<mode>.json
  library/publish_files/books_<mode>.jsonl.zst
        ↓  tooling/debug/export_debug_scenarios.py   (lecture seule)
selected DEV fixtures
  apps/<game>/src/dev/debugScenarios.generated.ts    (13 books, 100 KB)
        ↓
Debug Panel
        ↓  playBet(book)
normal book pipeline
  playBookEvents → bookEventHandlerMap → emitterEvent → composants
```

Le navigateur ne lit **jamais** `math/`. La frontière est le fichier généré.

Nombre de books gardés : **quelques-uns par scénario** (2 par défaut). Jamais la
bibliothèque Math complète.

---

## Opening the panel

```powershell
pnpm run dev --filter=lines
```

puis ouvrir **<http://localhost:3001/?debug=true>**

Le panel apparaît en bas à droite : bouton `▲ DEBUG`. Cliquer pour déplier.
Passer l'écran de chargement (`PRESS ANYWHERE TO CONTINUE`), puis jouer.

### Le mode `?debug=true`

C'est un **mode local explicite**, actif uniquement sur un serveur de dev.

| URL | Authenticate RGS | Debug Panel |
| --- | --- | --- |
| `/` (DEV) | tenté — comportement Stake d'origine | absent |
| `/?debug=true` (DEV) | **sauté** | présent |
| production | tenté | **absent du bundle** |

Sans ce mode, le jeu appelle `/wallet/authenticate` au démarrage ; sans session
la requête échoue et une modale **« TypeError: Failed to fetch »** recouvre le
jeu. Le mode debug supprime cette seule étape.

### Ce que le mode fait — et ne fait pas

```text
FAIT          ne rend pas <Authenticate>
              n'enregistre pas la progression du round (POST /bet/event)

NE FAIT PAS   aucun faux RGS, aucun serveur de mock
              aucun wallet reproduit, aucun solde simulé
              aucun état XState forcé
              aucune mécanique modifiée
```

Tout le reste repose sur les **valeurs par défaut de `state-shared`**
(`betAmount: 1`, `wageredBetAmount: 1`, `currency: 'USD'`, `betAmountOptions`
déjà peuplées) — exactement ce dont Storybook se contente via
`StoryGameTemplate`. Les gains s'affichent correctement parce que
`bookEventAmountToNormalisedAmount` s'appuie sur `wageredBetAmount`, pas sur le
solde.

### Deux points de garde, tous deux DEV-only

| Fichier | Rôle |
| --- | --- |
| `src/routes/+layout.svelte` | saute `<Authenticate>` et monte le panel |
| `src/game/bookEventHandlerMap.ts` | saute `recordBookEvent` (POST `/bet/event`) |

Le second est nécessaire : `recordBookEvent` est appelé dans le handler `reveal`
des rounds bonus. Son `try/catch` n'attrape pas le rejet de promesse, l'erreur
remontait donc en exception non gérée pendant la lecture.

Les deux gardes passent par `src/game/devDebugMode.ts`, dont `isLocalDebugMode()`
est replié à `false` en production.

> Aucun package Stake n'a été modifié pour obtenir ce mode.

---

## Selecting a scenario

1. **Scénario** — liste alimentée par `debugScenarios.generated.ts`, préfixée par
   son mode : `[base] Base — MAX WIN (5000x, 0.11% des rounds)`.
2. **Book** — quand le scénario en contient plusieurs, choisir lequel jouer
   (`#1638 — payout 500000`).

La liste s'adapte au jeu : aucune catégorie universelle n'est imposée. Une slot
sans bonus n'aura pas de scénario bonus.

## Play

`PLAY` appelle `playBet(book)` — la fonction que la machine XState appelle
elle-même dans `onPlayGame`. Le round se déroule normalement : reveal,
animations, gains, free spins.

## Replay

`REPLAY` rejoue **le même book**, pas un résultat équivalent. Le book est dérivé
du scénario et de l'index sélectionnés, qui ne changent pas entre deux clics —
la reproduction est garantie par construction.

C'est ce qui permet de reproduire un bug à volonté.

---

## Runtime information

```text
mode                base | bonus
scénario            id technique du scénario courant
book ID             identifiant Math du book joué
payoutMultiplier    valeur brute du book
bookEvents          nombre d'events de la séquence
viewport            largeur × hauteur + orientation
FPS                 moyenne glissante sur 500 ms (requestAnimationFrame)
état                prêt | lecture en cours…
```

Le FPS est une mesure de diagnostic légère, pas un profiler. Aucune dépendance
ajoutée.

---

## Production safety

Deux protections, dont une vérifiée sur le build réel.

**1. Import dynamique gardé** dans `apps/<game>/src/routes/+layout.svelte` :

```svelte
let DebugPanel = $state<Component | null>(null);
if (import.meta.env.DEV) {
    import('../dev/DebugPanel.svelte').then((module) => (DebugPanel = module.default));
}
```

En production, Vite replie `import.meta.env.DEV` à `false`, la branche devient
inatteignable et Rollup élimine le module **et ses fixtures**. Ce n'est pas un
`display:none` : le code n'existe pas dans le bundle.

**2. Vérification sur le build** — après `pnpm run build --filter=lines --force` :

```text
marqueur              fichiers du build le contenant
DebugPanel            0
debugScenarios        0
base-max-win          0
base-no-win           0
isLocalDebugMode      0
debug=true            0
DEBUG_QUERY_KEY       0
```

Et le comportement RGS de production reste intact — les quatre endpoints sont
toujours dans le bundle :

```text
/wallet/authenticate  1     /wallet/play       1
/wallet/end-round     1     /bet/event         1
```

À refaire à chaque release. Le seul `payoutMultiplier` restant vient de
`createPrimaryMachines` (code Stake), pas de nos fixtures.

---

## Adding a scenario for a future game

```text
1. Le Math définit un critère intéressant dans son game_config
2. Les simulations produisent les force records
3. Identifier le critère utile dans library/forces/force.json
4. Ajouter le scénario à apps/<game>/src/dev/debugScenarios.config.json
5. Régénérer (voir tooling/debug/README.md)
6. Ouvrir le Debug Panel
7. PLAY  -> vérifier le round
8. REPLAY -> reproduire à l'identique
```

Aucune étape ne repose sur l'attente du hasard.

Voir [`tooling/debug/README.md`](../tooling/debug/README.md) pour le format de
configuration et les deux types de sélection.

---

## What the Debug Panel must never do

```text
calculer un gain, un RTP, un résultat
tirer des reel stops
décider d'un bonus ou d'un multiplicateur
modifier directement la grille (forceScatter() et compagnie)
créer un second event system (DebugEvent, DebugEventBus…)
forcer un état de la machine XState (idle / playing / bonus)
lire math/ depuis le navigateur
embarquer la bibliothèque Math dans le frontend
contenir un secret, un sessionID, un token, une URL privée
apparaître dans un build de production
```

> **Ne jamais fabriquer le résultat dans le Debug Panel.** Il sélectionne un
> résultat Math existant et laisse le frontend jouer normalement.

Un scénario de gameplay pointe toujours vers un vrai Book. Pas de callback qui
bidouille l'UI.

---

## Vérification effectuée

Sur `http://localhost:3001/?debug=true`, dans un vrai navigateur (Chrome headless
piloté par CDP) :

```text
chargement              0 requête réseau échouée · 0 erreur console
jeu affiché             board, UI, arrière-plan rendus ; aucune modale d'erreur
panel                   7 scénarios listés, select scénario + select book, PLAY/REPLAY
base-no-win   PLAY      book #0,     3 events  → round terminé, état "prêt"
base-no-win   REPLAY    book #0                → même book, round terminé
bonus-round   PLAY      book #0,    35 events  → round terminé (56 s)
base-max-win  PLAY      book #1638, 62 events  → round terminé (139 s)
```

Les durées sont celles du rendu logiciel headless (~11 FPS, SwiftShader). Sur
GPU réel, elles sont bien plus courtes.

Les rounds bonus marquent des pauses sur les écrans `PRESS ANYWHERE TO CONTINUE`
(intro et outro des free spins) : c'est le comportement normal du jeu, pas un
blocage. Un round paraît « figé » tant qu'on n'a pas cliqué.

---

## Limites connues

### Le round n'est pas piloté par la machine XState

`playBet` est le point d'entrée que la machine appelle dans `onPlayGame` — le
rendu est donc identique à un vrai round. Mais le cycle complet de la machine
(`newGame` → `playGame` → `endGame`) n'est pas déclenché, car `newGame` appelle
`requestBet` sur le RGS.

Conséquence : pas de débit de solde, pas de `end-round`, pas d'autospin. Le
**rendu du round** est fidèle ; la **comptabilité du pari** ne l'est pas.

Aucun état de machine n'est forcé pour autant : le panel n'écrit pas dans XState.

### Slow motion

```text
SLOW MOTION DEFERRED UNTIL GAME TIMING CONTRACT EXISTS
```

Le sample n'expose pas de contrat de timing centralisé : les durées sont réparties
dans les composants et le mode turbo agit localement. Créer un `0.25x` imposerait
de toucher toutes les animations de `lines`. À reprendre quand un jeu Gogold
définira ses durées en constantes nommées (règle `CLAUDE.md`).

### Un event Math non géré par le frontend

Les books MAX WIN contiennent un event `wincap` :

```json
{ "index": 35, "type": "wincap", "amount": 500000 }
```

`bookEventHandlerMap` de `apps/lines` ne le gère pas. **Observé dans le
navigateur** en jouant `base-max-win` (book #1638, 62 events) : le round se
déroule intégralement jusqu'à `finalWin` et se termine normalement, avec une
seule trace console :

```text
Missing bookEventHandler in "bookEventHandlerMap" for: Object
```

C'est un **écart de contrat math ↔ frontend** : le Math émet un event que le
frontend ignore.

Non corrigé, décision assumée : `apps/lines` est un sample upstream, pas un jeu
Gogold ; on conserve le comportement amont. C'est exactement le type d'écart que
le Debug Panel sert à révéler — il n'apparaît qu'une fois sur ~900 rounds en jeu
naturel, contre deux clics ici.

Pour un vrai jeu Gogold, cet écart serait bloquant : voir la règle de
[Definition of Done](STORYBOOK.md#story-coverage-requirement-for-future-games).

---

## Ce que ce document ne fait PAS

Il ne décrit pas les scénarios réseau (`ERR_*`, timeout, maintenance) — ils
relèvent d'une étape QA dédiée. Il ne remplace pas [`STORYBOOK.md`](STORYBOOK.md)
ni le pipeline d'assets [`ASSET_PIPELINE.md`](ASSET_PIPELINE.md).

Il ne définit aucun jeu, aucune mécanique et aucun template.
