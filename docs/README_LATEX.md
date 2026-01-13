# Compilation du Rapport LaTeX

Ce document contient les instructions pour compiler le rapport de projet en format LaTeX.

## Prérequis

Pour compiler le document LaTeX, vous devez avoir installé :

1. **LaTeX Distribution** :
   - **Windows** : MiKTeX ou TeX Live
   - **Linux** : `sudo apt-get install texlive-full` (ou équivalent)
   - **macOS** : MacTeX

2. **Éditeur LaTeX** (optionnel mais recommandé) :
   - TeXstudio
   - Overleaf (en ligne)
   - VS Code avec extension LaTeX Workshop

## Compilation

### Méthode 1 : Ligne de commande

Depuis le dossier `docs/` :

```bash
pdflatex rapport_projet.tex
pdflatex rapport_projet.tex  # Deux fois pour les références croisées
```

**⚠️ IMPORTANT** : LaTeX doit être compilé **deux fois** pour que la table des matières soit générée correctement. La première compilation crée le fichier `.toc` (table of contents), et la deuxième compilation l'utilise pour afficher la table des matières dans le PDF.

Ou avec BibTeX si vous ajoutez des références :

```bash
pdflatex rapport_projet.tex
bibtex rapport_projet
pdflatex rapport_projet.tex
pdflatex rapport_projet.tex
```

### Méthode 2 : Éditeur LaTeX

Ouvrez `rapport_projet.tex` dans votre éditeur LaTeX préféré (TeXstudio, TeXworks, etc.) et utilisez le bouton de compilation. La plupart des éditeurs compilent automatiquement deux fois si nécessaire.

### Méthode 3 : Overleaf (en ligne)

1. Créez un compte sur [Overleaf](https://www.overleaf.com)
2. Créez un nouveau projet
3. Copiez le contenu de `rapport_projet.tex`
4. Compilez en ligne

## Images

Le document fait référence à plusieurs images :

- `../images/gestes_lecture_navigation.png` - Gestes de lecture et navigation
- `../images/gestes_volume_fullscreen.png` - Gestes de volume et plein écran
- `../confusion_matrix_20251204_202545.png` - Matrice de confusion (existe déjà)

**Note** : Si les images des gestes n'existent pas encore, vous pouvez :
1. Les créer et les placer dans le dossier `images/` à la racine du projet
2. Ou commenter temporairement les lignes `\includegraphics` correspondantes

## Personnalisation

Vous pouvez modifier :
- Les informations des auteurs dans le préambule
- Les couleurs des hyperliens
- Le style des titres
- Les marges de la page

## Résolution des problèmes

### Erreur "File not found" pour les images
- Vérifiez que les chemins des images sont corrects
- Créez un dossier `images/` à la racine si nécessaire

### Erreur de compilation avec les packages
- Installez les packages manquants via votre gestionnaire de paquets LaTeX
- Sur MiKTeX : les packages sont installés automatiquement à la première compilation

### Problèmes d'encodage
- Assurez-vous que le fichier est en UTF-8
- Vérifiez que `\usepackage[utf8]{inputenc}` est présent

