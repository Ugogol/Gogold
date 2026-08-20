---
paths:
  - "apps/*/static/assets/**"
  - "source-assets/**"
  - "tooling/assets/**"
---

# Assets

Référence détaillée : `docs/ASSETS.md` (conventions de nommage),
`docs/ASSET_PIPELINE.md` (processus), `docs/BRIEF_GRAPHISTE.md` (brief externe).

## Trois niveaux, jamais mélangés

```text
MASTER   .psd .aep .blend .kra, rendus HD, audio non compressé  → source-assets/
EXPORT   PNG transparents propres, frames numérotées            → source-assets/
RUNTIME  WebP/PNG, atlas .json, Spine, audio compressé, fonts   → apps/<game>/static/assets/
```

**Aucun master dans `static/assets/`.** Le checker le refuse :

```powershell
node tooling/assets/check-assets.mjs apps/<game>/static/assets
```

Il lit, analyse et signale — il ne supprime jamais rien.

## Structure runtime

```text
apps/<game>/static/assets/{audio,fonts,spines,sprites}/
```

C'est le pattern des samples Stake, adopté par cohérence — pas une exigence de
plateforme.

## Formats

Aucun format n'est imposé universellement. Choisir selon qualité, poids, alpha,
dimensions, mémoire GPU, fréquence d'usage et type d'animation.

WebP est le format runtime par défaut du projet ; PNG reste utile quand il est la
seule représentation livrée ou qu'un besoin lossless est démontré. **Il n'existe
aucun mécanisme de fallback PNG** : un PNG posé à côté d'un WebP est un reliquat
d'export qui alourdit le build sans jamais être chargé.

Une seule représentation runtime par asset. Le format réellement chargé est celui
qu'importe le code (`assets.ts`, `index.ts`, `.atlas`), pas celui présent dans le
dossier.

## Frames d'animation

Même canvas logique, même origine, dimensions identiques entre frames.
Numérotation zero-paddée (`nom_000`) pour que le tri lexical soit le tri
numérique. Le trim préserve l'alignement via `sourceSize`/`spriteSourceSize` ;
il ne le répare pas.

## Atlas

TexturePacker avec le preset validé `tooling/assets/texturepacker/`. Ne pas
inventer de réglages : ils sont justifiés un par un dans son README.

## Autonomie du build

Le frontend publié est statique et autonome : aucun asset distant, aucun CDN
d'image, d'audio ou de police au runtime. Tout ce dont le jeu a besoin est dans
`static/`.

## Poids

Les cibles de poids Gogold sont des **objectifs internes**, jamais des limites
Stake. Mesurer d'abord (`check-assets`, `check-production-build`), comparer,
optimiser ensuite. Ne pas inventer de budget par catégorie sans données.

Ne jamais présenter une convention Gogold (plafond de texture, format, budget)
comme une exigence de la plateforme.
