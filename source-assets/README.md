# source-assets

Fichiers **sources** de production : masters et exports intermédiaires.

Rien ici n'est livré au joueur. Les fichiers réellement chargés par un jeu vivent
dans `apps/<game>/static/assets/`.

Processus complet : [`docs/ASSET_PIPELINE.md`](../docs/ASSET_PIPELINE.md).
Nommage : [`docs/ASSETS.md`](../docs/ASSETS.md).

## Structure

```text
source-assets/
└── <game>/
    ├── symbols/
    ├── backgrounds/
    ├── ui/
    ├── fx/
    ├── animations/
    └── audio/
```

Un dossier par jeu, avec le même identifiant que `apps/<game>/`.

## Contenu attendu

| | Exemples |
| --- | --- |
| **Masters** | `.psd` `.psb` `.aep` `.blend` `.kra` `.xcf`, projets Spine `.spine`, sessions audio, rendus HD |
| **Exports intermédiaires** | frames PNG transparentes, planches avant packing, WAV/AIFF avant compression |

Un master peut être bien plus grand que l'asset runtime qui en dérive. C'est
normal : `MASTER ≠ RUNTIME`.

## Ces fichiers ne sont pas versionnés

`.gitignore` exclut tout le contenu de ce dossier — seul ce README est suivi.

Un seul `.psd` de symboles peut peser plusieurs centaines de Mo ; les committer
rendrait le repository inutilisable, et Git ne sait pas les compresser.

### La stratégie de stockage n'est pas encore décidée

Deux options restent ouvertes, à trancher séparément :

- un **stockage d'équipe** dédié (drive partagé, NAS, bucket) ;
- **Git LFS**, si Gogold décide de l'adopter.

> Git LFS n'est **pas** configuré. Ce choix engage tous les clones du repository
> et sera pris explicitement, pas en passant.

En attendant, ce dossier définit **où les sources se rangent en local** et
garantit que le pipeline a un point de départ nommé. Chacun conserve ses masters
selon la convention d'équipe en vigueur.

## Ce que ce dossier ne fait PAS

Il ne contient aucun asset runtime, n'est jamais lu par un build, et n'entre dans
aucun bundle. Aucun outil ne le convertit automatiquement.
