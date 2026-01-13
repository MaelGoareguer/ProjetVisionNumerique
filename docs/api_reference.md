# Référence API

## Modules Principaux

### `vision_numerique.main`

Point d'entrée de l'application.

#### `main() -> None`

Lance l'application principale. Charge la configuration, initialise le logging et crée la fenêtre principale.

---

### `vision_numerique.processing.base`

Classe abstraite pour les processeurs vidéo.

#### `VideoProcessor`

Classe de base pour tous les processeurs vidéo.

**Méthodes** :

- `__init__(name: str | None = None, config: dict | None = None, **kwargs: Any)`
  - Initialise le processeur avec un nom et une configuration
  
- `process_frame(frame: np.ndarray) -> np.ndarray`
  - Traite une frame vidéo et retourne la frame annotée
  - **À implémenter** par les sous-classes
  
- `close() -> None`
  - Libère les ressources du processeur

---

### `vision_numerique.processing.hand_mediapipe`

Implémentation MediaPipe pour la détection de gestes.

#### `HandMediaPipe(VideoProcessor)`

Processeur utilisant MediaPipe Hands pour la détection et la reconnaissance de gestes.

**Paramètres de configuration** :
- `max_num_hands` (int, default=2) : Nombre maximum de mains à détecter
- `min_detection_confidence` (float, default=0.5) : Confiance minimale pour la détection
- `min_tracking_confidence` (float, default=0.5) : Confiance minimale pour le suivi
- `static_image_mode` (bool, default=False) : Mode image statique
- `draw_landmarks` (bool, default=True) : Dessiner les landmarks
- `draw_connections` (bool, default=True) : Dessiner les connexions

**Méthodes** :

- `process_frame(frame: np.ndarray) -> np.ndarray`
  - Détecte les mains, reconnaît les gestes et exécute les actions
  
- `_recognize_gesture(landmarks, is_right_hand: bool = True) -> str | None`
  - Reconnaît un geste à partir des landmarks
  - Retourne : `"TOGGLE_PLAY_PAUSE"`, `"FULLSCREEN"`, `"AVANCER"`, `"RECULER"`, `"VOLUME_UP"`, `"VOLUME_DOWN"`, ou `None`
  
- `close() -> None`
  - Ferme la session MediaPipe

**Attributs** :
- `metrics_callback` : Callback pour les métriques
- `main_window` : Référence à la fenêtre principale

---

### `vision_numerique.video.camera`

Gestion de la capture vidéo depuis la webcam.

#### `Camera`

Classe pour la capture vidéo depuis une webcam.

**Méthodes** :

- `__init__(index: int = 0, resolution: tuple[int, int] = (1280, 720), fps: int = 30)`
  - Initialise la caméra avec les paramètres spécifiés
  
- `read() -> tuple[bool, np.ndarray]`
  - Lit une frame de la caméra
  - Retourne : `(succès, frame)`
  
- `release() -> None`
  - Libère la ressource de la caméra

**Propriétés** :
- `is_opened() -> bool` : Vérifie si la caméra est ouverte

---

### `vision_numerique.video.video_player`

Gestion de la lecture de fichiers vidéo.

#### `VideoPlayer`

Classe pour la lecture de fichiers vidéo.

**Méthodes** :

- `__init__(file_path: str)`
  - Ouvre un fichier vidéo
  
- `read() -> tuple[bool, np.ndarray]`
  - Lit une frame de la vidéo
  
- `get_position() -> float`
  - Retourne la position actuelle en secondes
  
- `get_duration() -> float`
  - Retourne la durée totale en secondes
  
- `set_position(position: float) -> None`
  - Définit la position de lecture
  
- `play() -> None`
  - Démarre la lecture
  
- `pause() -> None`
  - Met en pause
  
- `advance() -> None`
  - Avance de 5 secondes
  
- `rewind() -> None`
  - Recule de 5 secondes
  
- `get_volume() -> float`
  - Retourne le volume (0.0-1.0)
  
- `adjust_volume(delta: float) -> None`
  - Ajuste le volume
  
- `release() -> None`
  - Libère les ressources

---

### `vision_numerique.utils.metrics`

Système de métriques de performance.

#### `PerformanceMetrics`

Classe pour la collecte et l'analyse des métriques.

**Méthodes** :

- `on_frame_processed(hand_detected: bool, hand_present: bool | None = None) -> None`
  - Appelé à chaque frame traitée
  
- `on_gesture_recognized(predicted_gesture: str) -> None`
  - Appelé quand un geste est reconnu
  
- `declare_gesture(gesture_name: str) -> None`
  - Déclare manuellement un geste (vérité terrain)
  
- `set_hand_present(present: bool) -> None`
  - Définit l'état de vérité terrain pour la présence de main
  
- `clear_hand_present() -> None`
  - Réinitialise l'état de vérité terrain
  
- `get_detection_metrics() -> dict`
  - Retourne les métriques de détection
  
- `get_gesture_metrics() -> dict`
  - Retourne les métriques de reconnaissance
  
- `reset() -> None`
  - Réinitialise toutes les métriques
  
- `export_to_json(file_path: str | Path) -> bool`
  - Exporte les métriques en JSON
  
- `export_to_csv(file_path: str | Path) -> bool`
  - Exporte les métriques en CSV
  
- `export_confusion_matrix_image(file_path: str | Path) -> bool`
  - Génère une image de la matrice de confusion

**Retour de `get_detection_metrics()`** :
```python
{
    "total_frames": int,
    "frames_with_hand": int,
    "frames_detected": int,
    "frames_with_hand_and_detected": int,
    "frames_without_hand": int,
    "frames_detected_without_hand": int,
    "detection_rate": float,  # Pourcentage
    "false_positive_rate": float,  # Pourcentage
    "true_positive_rate": float  # Pourcentage
}
```

**Retour de `get_gesture_metrics()`** :
```python
{
    "total_declarations": int,
    "total_predictions": int,
    "gesture_precision": dict[str, float],  # Précision par geste (%)
    "gesture_counts": dict[str, int],  # Nombre total par geste
    "gesture_correct": dict[str, int],  # Nombre correct par geste
    "confusion_matrix": dict[str, dict[str, int]]  # Matrice de confusion
}
```

---

### `vision_numerique.utils.config`

Gestion de la configuration.

#### `load_settings(files: list[str]) -> dict`

Charge la configuration depuis des fichiers YAML.

**Paramètres** :
- `files` : Liste des chemins de fichiers YAML (ordre de priorité)

**Retour** : Dictionnaire de configuration

#### `save_settings(settings: dict, file_path: str) -> None`

Sauvegarde la configuration dans un fichier YAML.

---

### `vision_numerique.utils.logger`

Configuration du logging.

#### `setup_logging(config: dict) -> None`

Configure le système de logging.

**Paramètres** :
- `config` : Dictionnaire de configuration avec les clés :
  - `level` : Niveau de log (DEBUG, INFO, WARNING, ERROR)
  - `format` : Format des messages
  - `handlers` : Configuration des handlers (console, file)

---

### `vision_numerique.ui.main_window`

Fenêtre principale de l'application.

#### `MainWindow(QMainWindow)`

Fenêtre principale de l'application.

**Méthodes** :

- `__init__(settings: dict)`
  - Initialise la fenêtre avec la configuration
  
- `set_processor(processor_name: str) -> None`
  - Définit le processeur actif ("none", "mediapipe", etc.)
  
- `open_video() -> None`
  - Ouvre un dialogue pour sélectionner une vidéo
  
- `toggle_play_pause() -> None`
  - Bascule entre play et pause
  
- `open_settings() -> None`
  - Ouvre le dialogue de paramètres
  
- `open_metrics() -> None`
  - Ouvre le dialogue de métriques

**Attributs** :
- `settings` : Configuration de l'application
- `metrics` : Instance de `PerformanceMetrics`
- `video_player` : Instance de `VideoPlayer` (si vidéo ouverte)
- `is_playing` : État de lecture (bool)

---

## Types et Structures de Données

### Gestes Reconnus

```python
GESTURE_TOGGLE_PLAY_PAUSE = "TOGGLE_PLAY_PAUSE"
GESTURE_FULLSCREEN = "FULLSCREEN"
GESTURE_AVANCER = "AVANCER"
GESTURE_RECULER = "RECULER"
GESTURE_VOLUME_UP = "VOLUME_UP"
GESTURE_VOLUME_DOWN = "VOLUME_DOWN"
```

### Configuration YAML

Structure typique de `settings.yaml` :

```yaml
camera:
  fps: 30
  index: 0
  resolution: [640, 480]

engines:
  mediapipe:
    max_num_hands: 2
    min_detection_confidence: 0.5
    min_tracking_confidence: 0.5
    static_image_mode: false
    draw_landmarks: true
    draw_connections: true

logging:
  level: INFO
  format: '[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
  handlers:
    console: true
    file: log/app.log
```

---

## Exemples d'Utilisation

### Créer un Processeur Personnalisé

```python
from vision_numerique.processing.base import VideoProcessor
import cv2

class MonProcesseur(VideoProcessor):
    def process_frame(self, frame):
        # Traitement personnalisé
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def close(self):
        # Nettoyage des ressources
        pass
```

### Utiliser le Système de Métriques

```python
from vision_numerique.utils.metrics import PerformanceMetrics

metrics = PerformanceMetrics()

# Pendant le traitement
metrics.on_frame_processed(hand_detected=True, hand_present=True)
metrics.on_gesture_recognized("TOGGLE_PLAY_PAUSE")

# Récupérer les métriques
detection_metrics = metrics.get_detection_metrics()
gesture_metrics = metrics.get_gesture_metrics()

# Exporter
metrics.export_to_json("metrics.json")
metrics.export_confusion_matrix_image("confusion_matrix.png")
```

### Charger la Configuration

```python
from vision_numerique.utils.config import load_settings

settings = load_settings(["settings.yaml"])
camera_config = settings.get("camera", {})
```

