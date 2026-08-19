# Gogold Tooling

Scripts et outils servant à automatiser le développement des jeux Gogold.

## Contenu

- [`assets/`](assets/) — mesure et validation des assets runtime, preset
  TexturePacker. Voir [`docs/ASSET_PIPELINE.md`](../docs/ASSET_PIPELINE.md).

Exemples futurs :

- compression des images
- validation des noms de fichiers
- création automatique d'un nouveau jeu
- validation avant publication Stake

## Statut

Seul l'outillage assets est implémenté. Le reste réserve l'emplacement et
documente son rôle.

## Ce que ce dossier ne fait PAS

Il ne contient pas de code embarqué dans le bundle livré au joueur. Les outils
servent à fabriquer et vérifier les jeux, jamais à les exécuter.
