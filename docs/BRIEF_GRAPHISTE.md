# Brief graphiste — assets Gogold

Ce document explique **exactement quoi produire, à quelle taille et dans quel format** pour qu'un asset puisse être intégré sans être refait.

Le principe à retenir :

**Le graphiste produit grand et propre. L'intégration se charge ensuite de réduire, compresser et regrouper les images pour le jeu.**

---

## 1. Ce que tu dois livrer

### Symbole fixe

Exemple : plante, champignon, Wild.

→ **PNG 32 bits avec transparence**

Le fond autour du symbole doit être réellement transparent.

### Animation image par image

Exemple : Wild qui s'ouvre, symbole qui explose.

→ une suite de **PNG transparents**

Exemple :

`wildWin_000.png`
`wildWin_001.png`
`wildWin_002.png`
`wildWin_003.png`

### Background

Si toute l'image est opaque :

→ **PNG ou JPG qualité maximale**

### Icône vectorielle

Uniquement si l'élément a réellement été dessiné en vectoriel :

→ **SVG**

### Animation complexe

Pour un personnage articulé avec plusieurs parties réutilisées :

→ **projet Spine + export**

---

## 2. Taille des symboles — règle simple

C'est la règle la plus importante.

Une slot est construite autour d'une **taille de cellule**.

Par exemple, l'intégration peut décider qu'une case de la grille correspond à :

**200 × 200 px à l'affichage de référence.**

Dans ce cas :

| Étape                       |        Taille recommandée |
| --------------------------- | ------------------------: |
| Taille visible dans le jeu  |                 200 × 200 |
| PNG livré                   |         environ 400 × 400 |
| Fichier de travail / master | environ 800 × 800 ou plus |

Donc :

**affichage ×2 = export PNG**

**affichage ×4 minimum = fichier de travail**

Exemple :

```text
Cellule du jeu : 200 × 200

Master artiste :
800 × 800 minimum

Export livré :
400 × 400 PNG transparent
```

L'intégration pourra ensuite réduire le 400 × 400 vers la taille réellement nécessaire.

### Important

**Ne choisis pas toi-même une taille arbitraire pour les symboles.**

Au début du projet, l'intégration doit fournir une information très simple :

> Taille de référence d'une cellule = XXX × XXX px.

À partir de là, tous les exports sont faciles à calculer.

Si cette taille n'a pas encore été donnée, **demande-la avant de produire tous les exports définitifs**.

---

## 3. Tous les symboles doivent partager le même canvas

Si nous décidons que les symboles sont livrés en :

**512 × 512 px**

alors :

* Low 1 = 512 × 512
* Low 2 = 512 × 512
* Low 3 = 512 × 512
* High 1 = 512 × 512
* High 2 = 512 × 512
* Wild = 512 × 512
* Scatter = 512 × 512

Même si certains dessins sont naturellement plus petits.

Le **canvas reste identique**.

Exemple :

```text
lowLeaf.png       512 × 512
lowFlower.png     512 × 512
highPlant.png     512 × 512
highMushroom.png  512 × 512
wild.png          512 × 512
```

### Ce qui change

Le dessin à l'intérieur du canvas peut être plus ou moins large ou haut.

### Ce qui ne change jamais

La taille du canvas.

---

## 4. Exemple visuel

Imagine un canvas transparent de :

**512 × 512 px**

Le symbole occupe environ le centre :

```text
┌──────────────────────────┐
│                          │
│      marge transparente  │
│                          │
│        █████████         │
│      █████████████       │
│      ███ SYMBOLE █       │
│      █████████████       │
│        █████████         │
│                          │
│      marge transparente  │
│                          │
└──────────────────────────┘
        512 × 512
```

Ne recadre PAS le fichier au bord du dessin.

La marge transparente est normale.

Elle sera supprimée automatiquement au moment du packing si nécessaire.

---

## 5. Taille visuelle des symboles

Tous les PNG peuvent être en 512 × 512 sans que tous les dessins aient exactement la même taille.

Il faut surtout conserver une **cohérence visuelle**.

Par exemple :

```text
Low :
dessin relativement simple et légèrement plus petit

High :
dessin plus imposant

Wild :
peut avoir une présence visuelle légèrement supérieure
```

Mais évite :

```text
Low = minuscule au milieu du canvas

High = touche les quatre bords
```

Les symboles doivent sembler appartenir au même jeu.

L'intégration pourra ajuster légèrement leur scale ensuite.

---

## 6. Animations — règle absolue

Toutes les frames d'une animation doivent avoir :

* exactement la même largeur ;
* exactement la même hauteur ;
* exactement la même origine ;
* exactement le même centrage général.

Exemple correct :

```text
wildWin_000.png → 512 × 512
wildWin_001.png → 512 × 512
wildWin_002.png → 512 × 512
wildWin_003.png → 512 × 512
wildWin_004.png → 512 × 512
```

Le personnage peut bouger à l'intérieur.

Exemple :

```text
FRAME 000          FRAME 001          FRAME 002

┌─────────┐        ┌─────────┐        ┌─────────┐
│   🌱    │        │   🌿    │        │  🌺     │
│         │        │         │        │         │
└─────────┘        └─────────┘        └─────────┘

512 × 512          512 × 512          512 × 512
```

### À ne surtout pas faire

```text
frame 000 = 512 × 512
frame 001 = 487 × 502
frame 002 = 530 × 490
```

Même si Photoshop ou After Effects semble jouer correctement l'animation, elle risque de **sauter dans le jeu**.

---

## 7. Ne jamais recadrer automatiquement une animation

Exemple :

La plante ouvre énormément la bouche à la frame 8.

Le canvas doit être assez grand dès la frame 0 pour contenir cette ouverture.

Donc avant de commencer l'animation :

**prévois le mouvement maximal.**

Le dessin bouge dans le canvas.

**Le canvas ne bouge jamais.**

---

## 8. Résolution maximale

Aucune image exportée ne doit dépasser :

**2048 × 2048 px**

Si un asset nécessite réellement davantage :

**prévenir l'intégration avant de le découper.**

Ne découpe pas arbitrairement une illustration en plusieurs fichiers.

---

## 9. Backgrounds

Un background fonctionne différemment d'un symbole.

Il doit être produit en haute résolution en conservant le bon **ratio d'écran**.

Exemple desktop :

**16:9**

Il n'est cependant généralement pas nécessaire de livrer une image gigantesque.

La version destinée à l'intégration ne doit pas dépasser environ :

**2048 px sur son plus grand côté**, sauf demande spécifique.

Le fichier master peut être plus grand.

Exemple :

```text
Master :
3840 × 2160

Export intégration :
2048 × 1152
```

---

## 10. UI

Pour :

* Spin ;
* Auto Spin ;
* Turbo ;
* Menu ;
* Sound ;
* Bet ;
* boutons + / − ;
* panneaux ;
* petites icônes ;

produire soit :

### Vectoriel

SVG si le graphisme est réellement vectoriel.

### Raster

PNG transparent haute résolution.

Dans ce cas :

**environ 2× la taille prévue à l'écran.**

Exemple :

bouton affiché environ 100 × 100

→ export autour de **200 × 200**

---

## 11. FX

Les effets comme :

* explosion ;
* glow ;
* fumée ;
* particules ;
* éclaboussures ;
* énergie magique ;

peuvent être livrés sous forme de PNG ou séquences PNG.

Même règle que les animations :

**toutes les frames d'une même animation ont exactement le même canvas.**

---

## 12. Ce qu'il ne faut PAS livrer

Ne livre pas de WebP.

Ne compresse pas toi-même les images finales.

Nous voulons récupérer une source propre.

À éviter dans les exports :

```text
.webp
.psd
.psb
.aep
.blend
.kra
.xcf

.wav
.aiff
.flac

Thumbs.db
.bak
```

Les fichiers de travail doivent être conservés, mais ils ne sont pas utilisés directement par le jeu.

---

## 13. Pourquoi pas de WebP ?

Le graphiste livre :

**PNG propre → intégration → compression optimisée → format utilisé par le jeu**

et non :

**PNG → WebP compressé par le graphiste → nouvelle compression**

Sinon une partie de la qualité est perdue avant même l'intégration.

---

## 14. Comment nommer les fichiers

Utiliser du **camelCase**.

Correct :

```text
highMushroom.png
wildPlant.png
boardFrame.png
boardFrameActive.png
backgroundFreeSpins.png
```

Incorrect :

```text
High Mushroom.png
wild_final.png
wildV2.png
wildOK.png
nouveauWild.png
```

Pas :

* d'espace ;
* d'accent ;
* de `final` ;
* de `v2` ;
* de `test` ;
* de `OK` ;
* de `copie`.

Git gère l'historique des versions.

---

## 15. Nom des animations

Toujours :

**nom + underscore + numéro sur 3 chiffres**

À partir de 000.

Exemple :

```text
wildWin_000.png
wildWin_001.png
wildWin_002.png
wildWin_003.png
...
wildWin_012.png
```

Pas :

```text
wildWin1.png
wildWin2.png
wildWin10.png
```

---

## 16. États d'un même asset

Toujours garder le même nom principal.

Exemple :

```text
boardFrame.png
boardFrameActive.png

background.png
backgroundFreeSpins.png

barrel.png
barrelFull.png

wild.png
wildActive.png
```

Cela permet de retrouver immédiatement tous les états du même élément.

---

## 17. Organisation des fichiers source

Déposer le travail dans :

```text
source-assets/<nomDuJeu>/

├── symbols/
├── backgrounds/
├── ui/
├── fx/
├── animations/
└── audio/
```

Les **masters** peuvent être archivés avec les sources de production.

Les **exports PNG/SVG** destinés au pipeline sont ensuite récupérés par l'intégration.

Important : les masters `.psd`, `.aep`, `.blend`, etc. ne doivent jamais finir dans le dossier runtime/build réellement envoyé avec le jeu.

---

## 18. Poids du jeu

Objectif Gogold :

```text
idéal : 15–25 MB

maximum visé : 35 MB
```

Le graphiste n'a pas à compresser agressivement ses fichiers pour respecter ce poids.

C'est l'intégration qui optimise.

En revanche, avant de produire quelque chose de très lourd, par exemple :

* animation de 80 frames ;
* énorme background animé ;
* personnage occupant tout l'écran ;
* plusieurs animations 2K ;

demande validation.

---

## 19. Exemple complet pour un symbole

L'intégration annonce :

```text
Cellule de référence :
200 × 200 px
```

Le graphiste fait :

```text
Master :
800 × 800 ou davantage

Export :
400 × 400 PNG transparent
```

Tous les symboles utilisent :

```text
400 × 400
```

Exemple :

```text
lowBud.png          400 × 400
lowFlower.png       400 × 400
lowSpore.png        400 × 400
lowLeaf.png         400 × 400

highPlant.png       400 × 400
highMushroom.png    400 × 400
highFlower.png      400 × 400
highMonster.png     400 × 400

wild.png            400 × 400
```

Puis une animation du Wild :

```text
wildWin_000.png     400 × 400
wildWin_001.png     400 × 400
wildWin_002.png     400 × 400
...
wildWin_015.png     400 × 400
```

C'est exactement ce que nous voulons recevoir.

---

## 20. La règle à retenir

Pour un symbole :

**1. On te donne la taille de cellule.**

**2. Tu travailles au minimum à 4× cette taille.**

**3. Tu exportes environ à 2× cette taille.**

**4. Tous les symboles utilisent le même canvas.**

**5. Toutes les frames d'une animation utilisent exactement le même canvas.**

**6. Tu livres du PNG transparent propre.**

**7. Tu ne recadres jamais frame par frame.**

**8. L'intégration s'occupe du trimming, TexturePacker, WebP et de l'optimisation finale.**

---

## Checklist ultra courte

Avant d'envoyer un symbole ou une animation :

* [ ] PNG avec vraie transparence
* [ ] Bonne taille de canvas
* [ ] Même canvas que les autres symboles de la famille
* [ ] Même canvas sur toutes les frames
* [ ] Animation numérotée `_000`, `_001`, `_002`…
* [ ] Nom en camelCase
* [ ] Aucun `final`, `v2`, `test`, `ok`
* [ ] Export inférieur ou égal à 2048 px par côté
* [ ] Pas de WebP
* [ ] Master conservé
* [ ] En cas de doute sur la taille : demander la taille de cellule avant de produire
