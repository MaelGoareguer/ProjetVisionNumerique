# Vision Numérique - Contrôle Vidéo par Gestes

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/qt-for-python)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-orange.svg)](https://mediapipe.dev/)

## Résumé

**Vision Numérique** est une application de recherche en vision par ordinateur qui exploite la détection de gestes de la main via MediaPipe pour contrôler la lecture vidéo en temps réel. Ce projet combine des techniques avancées de traitement d'images, de reconnaissance de gestes et d'interaction homme-machine (HCI) pour créer une interface de contrôle vidéo intuitive et sans contact.

## Abstract

Cette application de recherche explore l'utilisation de la vision par ordinateur pour le contrôle gestuel de médias vidéo. En s'appuyant sur MediaPipe Hands, nous implémentons un système de reconnaissance de gestes en temps réel capable de détecter et classifier différents mouvements de la main pour contrôler la lecture, la navigation et le volume d'une vidéo. Le système intègre des métriques de performance détaillées pour l'évaluation de la précision de détection et de reconnaissance.

## Fonctionnalités

### Détection et Reconnaissance de Gestes

- **Détection de mains en temps réel** : Utilisation de MediaPipe Hands pour la détection et le suivi de jusqu'à 2 mains simultanément
- **Reconnaissance de 6 gestes distincts** :
  - Main plate serrée → Play/Pause
  - Main plate écartée → Plein écran
  - Index pointé vers la droite → Avancer dans la vidéo
  - Index pointé vers la gauche → Reculer dans la vidéo
  - Index pointé vers le haut → Augmenter le volume
  - Index pointé vers le bas → Diminuer le volume

### Interface Utilisateur

- Interface graphique moderne avec PySide6
- Affichage en temps réel du flux vidéo avec annotations des landmarks
- Fenêtre vidéo séparée avec contrôle plein écran
- Visualisation des métriques de performance
- Système de logs détaillé

### Métriques et Évaluation

- **Métriques de détection** :
  - Taux de détection (detection rate)
  - Taux de vrais positifs (true positive rate)
  - Taux de faux positifs (false positive rate)
  
- **Métriques de reconnaissance** :
  - Précision par geste
  - Matrice de confusion
  - Export des métriques (JSON, CSV, PNG)

- **Système de vérité terrain** : Annotation manuelle pour l'évaluation des performances

## Architecture

Le projet suit une architecture modulaire permettant l'extensibilité et la maintenabilité :

```
vision_numerique/
├── processing/          # Processeurs vidéo (détection, reconnaissance)
│   ├── base.py         # Classe abstraite VideoProcessor
│   └── hand_mediapipe.py  # Implémentation MediaPipe
├── video/              # Gestion des sources vidéo
│   ├── camera.py       # Capture caméra
│   └── video_player.py # Lecteur vidéo
├── ui/                 # Interface utilisateur
│   ├── main_window.py  # Fenêtre principale
│   ├── video_window.py # Fenêtre vidéo
│   └── ...
├── utils/              # Utilitaires
│   ├── metrics.py      # Système de métriques
│   ├── config.py       # Gestion de configuration
│   └── logger.py       # Système de logging
└── engines/            # Moteurs de traitement (extensible)
```

### Flux de Traitement

1. **Capture** : Acquisition du flux vidéo (caméra ou fichier)
2. **Pré-traitement** : Conversion des formats d'image (BGR → RGB pour MediaPipe)
3. **Détection** : MediaPipe Hands détecte les landmarks des mains
4. **Reconnaissance** : Classification des gestes basée sur la géométrie des landmarks
5. **Action** : Exécution des commandes vidéo correspondantes
6. **Métriques** : Enregistrement des performances pour analyse

## Installation

### Prérequis

- Python 3.10 ou supérieur
- Webcam (pour la détection en temps réel)
- Système d'exploitation : Windows, Linux ou macOS

### Installation depuis les sources

1. **Cloner le dépôt** :
```bash
git clone https://github.com/votre-username/ProjetVisionNumerique.git
cd ProjetVisionNumerique
```

2. **Créer un environnement virtuel** :
```bash
# Windows (PowerShell)
py -3.10 -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3.10 -m venv .venv
source .venv/bin/activate
```

3. **Installer le package** :
```bash
pip install -e .
```

Cette commande installera automatiquement toutes les dépendances listées dans `pyproject.toml`.

### Dépendances principales

- **PySide6** (≥6.5) : Framework GUI
- **OpenCV** (≥4.8,<4.10) : Traitement d'images
- **MediaPipe** (≥0.10.0) : Détection de gestes
- **NumPy** (<2) : Calculs numériques
- **Matplotlib** (≥3.7.0) : Visualisation des métriques
- **PyYAML** (≥6.0) : Gestion de configuration

## Utilisation

### Lancement de l'application

```bash
vision-numerique
```

Ou directement depuis Python :

```bash
python -m vision_numerique.main
```

### Guide d'utilisation

1. **Activation de la détection** : Cliquez sur le bouton "MediaPipe" pour activer la détection de gestes
2. **Ouverture d'une vidéo** : Menu "Fichier" → "Ouvrir une vidéo..."
3. **Contrôle par gestes** :
   - Maintenez votre main devant la caméra
   - Effectuez les gestes décrits dans la section Fonctionnalités
   - La vidéo s'ouvrira dans une fenêtre séparée
4. **Consultation des métriques** : Menu "Métriques" → "Voir les métriques..."

### Raccourcis clavier

- **Espace** : Play/Pause
- **→** : Avancer dans la vidéo
- **←** : Reculer dans la vidéo
- **H** : Déclarer une main présente (vérité terrain)
- **N** : Déclarer aucune main (vérité terrain)
- **C** : Réinitialiser la vérité terrain

## Méthodologie

### Algorithme de Reconnaissance de Gestes

Le système de reconnaissance repose sur l'analyse géométrique des landmarks détectés par MediaPipe Hands. Chaque main est représentée par 21 points clés (landmarks) correspondant aux articulations et extrémités des doigts.

#### Classification des Gestes

1. **Main plate** : Détection basée sur le nombre de doigts tendus (≥4 doigts) et la distance normalisée entre les extrémités des doigts
   - **Serrée** : Distance moyenne < 42% de la taille de la main
   - **Écartée** : Distance moyenne ≥ 42% de la taille de la main

2. **Navigation (Avancer/Reculer)** : Analyse de la direction horizontale de l'index par rapport au poignet
   - Seuil minimum : 0.07 (normalisé)
   - Ratio horizontal/vertical > 0.8

3. **Volume** : Analyse de la direction verticale de l'index
   - Seuil minimum : 0.10 (normalisé)
   - Ratio vertical/horizontal > 1.5

#### Optimisations de Performance

- **Traitement alterné** : Traitement d'une frame sur deux pour améliorer les performances (MediaPipe utilise déjà le tracking entre frames)
- **Cache des résultats** : Réutilisation des résultats de détection pour les frames non traitées
- **Complexité du modèle** : Utilisation du modèle léger (complexity=0) pour MediaPipe Hands

### Évaluation des Performances

Le système intègre un module de métriques complet permettant :

- Le calcul de métriques de détection (précision, rappel, F1-score)
- La génération de matrices de confusion pour la classification des gestes
- L'export des résultats pour analyse approfondie

## Structure du Projet

```
ProjetVisionNumerique/
├── README.md                 # Ce fichier
├── pyproject.toml            # Configuration du package
├── settings.yaml             # Configuration par défaut
├── .gitignore                # Fichiers ignorés par Git
├── requirements.txt          # Dépendances (alternative)
│
├── vision_numerique/         # Package principal
│   ├── __init__.py
│   ├── main.py               # Point d'entrée
│   ├── processing/           # Processeurs vidéo
│   ├── video/                # Gestion vidéo
│   ├── ui/                   # Interface utilisateur
│   ├── utils/                # Utilitaires
│   ├── engines/              # Moteurs de traitement
│   └── resources/            # Ressources (modèles, etc.)
│
├── docs/                     # Documentation
│   ├── architecture.md       # Architecture détaillée
│   ├── methodology.md        # Méthodologie de recherche
│   └── api_reference.md      # Référence API
│
├── tests/                    # Tests unitaires et d'intégration
│   └── ...
│
├── examples/                 # Exemples d'utilisation
│   └── ...
│
├── notebooks/                # Notebooks Jupyter pour analyse
│   └── ...
│
├── scripts/                  # Scripts utilitaires
│   └── ...
│
├── data/                     # Données de test
│   └── ...
│
└── videos/                   # Vidéos d'exemple
    └── ...
```

## Résultats et Performance

### Métriques Typiques

Sur un système standard (CPU moderne, webcam 720p) :

- **FPS de traitement** : ~15-30 FPS (selon la complexité de la scène)
- **Latence de détection** : < 100ms
- **Précision de détection** : > 90% (selon les conditions d'éclairage)
- **Précision de reconnaissance** : Variable selon le geste (70-95%)

### Limitations

- Sensibilité aux conditions d'éclairage
- Nécessite une distance optimale main-caméra (30-80 cm)
- Performance dépendante du matériel (CPU/GPU)
- Détection limitée à 2 mains simultanément

### Travaux Futurs

- [ ] Support de plus de gestes complexes
- [ ] Amélioration de la robustesse aux variations d'éclairage
- [ ] Intégration d'un modèle de deep learning pour la classification
- [ ] Support multi-mains avancé (>2 mains)
- [ ] Calibration automatique des seuils de détection
- [ ] Interface de configuration avancée pour les chercheurs

## Références

### Bibliographie

- **MediaPipe Hands** : [Lugaresi et al., 2019] - On-device real-time hand tracking
- **Vision par ordinateur** : Techniques modernes de détection et suivi d'objets
- **Interaction Homme-Machine** : Interfaces gestuelles et contrôle sans contact

### Ressources Techniques

- [Documentation MediaPipe](https://google.github.io/mediapipe/solutions/hands)
- [Documentation PySide6](https://doc.qt.io/qtforpython/)
- [Documentation OpenCV](https://docs.opencv.org/)

## Équipe

- **GOAREGUER Maël**
- **AKKAYA Garip**
- **BAUDART Alexandre**
- **POTIN Léa**

## Remerciements

- Équipe MediaPipe de Google pour l'excellent framework de détection
- Communauté open source pour les outils et bibliothèques utilisés

---

*Ce projet est développé dans un contexte d'étude de recherche en vision par ordinateur et interaction homme-machine.*
