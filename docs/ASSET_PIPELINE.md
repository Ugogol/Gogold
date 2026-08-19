# Gogold Asset Pipeline

Comment un asset passe de la table du graphiste au build publié sur Stake.

Ce document décrit **le processus**. Les règles de nommage et d'organisation sont
dans [`ASSETS.md`](ASSETS.md) — les deux se complètent, ils ne se répètent pas.

Étiquettes d'autorité identiques à `ASSETS.md` : **[CONTRAT STAKE]**,
**[PATTERN SAMPLE]**, **[CONVENTION GOGOLD]**.

---

## Purpose

Qu'un asset suive toujours le même chemin, sans arbitrage au cas par cas :

```text
SOURCE → EXPORT → OPTIMIZE → PACK → CHECK → RUNTIME → STORYBOOK → BUILD
```

Une personne Art/Integration doit pouvoir exécuter cette chaîne seule.

---

## Source vs Export vs Runtime

Trois niveaux, jamais mélangés. **[CONVENTION GOGOLD]**

| Niveau | Contenu | Emplacement | Livré au joueur |
| --- | --- | --- | --- |
| **MASTER** | `.psd` `.aep` `.blend` `.kra` `.spine`, rendus HD, audio non compressé | `source-assets/<game>/` (hors Git — voir son README) | non |
| **EXPORT** | PNG transparents propres, frames numérotées, WAV/AIFF export | dossier de travail local ou `source-assets/` | non |
| **RUNTIME** | WebP, PNG, `.json` atlas, `.atlas` + skeleton Spine, audio compressé, fonts bitmap | `apps/<game>/static/assets/` | oui |

> `static/` ne contient **que** du runtime. Aucun fichier de travail, jamais.

Le checker refuse tout master trouvé dans un dossier runtime (voir plus bas).

---

## Runtime structure

Structure de référence, reprise des sample games. **[PATTERN SAMPLE]**

```text
apps/<game>/static/assets/
├── audio/     audio sprite (sounds.json + pistes)
├── fonts/     polices bitmap (.xml/.json + texture)
├── spines/    un sous-dossier par animation Spine
└── sprites/   un sous-dossier par atlas / image isolée
```

Détail du nommage : `ASSETS.md` §2, §3, §7, §9.

---

## Image formats

Aucun format n'est imposé par Stake. Ce qui compte est **ce que le code importe**.

### Fait vérifié dans `apps/lines`

Sur les 33 `.png` du sample, **27 ont un jumeau `.webp` de même nom** (21 MB).
Chaque `.atlas` et chaque `index.ts` qui dispose d'un WebP référence le WebP ;
aucun de ces 27 PNG n'est référencé nulle part.

> **Il n'existe aucun mécanisme de fallback PNG dans le SDK.** Un PNG posé à côté
> d'un WebP n'est pas un repli : c'est un reliquat d'export. Il alourdit le build
> sans jamais être chargé. Cela tranche la question laissée ouverte dans
> `ASSETS.md` §7.

### Règles Gogold **[CONVENTION GOGOLD]**

| Format | Quand l'utiliser |
| --- | --- |
| **WebP** | Format runtime par défaut : atlas, textures Spine, images isolées. Alpha inclus — l'alpha n'impose pas le PNG. |
| **PNG** | Seulement s'il est la **seule** représentation livrée, ou si un besoin lossless est démontré. Reste le format d'échange normal en EXPORT. |
| **JPG** | Grandes images strictement opaques (fond plein écran) si le gain de poids est réel et l'artefact invisible. |
| **SVG** | Éléments réellement vectoriels (icônes UI simples, formes plates). Pas pour l'illustration. |

Ne pas généraliser AVIF, KTX2 ou Basis : aucun besoin démontré, et rien ne prouve
qu'ils traversent la chaîne Pixi/Stake telle qu'intégrée.

> **Une seule représentation runtime par asset.** Si un WebP est livré, le PNG
> correspondant reste dans `source-assets/`.

---

## Resolution

Aucune dimension unique pour tous les assets. Des règles **par catégorie**.

### Le repère est l'espace de design, pas l'écran

Le jeu est dessiné dans un espace de design fixe, que `utils-layout` met ensuite à
l'échelle du viewport. Dans `apps/lines` (`src/game/constants.ts`) :

```text
desktop           1422 × 800 unités
landscape         1600 × 900 unités
portrait           800 × 1422 unités
cellule symbole   SYMBOL_SIZE = 120 unités   (soit 15 % de la hauteur desktop)
```

Un graphiste ne raisonne donc jamais en « pixels écran » : il raisonne en
**multiple de la cellule de design**.

### Ce que livre réellement le sample — mesuré

| | Valeur |
| --- | --- |
| Symboles statiques (`symbolsStatic`) | `sourceSize` **200 × 200 px** pour une cellule de 120 unités → **×1.67** |
| Symboles Spine (`spines/symbols/`) | atlas exporté à **0.2×** des unités du projet Spine, skeleton rechargé avec `scale: 2`, rendu dans la même cellule de 120 unités |
| Atlas les plus grands | 1889 × 1152 et 1791 × 1909 — tous sous 2048 |

Vérification du facteur Spine : l'attachment `beard` de `h1.json` mesure
714 × 489 unités, sa région dans `symbols.atlas` mesure 143 × 98 px — exactement
0.2×. Le `scale:0.2` de l'en-tête `.atlas` est **ignoré par le runtime**
(`TextureAtlas.js` ne lit pas ce champ) ; c'est le `scale: 2` d'`assets.ts` qui
agit, appliqué au skeleton.

### Matrice **[CONVENTION GOGOLD]**

| TYPE | SOURCE (master) | RUNTIME | RÈGLE |
| --- | --- | --- | --- |
| **Symbol static** | ≥ 4× la cellule | ≈ 2× la cellule de design | canvas identique pour toute la famille ; pas de surdimensionnement |
| **Symbol animated** | frames au même canvas que le static | atlas, ≈ 2× | dimensions **strictement** identiques entre frames |
| **Background** | HD, ≥ 2× la plus grande cible | texture au ratio utile, ≤ 2048 | éviter la texture géante ; JPG si strictement opaque |
| **UI** | vectoriel ou HD propre | ≈ 2× la taille affichée | marge Retina ; SVG seulement si réellement vectoriel |
| **FX** | selon besoin | atlas ou Spine, ≈ 2× | limiter la transparence vide — le trim la retire |
| **Font** | source vectorielle | bitmap font, atlas ≤ 2048 | uniquement les glyphes réellement utilisés |

### Pourquoi ≈ 2×

L'espace de design fait 800 unités de haut en desktop. Affiché sur un écran de
1080 px il est déjà agrandi ×1.35, sur du 1440 px ×1.8 — auquel s'ajoute le
`devicePixelRatio` sur mobile et Retina. **2× est le plancher pragmatique**, pas
un confort.

Au-delà, le gain visuel devient invisible et le coût mémoire réel : une texture
double en largeur coûte **quatre fois** la mémoire GPU.

> Ces facteurs sont à revalider quand la grille de Grogg et son `SYMBOL_SIZE`
> seront fixés. La méthode ne changera pas ; les nombres, peut-être.

### Deux règles qui ne se négocient pas

- **Un master n'est jamais agrandi.** On descend toujours d'une source plus
  grande. Un asset upscalé se voit.
- **Plafond de texture 2048 × 2048** (`CLAUDE.md`). Au-delà, découper ou réduire —
  ne pas activer le multipack par défaut.

---

## Animation strategy

Un symbole n'a pas besoin de cinq animations. **[CONVENTION GOGOLD]**

| État | Obligatoire | Remarque |
| --- | --- | --- |
| **Static** | oui | tout symbole en a un |
| **Land** | non | seulement si l'impact visuel le justifie |
| **Win** | selon DA | souvent réalisable en code (scale/glow/tint) sans nouvel asset |
| **Disappear / cascade** | non | privilégier une animation générique du moteur |
| **Anticipation** | non | réservée aux symboles qui déclenchent une mécanique |
| **Idle** | non | ne pas animer tous les symboles en permanence |

Objectif : **impact visuel élevé, poids faible, production rapide.**

---

## Code vs Spritesheet vs Spine

| Technique | À privilégier pour |
| --- | --- |
| **Code / Pixi** | scale, bounce, rotation, fade, glow, shake, déplacements simples, particules simples. Aucun asset supplémentaire. |
| **Spritesheet** | animation frame-by-frame courte, FX peint, transformation impossible à décrire par transformations. |
| **Spine** | animation complexe, personnage articulé, plusieurs animations partageant les mêmes pièces, réutilisation forte. |

Ordre de décision : **code d'abord**, spritesheet ensuite, Spine si les deux
premiers ne suffisent pas. Une spritesheet de 40 frames coûte plus cher qu'un
`scale` animé qui rend aussi bien.

Aucun moteur d'animation Gogold n'est créé : on utilise `pixi-svelte` et les
composants Stake.

---

## TexturePacker workflow

Preset validé : [`tooling/assets/texturepacker/`](../tooling/assets/texturepacker/).
Réglages, justification et commande CLI y sont documentés.

Résumé :

```powershell
& "C:\Program Files\CodeAndWeb\TexturePacker\bin\TexturePacker.exe" `
    tooling\assets\texturepacker\gogoldSprites.tps `
    source-assets\<game>\<sheet>\ `
    --sheet apps\<game>\static\assets\sprites\<sheet>\<sheet>.webp `
    --data  apps\<game>\static\assets\sprites\<sheet>\<sheet>.json
```

Le `.tps` fournit les réglages ; les chemins d'entrée/sortie sont passés en ligne
de commande. Le dossier de la spritesheet et ses fichiers partagent le même nom de
base (`ASSETS.md` §7).

### Deux types d'atlas — ne pas les confondre **[CONTRAT STAKE]**

`assets.ts` déclare un `type` qui change la façon dont les frames sont exposées
(`packages/pixi-svelte/src/lib/assetLoad.ts`) :

| `type` | Traitement | Usage |
| --- | --- | --- |
| `sprites` | les frames sont **fusionnées à plat** dans la map globale des assets | banque d'images (symboles statiques, UI) |
| `spriteSheet` | `Object.values(textures)` → **tableau ordonné** | animation frame-by-frame |

Deux conséquences directes :

1. Avec `sprites`, **les noms de frames sont un espace de noms global au jeu**.
   Deux atlas contenant `bg.png` s'écrasent silencieusement. Préfixer les frames
   par leur famille.
2. Avec `spriteSheet`, **l'ordre des frames est l'ordre des clés du JSON**. D'où
   la règle de numérotation ci-dessous.

---

## Frame alignment

L'erreur classique : frame 2 décalée de 8 px, frame 3 agrandie — l'animation
tremble.

### Numérotation **[CONVENTION GOGOLD]**

```text
✓ scatterWin_000  scatterWin_001  …  scatterWin_010
✗ scatterWin_1    scatterWin_2    …  scatterWin_10
```

Le zero-padding rend le tri lexical identique au tri numérique. Sans lui,
`10` se classe avant `2` et l'animation est jouée dans le désordre.

> Le sample Stake `sprites/coin/` utilise `1.png … 12.png` — exactement le cas
> fragile. On ne le corrige pas (`apps/lines` reste intact), on ne le reproduit
> pas.

### Canvas **[CONVENTION GOGOLD]**

Pour toutes les frames d'une même animation, et pour tous les symboles d'une même
famille :

- **même canvas logique** (ex. 200×200 pour toutes les frames d'un symbole) ;
- **même origine**, même centrage ; le contenu bouge *à l'intérieur* du canvas ;
- pas de redimensionnement involontaire entre frames ;
- marge transparente raisonnable — le trim la retire de l'atlas de toute façon.

### Le trim est sûr — vérifié

Le trim ne casse pas l'alignement : TexturePacker écrit `sourceSize` (canvas
d'origine) et `spriteSourceSize` (offset du contenu), et PixiJS reconstruit.

Vérifié avec le PixiJS du repo (8.8.1) sur un atlas produit par notre preset :
une frame source 200×200 dont le contenu est décalé ressort en **200×200,
`trim = x49 y34`**. Le canvas logique est préservé.

> Condition : que le canvas source soit réellement identique d'une frame à
> l'autre. Le trim préserve l'alignement ; il ne le répare pas.

### Pivot

PixiJS 8 lit le champ **`anchor`**, pas `pivot`
(`Spritesheet.mjs` → `defaultAnchor: data.anchor`). Le `pivot` présent dans les
atlas Stake est **ignoré au runtime**. Notre preset ne l'écrit pas ; les ancrages
se règlent dans le code.

---

## Audio workflow

```text
master (WAV/AIFF, non compressé)
   ↓ montage / mastering
export
   ↓ compression
runtime : audio sprite + sounds.json
   ↓
utils-sound (Howler)
```

Le SDK utilise un **audio sprite** : un fichier unique par format, `sounds.json`
décrivant les offsets. La séparation BGM / SFX / ambiance / voix est **logique**
(déclarée dans `sounds.json`), pas physique (`ASSETS.md` §11).

Ne créer aucun `AudioManager` Gogold : `utils-sound` fait le travail.

### Formats **[CONVENTION GOGOLD]**

Le sample livre quatre formats — `mp3`, `ogg`, `m4a`, `ac3` — soit **16.8 MB, 32 %
du poids de ses assets**. Aucune exigence Stake ne l'impose.

Gogold livre **MP3 + OGG** (règle `CLAUDE.md`), ce qui couvre les navigateurs
cibles. `m4a`/`ac3` ne sont ajoutés que si un navigateur cible échoue réellement.

WAV interdit en runtime — **[CONVENTION GOGOLD]**, décision Gogold (`CLAUDE.md`),
pas une contrainte Stake.

---

## Weight measurement

Deux mesures distinctes, à ne pas confondre. **[CONVENTION GOGOLD]**

| Mesure | Quoi | Comment |
| --- | --- | --- |
| **RUNTIME ASSETS SIZE** | `apps/<game>/static/assets/` | `node tooling/assets/check-assets.mjs apps/<game>/static/assets` |
| **FINAL FRONTEND BUILD SIZE** | `apps/<game>/build/` après build | mesure du dossier de build complet |

Le build ≠ les assets : il ajoute le bundle JS/CSS et un `index.html` volumineux
(`config-svelte` utilise `bundleStrategy: 'inline'`).

Relevé sur le sample Stake (référence, pas objectif) :

```text
RUNTIME ASSETS SIZE       51.9 MB   (155 fichiers)
FINAL FRONTEND BUILD SIZE 57 MB     (assets 53 MB + _app 1.2 MB + index.html 1.2 MB)
```

### Objectif interne Gogold

`CLAUDE.md` fixe : **15–25 MB idéalement, 35 MB maximum, moins de 5 MB au
chargement initial**.

> C'est un **objectif interne Gogold**, jamais une limite Stake. Stake ne publie
> aucun plafond de poids.

Le sample Stake est à 51.9 MB : il ne respecte pas cet objectif, et **on ne le
corrige pas** — c'est notre référence upstream intacte.

Le budget « chargement initial » se pilote par le flag `preload` de `assets.ts`
(voir plus bas), pas par le poids total.

### Budgets par catégorie

Aucun plafond par catégorie n'est fixé aujourd'hui. On **mesure d'abord** sur les
premières slots, puis on compare, puis on décide. Inventer `symbols = 8 MB` sans
données ne produirait qu'une règle qu'on contournerait.

Le checker fournit déjà la répartition par dossier et par extension.

---

## Runtime asset validation

```powershell
node tooling/assets/check-assets.mjs apps/<game>/static/assets
```

Signale les masters (`.psd`, `.aep`, `.blend`, `.wav`…), les fichiers temporaires
(`.tmp`, `.bak`, `Thumbs.db`…) et les dossiers hors convention. Sort en code 1 si
un fichier interdit est présent.

**Il ne supprime jamais rien.** Voir [`tooling/assets/`](../tooling/assets/).

---

## Final build measurement

Après `pnpm run build --filter=<game>`, mesurer `apps/<game>/build/`.

Le contrôle de release comparera les deux mesures à l'objectif interne. Le build
pipeline mis en place en A8 n'est pas modifié.

---

## Stake static-file constraint

Le frontend publié est **statique et autonome** **[CONTRAT STAKE]**.

```text
pas de Google Fonts au runtime
pas de CDN d'images
pas de CDN audio
aucun asset distant
```

Tout ce dont le jeu a besoin doit être dans `static/`, donc dans le build.

> `apps/lines/src/app.html` charge une police depuis `use.typekit.net`. C'est du
> code upstream laissé intact (voir `FRONTEND.md`). **Un jeu Gogold ne doit pas
> reprendre cette dépendance.**

Storybook n'est pas concerné : ce n'est pas le build publié.

---

## `assets.ts` — la source de vérité

`apps/<game>/src/game/assets.ts` déclare chaque asset :

```ts
symbolsStatic: {
    type: 'sprites',
    src: new URL('../../assets/sprites/symbolsStatic/symbolsStatic.json', import.meta.url).href,
},
```

`type` ∈ `spine | sprite | sprites | spriteSheet | font | audio`
(`packages/pixi-svelte/src/lib/types.ts`).

### La clé n'est pas le nom du fichier **[CONTRAT STAKE]**

Aucune règle mécanique ne relie la clé, l'ID math et le nom de fichier. Dans
`apps/lines` :

```text
winSmall     → MM_Localisation_winsmall.json
coins        → SD2_Coin.json
bigwin       → big_wins.atlas + mm_bigwin.json
goldFont     → mm_gold.xml
```

> **C'est `assets.ts` qui fait autorité sur la ressource réellement chargée.**
> Ne pas supposer `nom de fichier = ID math en minuscules`.

### `preload` pilote le chargement initial

`AssetsLoader.svelte` charge en **deux phases** : d'abord les assets marqués
`preload: true`, puis le reste avec une barre de progression.

C'est le levier direct du budget « moins de 5 MB au chargement initial » : n'y
mettre que l'écran de chargement, le fond et les sons d'amorçage.

---

## Standard workflow

```text
SOURCE       master dans source-assets/<game>/, jamais dans static/
   ↓
EXPORT       PNG transparents, canvas identique, frames zero-paddées (_000)
   ↓
OPTIMIZE     choix du format (WebP par défaut) ; une seule représentation runtime
   ↓
PACK         TexturePacker avec gogoldSprites.tps  |  export Spine  |  audio sprite
   ↓
CHECK        node tooling/assets/check-assets.mjs apps/<game>/static/assets
   ↓
INTEGRATE    déclarer dans src/game/assets.ts (type + src + preload éventuel)
   ↓
STORYBOOK    vérifier le rendu isolé
   ↓
BUILD        pnpm run build --filter=<game>
   ↓
CHECK SIZE   mesurer apps/<game>/build/ (FINAL FRONTEND BUILD SIZE)
```

---

## Ce que ce document ne fait PAS

Il ne définit pas les conventions de nommage (voir `ASSETS.md`), ne convertit
aucun asset, n'installe aucune chaîne de compression automatique, et ne fixe
aucun budget par catégorie tant que nous n'avons pas mesuré de vrai jeu.

Il ne crée aucun asset Grogg.
