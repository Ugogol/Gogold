# tooling/assets

Outils de **fabrication et de vérification** des assets Gogold.

Le processus complet est décrit dans [`docs/ASSET_PIPELINE.md`](../../docs/ASSET_PIPELINE.md).
Les conventions de nommage sont dans [`docs/ASSETS.md`](../../docs/ASSETS.md).

## Checker / transformation — la distinction

| | Fait quoi | Ce dossier |
| --- | --- | --- |
| **Checker** | lit, mesure, signale — ne modifie rien | `check-assets.mjs` |
| **Transformation** | produit ou convertit des fichiers | TexturePacker (outil externe), Spine, encodage audio |

Aucun script Gogold ne convertit d'assets en masse. La transformation reste
manuelle et outillée, pour garder le contrôle sur la qualité visuelle.

## check-assets.mjs

Mesure un dossier d'assets runtime et signale ce qui n'a rien à y faire.

```powershell
node tooling/assets/check-assets.mjs apps/lines/static/assets
node tooling/assets/check-assets.mjs apps/lines/static/assets --json
```

Node >= 22, aucune dépendance.

### Ce qu'il produit

```text
RUNTIME ASSETS SIZE      poids total + nombre de fichiers
Poids par dossier        audio / fonts / spines / sprites
Poids par extension      .webp .png .mp3 …
10 fichiers les plus lourds
Formats rencontrés
Validation runtime       masters, fichiers temporaires, dossiers hors convention
```

### Codes de sortie

```text
0   aucun fichier interdit
1   master (.psd .aep .blend .wav …) ou fichier temporaire (.tmp .bak …) détecté
2   argument ou dossier invalide
```

Utilisable comme garde-fou avant publication.

### Ce qu'il ne fait pas

Il **ne supprime, ne déplace, ne convertit et ne compresse rien**. Il lit, il
analyse, il signale. Les corrections sont faites à la main.

Il ne juge pas la qualité visuelle, ne vérifie pas le contenu des atlas, et ne
mesure pas le build final (voir `docs/ASSET_PIPELINE.md` → *Final build
measurement*).

## texturepacker/

Preset validé pour produire des atlas consommables par le frontend Stake.
Voir [`texturepacker/README.md`](texturepacker/README.md).
