from __future__ import annotations
import cv2
import numpy as np
from myapp.processing.base import VideoProcessor

class HandYolo(VideoProcessor):
    """
    Détection/pose des mains via Ultralytics YOLO.
    kwargs (depuis engines.yolo) : weights, task, conf, iou, classes, imgsz, device, draw_scores, draw_pose
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from myapp.engines.yolo_engine import YoloEngine
        self.draw_scores = bool(self.kwargs.pop("draw_scores", True))
        self.draw_pose = bool(self.kwargs.pop("draw_pose", True))
        self.engine = YoloEngine(**self.kwargs)
        
        # Callback pour les métriques (sera défini par le système de métriques)
        self.metrics_callback = None
        
        # Référence à la fenêtre principale pour accéder à l'état play/pause
        self.main_window = None
        
        # État pour la détection de gestes (debounce)
        self.last_gesture = None
        self.gesture_frame_count = 0
        self.gesture_threshold = 10  # Nombre de frames consécutives pour valider un geste
        
        # État précédent pour détecter les transitions
        self.last_hand_center_detected = None

    def _recognize_gesture_from_position(self, boxes, frame_width, frame_height):
        """
        Reconnaît un geste basique basé sur la position des mains détectées.
        - Main au centre = TOGGLE_PLAY_PAUSE (main plate)
        - Main à droite = AVANCER
        - Main à gauche = RECULER
        """
        if not boxes or len(boxes) == 0:
            return None
        
        # Prendre la première main détectée (ou la plus grande)
        largest_box = None
        largest_area = 0
        
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = xyxy
            area = (x2 - x1) * (y2 - y1)
            if area > largest_area:
                largest_area = area
                largest_box = box
        
        if largest_box is None:
            return None
        
        # Calculer le centre de la boîte
        xyxy = largest_box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Normaliser les positions (0.0 à 1.0)
        norm_x = center_x / frame_width
        norm_y = center_y / frame_height
        
        # Zones de l'écran pour les gestes
        # Gauche: 0.0 - 0.4 (RECULER)
        # Centre: 0.3 - 0.7 (TOGGLE_PLAY_PAUSE)
        # Droite: 0.6 - 1.0 (AVANCER)
        
        if 0.3 <= norm_x <= 0.7:
            # Zone centrale - TOGGLE_PLAY_PAUSE
            # Vérifier aussi si la main est dans la partie supérieure (geste de main plate)
            if norm_y < 0.5:  # Main dans la partie supérieure
                return "TOGGLE_PLAY_PAUSE"
        elif norm_x < 0.4:
            # Zone gauche - RECULER
            return "RECULER"
        elif norm_x > 0.6:
            # Zone droite - AVANCER
            return "AVANCER"
        
        return None

    def process_frame(self, frame):
        """
        Traite une frame : détection des mains avec YOLO.
        Retourne la frame annotée.
        """
        if frame is None:
            return frame
        
        results = self.engine.infer(frame)
        
        # Détecter si une main est présente
        hand_detected = False
        boxes = []
        if results is not None:
            # Vérifier si des boîtes de détection existent
            if hasattr(results, "boxes") and results.boxes is not None and len(results.boxes) > 0:
                hand_detected = True
                boxes = results.boxes
        
        # Calculer les métriques YOLO (confiance moyenne, nombre de mains)
        avg_confidence = None
        num_hands = 0
        if hand_detected and boxes:
            confidences = []
            for box in boxes:
                if hasattr(box, 'conf') and box.conf is not None and len(box.conf) > 0:
                    confidences.append(float(box.conf[0]))
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
            num_hands = len(boxes)
        
        # Notifier le système de métriques
        if self.metrics_callback:
            self.metrics_callback.on_frame_processed(
                hand_detected, 
                confidence=avg_confidence, 
                num_hands=num_hands if hand_detected else None
            )
        
        # Reconnaître un geste basé sur la position
        gesture = None
        if hand_detected and boxes:
            h, w, _ = frame.shape
            gesture = self._recognize_gesture_from_position(boxes, w, h)
            
            # Debounce: valider le geste seulement s'il est détecté plusieurs frames consécutives
            if gesture == self.last_gesture:
                self.gesture_frame_count += 1
            else:
                self.gesture_frame_count = 1
                self.last_gesture = gesture
            
            # Si le geste est stable, le déclarer
            if self.gesture_frame_count >= self.gesture_threshold:
                # Détecter la transition pour TOGGLE_PLAY_PAUSE
                if gesture == "TOGGLE_PLAY_PAUSE":
                    if self.last_hand_center_detected is False:
                        # Transition détectée : main au centre vient d'apparaître
                        if self.main_window:
                            self.main_window.toggle_play_pause()
                        if self.metrics_callback:
                            self.metrics_callback.on_gesture_recognized(gesture)
                        self.log.debug("Geste TOGGLE_PLAY_PAUSE détecté")
                    self.last_hand_center_detected = True
                else:
                    self.last_hand_center_detected = False
                    
                    # Pour AVANCER et RECULER, déclarer directement
                    if gesture in ("AVANCER", "RECULER"):
                        if self.main_window and self.main_window.video_player:
                            if gesture == "AVANCER":
                                self.main_window.video_player.advance()
                            elif gesture == "RECULER":
                                self.main_window.video_player.rewind()
                        if self.metrics_callback:
                            self.metrics_callback.on_gesture_recognized(gesture)
                        self.log.debug(f"Geste {gesture} détecté")
            else:
                # Geste pas encore stable, ne pas déclarer
                pass
        else:
            # Pas de main détectée, réinitialiser
            self.last_hand_center_detected = False
            self.gesture_frame_count = 0
            self.last_gesture = None
        
        # Dessiner les résultats
        annotated_frame = self.engine.draw(frame, results, draw_scores=self.draw_scores, draw_pose=self.draw_pose)
        
        # Afficher l'état de détection et le geste sur la frame
        h, w, _ = annotated_frame.shape
        if hand_detected:
            cv2.putText(
                annotated_frame,
                "MAIN DETECTEE",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )
            
            # Afficher le geste détecté
            if gesture and self.gesture_frame_count >= self.gesture_threshold:
                gesture_display = gesture
                if gesture == "TOGGLE_PLAY_PAUSE":
                    # Afficher l'état actuel
                    if self.main_window and self.main_window.is_playing:
                        gesture_display = "PLAY"
                    else:
                        gesture_display = "PAUSE"
                
                cv2.putText(
                    annotated_frame,
                    f"Geste: {gesture_display}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )
        
        return annotated_frame

    def close(self):
        if self.engine:
            self.engine.close()
