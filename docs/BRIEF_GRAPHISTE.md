# Brief graphiste — assets Gogold

Tout ce qu'il faut savoir pour livrer un asset exploitable du premier coup.

Aucune connaissance technique requise. Ce document est autonome : il renvoie aux
docs détaillées seulement si tu veux le « pourquoi ».

---

## 1. En deux phrases

Tu produis en **haute résolution**, tu livres des **PNG transparents propres**,
et l'intégration se charge de convertir, packer et optimiser.

Ce que tu livres n'est jamais ce qui part dans le jeu — c'est normal.

---

## 2. Ce que tu livres

| | Format | Remarque |
| --- | --- | --- |
| **Images fixes** | PNG 32 bits (alpha) | jamais de fond blanc « qui fera l'affaire » |
| **Frames d'animation** | PNG 32 bits numérotés | voir §5 |
| **Illustration opaque plein cadre** | PNG ou JPG qualité maximale | fond, ciel, décor sans transparence |
| **Icône réellement vectorielle** | SVG | seulement si c'est vraiment du vectoriel |
| **Animation complexe** | projet Spine + export | personnage articulé, pièces réutilisées |
| **Master** | `.psd` `.aep` `.blend` `.kra` | à conserver, **jamais** dans le dossier du jeu |

> Tu ne livres **pas** de WebP. La conversion est faite à l'intégration, avec des
> réglages contrôlés. Si tu livres un WebP compressé, la perte est déjà faite et
> irrattrapable.

---

## 3. À quelle taille produire

Le jeu ne raisonne pas en pixels d'écran mais en **cellules**. Une cellule de
symbole est l'unité de référence ; sa taille exacte est fixée par l'intégration au
début du projet.

Règle simple :

```text
master   ≥ 4 × la taille d'affichage
livraison  ≈ 2 × la taille d'affichage
```

Le ×2 n'est pas du confort : l'écran de jeu est agrandi pour remplir la fenêtre,
et les écrans Retina doublent encore la densité.

| Type | Master | Livraison |
| --- | --- | --- |
| Symbole (fixe ou animé) | ≥ 4× la cellule | ≈ 2× la cellule |
| Fond | ≥ 2× la plus grande cible | ratio utile, jamais > 2048 px de côté |
| Élément d'UI | vectoriel ou HD propre | ≈ 2× la taille affichée |
| FX | selon le besoin | ≈ 2× |

**Plafond absolu : 2048 × 2048 px** pour une image livrée. Au-delà, préviens
l'intégration plutôt que de découper toi-même.

**On ne remonte jamais une image.** Produis grand, on réduit. Un agrandissement
se voit toujours.

---

## 4. Le canvas — le point le plus important

C'est ici que 90 % des problèmes arrivent.

Pour **toutes les frames d'une même animation** et **tous les symboles d'une même
famille** :

- **même taille de canvas** (ex. tous les symboles sur 400 × 400) ;
- **même centrage**, même origine ;
- le dessin peut bouger *à l'intérieur* du canvas — c'est fait pour ;
- ne redimensionne pas le canvas entre deux frames ;
- laisse une marge transparente confortable : elle est retirée automatiquement.

```text
✓ 12 frames toutes en 400 × 400, le personnage bouge dedans
✗ frame 1 en 400 × 400, frame 2 recadrée en 380 × 390
```

Si les canvas diffèrent, l'animation **saute** à l'écran. C'est invisible dans ton
logiciel, très visible dans le jeu.

---

## 5. Nommer les fichiers

### Règles générales

- **camelCase** : `boardFrame`, `freeSpins`, `scatterLand`
- pas d'espace, pas d'accent, pas de caractère spécial
- le nom dit **ce que c'est** ou **ce que ça fait**, jamais son historique

```text
✓ scatterWin.png   barrelFull.png   freeSpinsIntro.png
✗ scatter_final2.png   Symbole1 (copie).png   testAnim_OK.png
```

Pas de `final`, `final2`, `new`, `v3`, `test`, `ok`. L'historique est géré par
l'outil de version, pas par le nom.

### États d'un même élément

Le nom de base d'abord, l'état ensuite — tout se regroupe au tri :

```text
boardFrame → boardFrameActive       barrel → barrelFull
background → backgroundFreeSpins
```

### Frames d'animation — numérotation

**Toujours trois chiffres, à partir de 000 :**

```text
✓ scatterWin_000.png  scatterWin_001.png  …  scatterWin_012.png
✗ scatterWin_1.png    scatterWin_2.png    …  scatterWin_10.png
```

Sans les zéros, l'ordinateur classe `10` avant `2` et l'animation est jouée dans
le désordre. Ce n'est pas une préférence esthétique.

---

## 6. Ce qu'il ne faut pas livrer dans le dossier du jeu

```text
.psd  .psb  .aep  .blend  .kra  .xcf   fichiers de travail
.wav  .aiff  .flac                     audio non compressé
rendus 4K « au cas où »
doublons : hero.png ET hero.webp
fichiers .bak, copies, Thumbs.db
```

Un contrôle automatique bloque la livraison si l'un d'eux s'y trouve. Les masters
ont leur place — voir §8 — mais pas celle-là.

---

## 7. Combien ça peut peser

Objectif interne Gogold pour un jeu complet :

```text
idéal    15 – 25 MB
maximum  35 MB
```

Ce n'est pas une limite imposée par la plateforme, c'est notre exigence de
qualité : un jeu lourd se charge mal en 4G, et beaucoup de joueurs sont en
mobile.

Concrètement : mieux vaut **six symboles superbes** que quinze animations
moyennes qui saturent le budget.

En cas de doute sur un asset volumineux (grand fond, longue animation), demande
avant de produire, pas après.

---

## 8. Où déposer les fichiers

```text
source-assets/<jeu>/
├── symbols/
├── backgrounds/
├── ui/
├── fx/
├── animations/
└── audio/
```

Masters **et** exports vont là. L'intégration s'occupe de la suite : conversion,
packing, mise en jeu.

---

## 9. Checklist avant d'envoyer

- [ ] PNG transparent (ou JPG si strictement opaque)
- [ ] Toutes les frames d'une animation ont **exactement** le même canvas
- [ ] Frames numérotées `_000`, `_001`, `_002`…
- [ ] camelCase, sans accent ni espace
- [ ] Aucun `final`, `v2`, `test`, `copie` dans le nom
- [ ] Rien ne dépasse 2048 px de côté
- [ ] Le master est conservé, séparé de la livraison
- [ ] Les états d'un même élément partagent le nom de base

---

## Pour aller plus loin

- Conventions de nommage complètes : [`ASSETS.md`](ASSETS.md)
- Processus technique, formats runtime, TexturePacker : [`ASSET_PIPELINE.md`](ASSET_PIPELINE.md)

Une question sur un cas non couvert ici : demande à l'intégration **avant** de
lancer la production. Une règle manquante coûte moins cher qu'une série de
symboles à refaire.
