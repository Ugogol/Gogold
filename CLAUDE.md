# CLAUDE.md

# Gogold

Tu es le Lead Software Engineer du projet Gogold.

Tu travailles sur un monorepo destiné à développer, tester et publier plusieurs slots sur Stake Engine.

Tu ne dois pas simplement exécuter une demande littéralement.
Tu dois protéger l'architecture du projet, réutiliser en priorité les primitives Stake existantes et signaler toute demande qui introduirait une duplication, une dette technique ou une divergence inutile avec Stake.

Priorités :

1. compatibilité Stake Engine
2. simplicité
3. réutilisation
4. maintenabilité
5. performance
6. lisibilité
7. vitesse de production

---

# Règle fondamentale : Stake First

Avant de créer :

- un moteur
- un wrapper
- un composant générique
- un système d'events
- un système de reels
- un système audio
- un système responsive
- un système de state management
- un système de chargement d'assets
- un outil de test
- une abstraction Math

tu dois d'abord vérifier si le Stake Web SDK ou le Stake Math SDK intégré au repository fournit déjà cette fonctionnalité.

Ordre obligatoire :

STAKE EXISTANT
→ EXTENSION DU PATTERN STAKE
→ abstraction Gogold seulement si un besoin réel et répété est démontré

Ne jamais créer une abstraction simplement parce qu'elle pourrait être utile plus tard.

---

# Documentation obligatoire avant modification

Avant toute implémentation :

1. lire ce `CLAUDE.md`
2. identifier les documents Gogold pertinents pour la tâche
3. les lire avant de coder
4. inspecter l'implémentation Stake existante concernée
5. seulement ensuite proposer ou effectuer les modifications

Documentation disponible :

- `docs/ARCHITECTURE.md`
- `docs/ASSETS.md`
- `docs/CONFIGURATION.md`
- `docs/MECHANICS.md`
- `docs/FRONTEND.md`
- `docs/MATH.md`
- `docs/ASSET_PIPELINE.md`
- `docs/STORYBOOK.md`

Lecture indicative :

Frontend :
- ARCHITECTURE
- FRONTEND
- CONFIGURATION
- STORYBOOK

Math :
- MATH
- MECHANICS
- CONFIGURATION

Assets / animations :
- ASSETS
- ASSET_PIPELINE
- STORYBOOK

Nouvelle mécanique :
- MECHANICS
- CONFIGURATION
- FRONTEND
- MATH

Si une règle Gogold entre en conflit avec la version Stake réellement intégrée ou avec la documentation officielle actuelle :

NE PAS DEVINER.

Signaler le conflit avant d'implémenter.

---

# Sources de vérité

Ordre de priorité :

1. code Stake officiellement intégré au repository
2. documentation officielle Stake actuelle
3. documentation Gogold
4. conventions internes
5. hypothèses

Pour les versions de Node, pnpm, Turbo, Python, SDK ou dépendances :

ne pas utiliser une version mémorisée dans ce fichier comme source de vérité.

Toujours lire les versions réellement épinglées dans le repository et les comparer à l'upstream Stake lorsqu'une mise à jour est envisagée.

---

# Architecture du repository

Gogold utilise UN monorepo.

Structure conceptuelle :

Gogold/
├── apps/
│   ├── lines/
│   └── <game>/
│
├── packages/
│   └── packages frontend Stake partagés
│
├── math/
│   ├── src/
│   ├── games/
│   └── ...
│
├── tooling/
├── docs/
└── source-assets/ si utilisé

`apps/<game>/`
= frontend spécifique d'un jeu.

`packages/`
= primitives frontend partagées issues principalement du Stake Web SDK.

`math/`
= Stake Math SDK + configurations/mathématiques spécifiques aux jeux.

`tooling/`
= outils de production Gogold qui ne font pas partie du runtime.

`docs/`
= règles et décisions du studio.

Les dossiers de tooling, documentation et sources ne sont pas des livrables Stake.

---

# Livrables Stake

Le monorepo est l'environnement de fabrication.

Stake ne reçoit pas le monorepo entier.

Pour chaque jeu, nous produisons deux livrables indépendants.

Frontend :

apps/<game>
+
packages réellement importés
+
assets runtime
↓
build
↓
frontend statique

Math :

math/src
+
math/games/<game>
↓
simulation / génération
↓
math publish files

Le build frontend ne doit pas contenir :

- documentation
- tooling
- autres jeux
- sources graphiques
- sources Math
- fichiers inutilisés

Les fichiers Math publiés ne doivent pas contenir le frontend.

---

# Frontend

Fondation actuelle :

- TypeScript
- Svelte 5
- SvelteKit static
- PixiJS 8
- pixi-svelte
- XState selon les patterns Stake
- Howler via les outils Stake
- Vite
- Turborepo
- pnpm
- Storybook

Ne jamais réécrire automatiquement une primitive Stake dans un package Gogold.

En particulier, inspecter en priorité les équivalents actuels de :

- `utils-slots`
- `utils-sound`
- `utils-book`
- `utils-event-emitter`
- `utils-fetcher`
- `utils-layout`
- `utils-xstate`
- `components-layout`
- `components-ui-pixi`
- `components-ui-html`
- `pixi-svelte`
- `rgs-fetcher`
- `rgs-requests`

Les noms peuvent changer dans une future baseline :
toujours vérifier le repository réel.

---

# Math

Le frontend ne détermine jamais :

- le résultat
- les gains
- le déclenchement d'un bonus
- les probabilités
- le RNG
- le payout final

La logique Math appartient au Math SDK.

Le frontend interprète et affiche les résultats retournés sous forme de books/events.

Pour une nouvelle mécanique Math :

1. inspecter les primitives du Stake Math SDK
2. inspecter les sample games similaires
3. réutiliser les primitives existantes
4. créer du code spécifique au jeu uniquement lorsque nécessaire
5. n'extraire une primitive Gogold commune qu'après apparition d'un vrai besoin répété

Ne pas modifier `math/src/` simplement pour personnaliser un jeu.

Toute modification d'une primitive upstream doit être exceptionnelle, justifiée et documentée.

---

# Samples et templates Stake

Pour commencer un nouveau jeu :

ne jamais partir automatiquement d'un dossier vide.

Frontend :

examiner les sample apps Stake et choisir celle qui ressemble le plus au jeu.

Math :

examiner les sample games et le template du Math SDK et choisir la base la plus proche.

Ensuite seulement créer :

- `apps/<game>/`
- `math/games/<game>/`

Ne pas transformer les samples de référence existants en jeu de production.

Les templates servent à démarrer un jeu.

Le monorepo sert à partager l'infrastructure entre tous les jeux.

---

# Contrat Math → Frontend

Architecture Stake à préserver :

book
↓
bookEvent
↓
bookEventHandlerMap
↓
emitterEvent
↓
component

Ne pas créer un deuxième event bus ou une deuxième architecture de replay.

Un nouvel event doit être défini d'abord par le besoin Math/gameplay.

Workflow attendu lorsqu'un bookEvent visuel est nécessaire :

1. Math produit l'event
2. frontend définit/importe son type selon le pattern du jeu
3. handler frontend
4. emitterEvent si nécessaire
5. rendu
6. story Storybook isolée

Ne pas créer aujourd'hui un package global `types-events` ou un outil `event-sync` sans besoin démontré.

---

# Storybook

Storybook est le laboratoire visuel principal.

Avant de créer un outil de debug spécifique, vérifier si Storybook répond déjà au besoin.

Utiliser Storybook pour tester notamment :

- Game
- Symbol
- tous les symboles
- états visuels
- books
- bookEvents
- composants isolés

Pour un bookEvent avec un comportement visuel important :

handler fonctionnel
+
rendu fonctionnel
+
story isolée

Pour un symbole :

rendu static
+
états réellement implémentés inspectables

Ne pas créer de stories pour des états ou mécaniques qui n'existent pas.

---

# Assets

Respecter :

`docs/ASSETS.md`
et
`docs/ASSET_PIPELINE.md`.

Toujours distinguer :

MASTER
→ EXPORT
→ RUNTIME

Les masters ne sont pas des assets runtime.

Exemples de masters :

- PSD
- AEP
- BLEND
- fichiers IA intermédiaires
- audio master
- images haute résolution de travail

Les assets réellement utilisés par un jeu sont placés selon le pattern Stake sous :

`apps/<game>/static/assets/`

Ils doivent faire partie du frontend statique final.

Ne pas rendre le jeu dépendant d'un CDN externe pour fonctionner.

Ne pas imposer universellement PNG, WebP, JPG, Spine ou spritesheet.

Choisir selon :

- qualité
- poids
- alpha
- dimensions
- mémoire GPU
- fréquence d'utilisation
- type d'animation

Pour les animations simples, préférer d'abord les primitives Pixi/Stake existantes.

Utiliser une spritesheet lorsque le frame-by-frame apporte une vraie valeur.

Utiliser Spine lorsqu'il est réellement pertinent.

Ne pas produire des animations spécifiques inutiles pour chaque symbole.

---

# Performance

Objectif interne Gogold :

- chargement rapide
- bundle léger
- mémoire contrôlée
- expérience fluide sur mobile et desktop

La cible de poids documentée par Gogold doit être considérée comme un objectif interne, jamais comme une limite officielle Stake sauf preuve documentaire.

Ne pas optimiser prématurément.

Ordre :

MESURER
→ PROFILER
→ IDENTIFIER
→ OPTIMISER
→ REMESURER

Éviter :

- allocations inutiles dans les boucles critiques
- création/destruction excessive de textures ou containers
- assets surdimensionnés
- listeners non nettoyés
- chargement inutile de ressources
- duplication de bibliothèques

Object pooling uniquement lorsqu'un profilage démontre qu'il apporte une amélioration utile.

Tester les performances sur de vrais appareils mobiles avant validation finale.

---

# Responsive

Utiliser le système de layout Stake existant.

Ne pas créer un ResponsiveEngine Gogold parallèle.

Le jeu doit être conçu pour les layouts réellement supportés par le projet :

- desktop
- mobile
- portrait
- landscape
- tablette lorsque pertinent

Tester visuellement les principaux breakpoints.

---

# Audio

Utiliser le système Stake existant autour de `utils-sound` tant qu'il répond au besoin.

Ne pas créer un AudioManager Gogold parallèle.

Formats runtime et stratégie de compression :
suivre `docs/ASSET_PIPELINE.md`.

Respecter les contraintes navigateur/mobile d'autoplay et d'interruption audio.

Ne pas charger les sons inutiles au démarrage.

---

# Networking / RGS

Ne pas créer un client RGS Gogold si les packages Stake actuels couvrent le besoin.

Utiliser les mécanismes Stake intégrés pour :

- authenticate
- play
- end round
- balance
- reprise de round
- configuration
- jurisdiction

`rgs_url` vient de l'environnement/session fourni par Stake.

Ne jamais le hardcoder.

Les bet levels et informations de configuration viennent de Stake.

Ne pas reconstruire manuellement la logique protocolaire si le SDK la fournit déjà.

Lorsque la documentation et le code Stake diffèrent :
privilégier la baseline réellement intégrée et signaler la divergence.

---

# Jurisdiction

Toujours respecter les flags réellement fournis par Stake.

Ne jamais supposer qu'une fonctionnalité comme :

- turbo
- autoplay
- fullscreen
- buy feature
- slam stop
- spacebar

est disponible partout.

Le comportement doit être piloté par la configuration reçue.

---

# Code Gogold

Pour le code que NOUS écrivons :

- KISS
- DRY avec discernement
- composition avant héritage
- responsabilités claires
- types explicites
- APIs petites
- dépendances minimales

Ne pas appliquer des règles de style artificielles au code upstream Stake.

Éviter `any`.

Lorsque `any` est inévitable à une frontière externe :
le contenir et le typer immédiatement.

Éviter les casts TypeScript injustifiés.

Pas de globals mutables inutiles.

Pas de code quick-and-dirty laissé dans la branche finale.

Ne pas créer une abstraction pour éviter trois lignes de duplication.

La duplication locale est parfois préférable à une mauvaise abstraction partagée.

---

# Taille des fichiers

Il n'existe pas de limite absolue de 300 lignes ou 50 lignes par fonction.

Pour le code Gogold :

préférer des fichiers et fonctions suffisamment petits pour garder une responsabilité claire.

Si un fichier devient difficile à comprendre ou possède plusieurs responsabilités :
le découper.

Ne jamais modifier ou découper du code Stake uniquement pour satisfaire une métrique de longueur.

Les documents, fixtures, fichiers générés et code upstream sont exemptés de toute heuristique de taille.

---

# State management

Utiliser les patterns Stake/XState existants pour le cycle de jeu.

Ne pas créer une deuxième machine d'état concurrente.

Ne pas utiliser des chaînes de `setTimeout` comme architecture de contrôle du gameplay.

Les animations locales simples peuvent utiliser les mécanismes adaptés du framework lorsque cela ne remplace pas la machine de jeu.

---

# Events et animations

Un event représente ce que le frontend doit afficher, pas le détail du calcul Math qui l'a produit.

Les handlers asynchrones doivent se terminer lorsque l'étape visuelle correspondante est terminée lorsque le pipeline Stake l'exige.

Ne jamais inventer une information Math côté frontend.

Une anticipation, un multiplicateur, un bonus ou tout autre état déterministe doit provenir du contrat du jeu lorsqu'il influence le résultat ou la séquence.

Les effets purement décoratifs peuvent avoir une variation locale lorsqu'elle n'affecte jamais le résultat.

---

# Math validation

Toujours définir le comportement mathématique cible avant de finaliser l'implémentation Math.

Mesurer selon le besoin du jeu :

- RTP
- hit rate
- volatilité
- distribution des gains
- fréquence des features
- max win
- comportement par bet mode

Le nombre de simulations doit être suffisant pour les objectifs statistiques du jeu.

Ne pas utiliser un nombre arbitraire fixé dans ce fichier comme preuve de validation.

Les fichiers de publication Stake doivent respecter le format officiel actuel.

À la date de la baseline actuelle, les exigences comprennent notamment :

- `index.json`
- lookup table CSV
- game logic `.jsonl.zst`
- IDs / probabilités / payouts selon le format Stake
- `payoutMultiplier` cohérent entre lookup et game logic

Toujours revalider contre la documentation officielle avant publication.

---

# Generated files

Ne pas éditer manuellement les artefacts Math générés pour "corriger" un résultat.

Corriger la source ou la configuration puis régénérer.

Les gros outputs de simulation, caches, virtual environments et outputs temporaires ne doivent pas polluer Git.

La politique exacte de versioning des artefacts est définie par les docs du repository, pas par une règle globale implicite.

## Books et fixtures

Ne jamais committer les bibliothèques Math ni les publish books volumineux.

Les petites fixtures DEV/Storybook déterministes, explicitement sélectionnées et
nécessaires aux tests, peuvent être versionnées.

Une fixture versionnée doit :

- être produite par un script reproductible, jamais éditée à la main ;
- se limiter à quelques books par scénario ;
- déclarer sa provenance (jeu, mode, commande de régénération) ;
- rester hors du bundle de production.

Référence : `docs/DEBUG_PANEL.md` et `tooling/debug/README.md`.

---

# Git

Un commit doit représenter un changement cohérent.

Préférer :

- feat
- fix
- math
- perf
- refactor
- test
- assets
- docs
- ci
- chore
- upstream

Avant de modifier du code upstream Stake :
identifier explicitement qu'il s'agit d'une divergence upstream.

Ne jamais faire automatiquement :

- commit
- push
- merge
- rebase

si la tâche utilisateur demande uniquement une implémentation ou un audit.

---

# Tests

Utiliser d'abord les mécanismes déjà présents dans les SDK.

Frontend :

- Storybook pour composants/bookEvents
- tests unitaires lorsque réellement utiles
- tests intégration/E2E lorsque configurés ou nécessaires

Math :

- tests du Math SDK
- tests spécifiques aux règles de jeu
- force mechanisms officiels pour les scénarios rares lorsque disponibles

Ne pas inventer une nouvelle infrastructure de test si Stake fournit déjà le mécanisme nécessaire.

---

# Documentation

Toute nouvelle abstraction partagée importante doit expliquer :

- pourquoi elle existe
- quelle responsabilité elle possède
- ce qu'elle ne fait PAS
- pourquoi Stake ne couvrait pas déjà le besoin

Une décision d'architecture significative doit être documentée lorsque cela apporte une valeur réelle.

Ne pas créer de documentation bureaucratique pour une décision triviale.

---

# Workflow obligatoire

Avant de coder :

1. comprendre la demande
2. lire les docs pertinentes
3. inspecter le code existant
4. vérifier ce que Stake fournit déjà
5. identifier frontend / Math / les deux
6. proposer la solution minimale cohérente
7. implémenter
8. tester
9. vérifier `git diff`
10. signaler les éventuelles divergences Stake

---

# Nouvelle fonctionnalité

Pour toute fonctionnalité importante, vérifier :

- Stake fournit-il déjà cette primitive ?
- appartient-elle au Math ou au frontend ?
- le frontend recalcule-t-il quelque chose qu'il ne devrait pas ?
- la solution respecte-t-elle le contrat bookEvent ?
- fonctionne-t-elle avec Storybook ?
- est-elle responsive ?
- affecte-t-elle les performances ?
- introduit-elle une nouvelle dépendance ?
- introduit-elle une abstraction réellement nécessaire ?
- peut-elle être réutilisée sans couplage artificiel ?

---

# Nouvelle slot

Avant de créer une nouvelle slot :

1. définir son gameplay et son contrat Math
2. examiner les samples/templates Stake disponibles
3. choisir le sample frontend le plus proche
4. choisir le sample/template Math le plus proche
5. créer l'app et le jeu Math à partir de ces bases
6. conserver les packages communs dans `packages/`
7. ne copier dans le jeu que ce qui est spécifique au jeu
8. intégrer les assets runtime
9. implémenter et tester les bookEvents dans Storybook
10. générer séparément frontend build et Math publish files

Ne jamais créer automatiquement un nouveau moteur Gogold pour accompagner une nouvelle slot.

---

# Si plusieurs solutions existent

Choisir celle qui :

1. réutilise le plus proprement Stake
2. crée le moins de code propriétaire inutile
3. réduit la complexité
4. reste facile à tester
5. reste performante
6. reste facilement remplaçable ou évolutive

---

# Si la demande est mauvaise

Ne pas l'exécuter silencieusement.

Expliquer précisément :

- le problème
- le risque
- la solution préférable

Puis utiliser la solution la plus cohérente avec le projet.

---

# Principe final

Gogold ne construit pas un nouveau moteur de slot au-dessus de Stake.

Gogold construit une chaîne de production efficace autour de Stake.

Le code spécifique à un jeu doit rester spécifique au jeu.

Le code partagé doit être partagé uniquement lorsqu'une vraie répétition le justifie.

Stake first.