# Règles IA — où elles vivent et comment les maintenir

Ce document s'adresse aux **humains**. Il n'énonce aucune règle : il explique où
les écrire et pourquoi.

Claude Code démarre chaque session sans mémoire. Ce qu'il sait de Gogold vient
uniquement des fichiers ci-dessous, versionnés dans Git.

---

## Les trois niveaux

| Niveau | Fichier | Chargement | Pour quoi |
| --- | --- | --- | --- |
| **Global** | `CLAUDE.md` | à chaque session, en entier | règles utiles à presque toutes les tâches |
| **Domaine** | `.claude/rules/<domaine>.md` | quand un fichier correspondant est ouvert | règles d'un domaine précis |
| **Référence** | `docs/*.md` | jamais automatiquement — lu à la demande | procédures détaillées, décisions, mesures |

Un quatrième niveau existe pour les préférences personnelles :
`CLAUDE.local.md` à la racine, **non versionné** (à ajouter au `.gitignore` si
vous l'utilisez).

---

## Pourquoi ce découpage

`CLAUDE.md` est injecté dans le contexte à **chaque** session. Chaque ligne coûte
des tokens sur toutes les tâches, et la documentation Claude Code observe qu'un
fichier long réduit l'adhérence aux instructions. La cible est **200 lignes**.

Les règles `.claude/rules/` avec un frontmatter `paths:` ne se chargent que
lorsque Claude ouvre un fichier correspondant. Une règle Math ne pèse rien quand
on travaille sur les assets.

> **Ne pas utiliser `@fichier` pour importer les docs dans `CLAUDE.md`.** Les
> imports sont chargés au lancement, exactement comme si le contenu était collé
> dans le fichier. Ce serait le contraire de l'objectif.

---

## Règles actuelles

```text
.claude/rules/
├── frontend.md        apps/**/*.{ts,svelte}, apps/**/package.json
├── math.md            math/**/*.py, math/games/**
├── assets.md          apps/*/static/assets/**, source-assets/**, tooling/assets/**
├── stake-upstream.md  packages/**, math/src/**, apps/lines/**
├── testing-ci.md      .github/workflows/**, tooling/ci/**, math/tests/**, *.stories.svelte
└── debug.md           apps/*/src/dev/**, tooling/debug/**
```

Plusieurs règles peuvent s'appliquer au même fichier : un fichier de
`apps/lines/src/` déclenche `frontend.md` **et** `stake-upstream.md`. C'est
voulu.

---

## Où écrire une nouvelle décision

```text
concerne toutes les tâches       → CLAUDE.md          (rester bref)
concerne un domaine / type       → .claude/rules/<domaine>.md
procédure détaillée, mesures     → docs/
préférence personnelle           → CLAUDE.local.md    (non versionné)
```

C'est la règle qui empêche `CLAUDE.md` de regonfler. Elle est aussi rappelée
dans `CLAUDE.md` pour que Claude sache lui-même où ranger une décision.

---

## Ajouter une règle de domaine

1. créer `.claude/rules/<domaine>.md`
2. ajouter le frontmatter, avec des patterns assez larges pour couvrir le
   domaine mais assez précis pour ne pas se charger partout :

```markdown
---
paths:
  - "chemin/**/*.{ext1,ext2}"
---
```

3. écrire des règles **vérifiables**. Préférer « mesurer avant d'optimiser » à
   « toujours optimiser » : un absolu invérifiable est ignoré ou mal appliqué.
4. renvoyer vers la doc de référence plutôt que la recopier.
5. vérifier que les patterns correspondent à des fichiers réels — une règle qui
   ne matche rien ne se chargera jamais.

Garder chaque règle ciblée. Une règle de 500 lignes rate son objectif.

---

## Vérifier que tout est chargé

Dans une session Claude Code ouverte à la racine du repository :

```text
/context
```

Sous **Memory files**, `CLAUDE.md` doit apparaître. S'il est absent, Claude ne le
voit pas.

Pour vérifier une règle path-scoped : ouvrir un fichier du domaine (par exemple
un `.py` sous `math/`) et confirmer que la règle correspondante se charge.
`/memory` liste et ouvre les fichiers mémoire.

---

## Mémoire automatique

Claude Code peut retenir des observations de lui-même, hors de Git et hors de la
machine des autres. C'est utile pour des astuces locales.

> **L'architecture officielle, le workflow, les contraintes Stake et les
> commandes officielles restent dans Git.** La mémoire automatique n'en est
> jamais la source de vérité : elle n'est ni partagée, ni revue, ni versionnée.

---

## Ce que ces règles ne font pas

`CLAUDE.md` et `.claude/rules/` sont du **contexte**, pas une application
technique : Claude les lit et les suit, sans garantie stricte.

Pour empêcher réellement une action, il faut un hook `PreToolUse`. **Aucun hook
n'existe aujourd'hui** — c'est délibéré. Si une règle mérite un jour un
enforcement technique, ce sera une décision dédiée, pas un effet de bord.
