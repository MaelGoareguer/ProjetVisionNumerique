# Architecture du Système

## Vue d'ensemble

Le système **Vision Numérique** suit une architecture modulaire en couches, permettant une séparation claire des responsabilités et facilitant l'extensibilité.

## Architecture en Couches

```
┌─────────────────────────────────────────────────┐
│           Interface Utilisateur (UI)            │
│  (MainWindow, VideoWindow, Dialogs)             │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         Gestion Vidéo (Video Layer)             │
│  (Camera, VideoPlayer)                          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Traitement Vidéo (Processing Layer)         │
│  (VideoProcessor, HandMediaPipe)                 │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         Utilitaires (Utils Layer)                │
│  (Metrics, Config, Logger)                       │
└──────────────────────────────────────────────────┘
```

## Composants Principaux

### 1. Interface Utilisateur (`ui/`)

#### MainWindow
- Fenêtre principale de l'application
- Gestion de l'état global (play/pause, processeur actif)
- Coordination entre les différents composants
- Gestion des menus et raccourcis clavier

#### VideoWindow
- Fenêtre dédiée à l'affichage vidéo
- Support du mode plein écran
- Gestion des événements de la fenêtre vidéo

#### Dialogs
- **SettingsDialog** : Configuration des paramètres
- **MetricsDialog** : Affichage des métriques de performance
- **LogViewerDialog** : Consultation des logs
- **HelpDialog** : Aide utilisateur

### 2. Gestion Vidéo (`video/`)

#### Camera
- Capture du flux vidéo depuis la webcam
- Configuration de la résolution et FPS
- Gestion des propriétés de la caméra (zoom, autofocus)

#### VideoPlayer
- Lecture de fichiers vidéo
- Contrôle de la lecture (play/pause, avancer/reculer)
- Gestion du volume
- Synchronisation avec l'affichage

### 3. Traitement Vidéo (`processing/`)

#### VideoProcessor (classe abstraite)
- Interface de base pour tous les processeurs
- Définit le contrat `process_frame(frame) -> frame`
- Gestion de la configuration et du logging

#### HandMediaPipe
- Implémentation concrète utilisant MediaPipe Hands
- Détection des landmarks de la main
- Reconnaissance des gestes basée sur la géométrie
- Exécution des actions correspondantes

### 4. Utilitaires (`utils/`)

#### Metrics
- Collecte des métriques de performance
- Calcul des taux de détection et de reconnaissance
- Génération de matrices de confusion
- Export des résultats (JSON, CSV, PNG)

#### Config
- Chargement et sauvegarde de la configuration YAML
- Gestion des paramètres par défaut
- Validation des configurations

#### Logger
- Configuration centralisée du logging
- Support de plusieurs handlers (console, fichier)
- Formatage des messages

## Flux de Données

### Flux Principal

```
1. Capture (Camera/VideoPlayer)
   ↓
2. Traitement (VideoProcessor)
   ↓
3. Affichage (UI)
   ↓
4. Métriques (Metrics)
```

### Flux de Reconnaissance de Gestes

```
Frame vidéo (BGR)
    ↓
Conversion BGR → RGB
    ↓
MediaPipe Hands Processing
    ↓
Landmarks (21 points par main)
    ↓
Analyse géométrique
    ↓
Classification du geste
    ↓
Exécution de l'action
    ↓
Enregistrement métriques
```

## Patterns de Conception

### 1. Strategy Pattern
Les différents processeurs vidéo (HandMediaPipe, etc.) implémentent l'interface `VideoProcessor`, permettant de changer dynamiquement le mode de traitement.

### 2. Observer Pattern
Le système de métriques observe les événements de traitement et de reconnaissance pour collecter les données.

### 3. Factory Pattern
Le chargement des processeurs se fait via un système de plugins, permettant l'ajout de nouveaux processeurs sans modifier le code principal.

## Extensibilité

### Ajout d'un Nouveau Processeur

1. Créer une classe héritant de `VideoProcessor`
2. Implémenter `process_frame(frame) -> frame`
3. Ajouter la configuration dans `settings.yaml`
4. Enregistrer dans le système de plugins

### Ajout d'un Nouveau Geste

1. Modifier `_recognize_gesture()` dans `HandMediaPipe`
2. Ajouter la logique de détection géométrique
3. Implémenter l'action correspondante
4. Mettre à jour la documentation

## Performance

### Optimisations Implémentées

- **Traitement alterné** : Une frame sur deux est traitée par MediaPipe
- **Cache des résultats** : Réutilisation des résultats de détection
- **Modèle léger** : Utilisation de MediaPipe Hands avec `complexity=0`
- **Threading** : Séparation des threads pour l'UI et le traitement (à implémenter)

### Goulots d'Étranglement

- Traitement MediaPipe (CPU-intensive)
- Conversion de formats d'image
- Affichage en temps réel

## Sécurité et Robustesse

- Gestion des erreurs à tous les niveaux
- Validation des entrées utilisateur
- Gestion gracieuse des erreurs de caméra
- Logging détaillé pour le débogage

