# TexturePacker — preset Gogold

`gogoldSprites.tps` — preset validé pour produire des atlas consommés par le
frontend Stake déjà intégré.

```text
PRESET GENERATED AND TESTED
TexturePacker 8.2.0 (64 bit)
```

Le `.tps` a été **produit par TexturePacker lui-même** (`--save`), pas écrit à la
main. Il ne contient aucun chemin absolu : les entrées/sorties sont passées en
ligne de commande.

## Utilisation

```powershell
$TP = "C:\Program Files\CodeAndWeb\TexturePacker\bin\TexturePacker.exe"

& $TP tooling\assets\texturepacker\gogoldSprites.tps `
      source-assets\<game>\<sheet>\ `
      --sheet apps\<game>\static\assets\sprites\<sheet>\<sheet>.webp `
      --data  apps\<game>\static\assets\sprites\<sheet>\<sheet>.json
```

Le `.tps` fournit les réglages, le dossier source fournit les frames. Le dossier
de sortie et ses fichiers partagent le même nom de base (`docs/ASSETS.md` §7).

En interface graphique : `Fichier ▸ Ouvrir` sur `gogoldSprites.tps`, glisser les
sprites, définir les chemins de sortie, `Publish`.

## Réglages et justification

Chaque valeur vient d'une observation, pas d'une préférence.

| Réglage | Valeur | Pourquoi |
| --- | --- | --- |
| `dataFormat` | `pixijs4` | Exporteur PixiJS. Produit exactement le jeu de champs lu par PixiJS 8 et présent dans les atlas Stake. |
| `textureFormat` | `webp` | Format runtime effectivement importé par les `index.ts` et les `.atlas` du sample. |
| `webpQualityLevel` | `101` (lossless) | Défaut du preset. Descendre vers 90 est le premier levier de poids si un atlas est trop lourd — à valider à l'œil. |
| `trimMode` | `Trim` | Utilisé par les atlas Stake (`trimmed: true`). `sourceSize` + `spriteSourceSize` préservent l'alignement. |
| `trimSpriteNames` | `false` | Les frames Stake gardent leur extension (`h1.webp`, `s.png`). Les noms de frames sont des clés : les changer casserait les références. |
| `allowRotation` | `true` | Les atlas Stake contiennent des frames `rotated: true`. PixiJS gère (`rotate: 2`). |
| `shapePadding` | `2` | Évite le bleeding entre sprites voisins en filtrage linéaire. |
| `borderPadding` | `2` | Même raison, sur le bord de la texture. |
| `extrude` | `1` | Duplique le pixel de bord : supprime les liserés sur sprite mis à l'échelle. |
| `alphaHandling` | `ClearTransparentPixels` | Nettoie les pixels transparents : évite les halos sombres autour des sprites détourés. |
| `maxTextureSize` | `2048 × 2048` | Plafond `CLAUDE.md`. Les atlas du sample restent sous cette limite (max observé 1889×1909). |
| `sizeConstraints` | `AnySize` | Les atlas Stake ne sont pas en puissance de deux (386×1645, 406×213). Forcer POT gaspillerait de la mémoire. |
| `multiPackMode` | `Off` | Aucun atlas du sample n'utilise le multipack. À n'activer que si un atlas dépasse réellement 2048². |
| `algorithm` | `MaxRects` | Meilleur remplissage que Basic pour des sprites de tailles hétérogènes. |
| `writePivotPoints` | `false` | **PixiJS 8 lit `anchor`, pas `pivot`** (`Spritesheet.mjs` → `defaultAnchor: data.anchor`). Le `pivot` des atlas Stake est inerte. Les ancrages se règlent dans le code. |

## Validation effectuée

1. Atlas de test généré à partir du preset (4 frames 200×200 à contenu décalé +
   1 sprite large).
2. Structure comparée à l'atlas Stake `symbolsStatic.json` : mêmes champs
   (`frame`, `rotated`, `trimmed`, `spriteSourceSize`, `sourceSize`) et même
   `meta` (`app`, `version`, `image`, `format`, `size`, `scale`, `smartupdate`).
3. **Les deux atlas ont été parsés avec le PixiJS du repo (8.8.1)** via
   `Spritesheet.parse()` :

```text
[preset Gogold]     5 frames — testCoin_001.png : 200x200 rotate=0 trim=x49 y34
[Stake reference]  17 frames — explodedW.png    : 200x200 rotate=2 trim=x9 y22
RESULT: BOTH PARSED BY PIXIJS 8 — OK
```

Une frame trimée ressort à ses **dimensions source complètes** : l'alignement
frame-à-frame est préservé.

## Licence

Le CLI signale que trim, rotation, extrude, WebP et MaxRects sont des
fonctionnalités **TexturePacker Pro** :

```text
TexturePacker:: warning: List of advanced features you are using:
```

Elles nécessitent une licence. Sans licence valide, ces réglages seraient
désactivés et les atlas produits ne correspondraient plus à ce preset.

## Frames d'animation

Pour un atlas de type `spriteSheet`, l'ordre de lecture est **l'ordre des clés du
JSON**. Nommer les frames avec zero-padding (`scatterWin_000`) pour que le tri
lexical soit le tri numérique.

Détail et démonstration : `docs/ASSET_PIPELINE.md` → *Frame alignment*.
