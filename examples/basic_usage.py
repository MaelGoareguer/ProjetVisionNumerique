"""
Exemple basique d'utilisation de Vision Numérique.

Cet exemple montre comment utiliser les composants principaux
du système de manière programmatique.
"""

from vision_numerique.video.camera import Camera
from vision_numerique.processing.hand_mediapipe import HandMediaPipe
from vision_numerique.utils.metrics import PerformanceMetrics

def exemple_camera():
    """Exemple d'utilisation de la caméra."""
    camera = Camera(index=0, resolution=(640, 480), fps=30)
    
    try:
        for _ in range(100):  # Capturer 100 frames
            success, frame = camera.read()
            if success:
                # Traiter la frame ici
                pass
    finally:
        camera.release()

def exemple_processeur():
    """Exemple d'utilisation d'un processeur."""
    processor = HandMediaPipe(
        max_num_hands=2,
        min_detection_confidence=0.5
    )
    
    # Simuler une frame (en pratique, depuis la caméra)
    import numpy as np
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    processed_frame = processor.process_frame(frame)
    
    processor.close()

def exemple_metriques():
    """Exemple d'utilisation du système de métriques."""
    metrics = PerformanceMetrics()
    
    # Simuler quelques frames
    metrics.on_frame_processed(hand_detected=True, hand_present=True)
    metrics.on_frame_processed(hand_detected=False, hand_present=False)
    metrics.on_gesture_recognized("TOGGLE_PLAY_PAUSE")
    
    # Récupérer les métriques
    detection_metrics = metrics.get_detection_metrics()
    gesture_metrics = metrics.get_gesture_metrics()
    
    print("Métriques de détection:", detection_metrics)
    print("Métriques de gestes:", gesture_metrics)
    
    # Exporter
    metrics.export_to_json("example_metrics.json")

if __name__ == "__main__":
    print("Exemples d'utilisation de Vision Numérique")
    # Décommenter pour tester :
    # exemple_camera()
    # exemple_processeur()
    # exemple_metriques()

