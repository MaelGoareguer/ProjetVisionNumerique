from __future__ import annotations
import cv2
import numpy as np
from myapp.processing.base import VideoProcessor

class HandMediaPipe(VideoProcessor):
    """
    Détection et reconnaissance de gestes via MediaPipe.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            import mediapipe as mp
        except ImportError as e:
            raise ImportError(
                "Le processeur MediaPipe nécessite 'mediapipe'. Installe-le: pip install mediapipe"
            ) from e
        
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Configuration MediaPipe
        max_num_hands = int(self.kwargs.pop("max_num_hands", 2))
        min_detection_confidence = float(self.kwargs.pop("min_detection_confidence", 0.5))
        min_tracking_confidence = float(self.kwargs.pop("min_tracking_confidence", 0.5))
        static_image_mode = bool(self.kwargs.pop("static_image_mode", False))
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=0  # 0 = léger, 1 = complet (plus rapide avec 0)
        )
        
        # Options d'affichage
        self.draw_landmarks = bool(self.kwargs.pop("draw_landmarks", True))
        self.draw_connections = bool(self.kwargs.pop("draw_connections", True))
        
        # Callback pour les métriques (sera défini par le système de métriques)
        self.metrics_callback = None
        
        # Référence à la fenêtre principale pour accéder à l'état play/pause
        self.main_window = None
        
        # Cache pour la dernière détection (pour améliorer les performances)
        self.last_results = None
        self.frame_counter = 0
        
        # État précédent pour détecter les transitions (debounce)
        self.last_hand_plate_detected = False
        
    def process_frame(self, frame):
        """
        Traite une frame : détection des mains et reconnaissance de gestes.
        Retourne la frame annotée.
        """
        if frame is None:
            return frame
        
        # Traiter seulement une frame sur deux pour améliorer les performances
        # (MediaPipe utilise déjà le tracking entre les frames)
        self.frame_counter += 1
        process_this_frame = (self.frame_counter % 2 == 0) or (self.last_results is None)
        
        if process_this_frame:
            # Conversion BGR vers RGB pour MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(frame_rgb)
            self.last_results = results
        else:
            # Réutiliser les résultats précédents
            results = self.last_results
        
        # Détection de main
        hand_detected = results.multi_hand_landmarks is not None and len(results.multi_hand_landmarks) > 0
        
        # Notifier le système de métriques
        if self.metrics_callback:
            self.metrics_callback.on_frame_processed(hand_detected)
        
        # Si aucune main n'est détectée, réinitialiser l'état de la main plate
        if not results.multi_hand_landmarks:
            self.last_hand_plate_detected = False
        
        # Dessiner les résultats
        if results.multi_hand_landmarks:
            handedness_list = results.multi_handedness or []
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                handedness = handedness_list[idx] if idx < len(handedness_list) else None
                if self.draw_landmarks:
                    if self.draw_connections:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style()
                        )
                    else:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            None,
                            self.mp_drawing_styles.get_default_hand_landmarks_style()
                        )
                
                # Reconnaître le geste
                is_right_hand = True
                if handedness and len(handedness.classification) > 0:
                    is_right_hand = handedness.classification[0].label == "Right"
                gesture = self._recognize_gesture(hand_landmarks, is_right_hand)
                
                # Gérer les gestes de contrôle vidéo
                current_hand_plate = (gesture == "TOGGLE_PLAY_PAUSE")
                
                # Détecter la transition : passage de "pas de main plate" à "main plate"
                if current_hand_plate and not self.last_hand_plate_detected:
                    # Transition détectée : main plate vient d'apparaître
                    if self.main_window:
                        self.main_window.toggle_play_pause()
                    self.log.debug("Transition main plate détectée, toggle play/pause")
                
                # Gérer les gestes de navigation (avancer/reculer) - seulement si ce n'est pas une main plate
                if gesture == "AVANCER" and not current_hand_plate:
                    if self.main_window and self.main_window.video_player:
                        self.main_window.video_player.advance()
                        self.log.debug("Geste AVANCER détecté")
                elif gesture == "RECULER" and not current_hand_plate:
                    if self.main_window and self.main_window.video_player:
                        self.main_window.video_player.rewind()
                        self.log.debug("Geste RECULER détecté")
                
                # Mettre à jour l'état précédent
                self.last_hand_plate_detected = current_hand_plate
                
                # Afficher le geste
                if gesture == "TOGGLE_PLAY_PAUSE":
                    # Afficher l'état actuel
                    if self.main_window and self.main_window.is_playing:
                        gesture_display = "PLAY"
                    else:
                        gesture_display = "PAUSE"
                else:
                    gesture_display = gesture
                
                # Afficher le geste
                if gesture_display:
                    h, w, _ = frame.shape
                    # Trouver la position de la main (poignet)
                    wrist = hand_landmarks.landmark[0]
                    x = int(wrist.x * w)
                    y = int(wrist.y * h) - 20
                    cv2.putText(
                        frame,
                        gesture_display,
                        (x, max(20, y)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA
                    )
                    
                    # Notifier le système de métriques pour la reconnaissance de geste
                    if self.metrics_callback and gesture:  # Utiliser le geste original pour les métriques
                        self.metrics_callback.on_gesture_recognized(gesture)
        
        return frame
    
    def _recognize_gesture(self, landmarks, is_right_hand: bool = True):
        """
        Reconnaît un geste pour le contrôle vidéo :
        - Doigts vers la droite = AVANCER
        - Doigts vers la gauche = RECULER
        - Main plate (tous doigts tendus) = TOGGLE_PLAY_PAUSE (toggle selon l'état actuel)
        """
        # Points clés de la main
        wrist = landmarks.landmark[0]
        thumb_tip = landmarks.landmark[4]
        thumb_mcp = landmarks.landmark[2]
        index_tip = landmarks.landmark[8]
        index_pip = landmarks.landmark[6]
        index_mcp = landmarks.landmark[5]
        middle_tip = landmarks.landmark[12]
        middle_pip = landmarks.landmark[10]
        ring_tip = landmarks.landmark[16]
        ring_pip = landmarks.landmark[14]
        pinky_tip = landmarks.landmark[20]
        pinky_pip = landmarks.landmark[18]
        
        # Vérifier si les doigts sont tendus (tip au-dessus de pip)
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y
        
        # Pour le pouce, vérifier s'il est à droite (main droite) ou à gauche (main gauche) du MCP
        if is_right_hand:
            thumb_up = thumb_tip.x > thumb_mcp.x
        else:
            thumb_up = thumb_tip.x < thumb_mcp.x
        
        fingers_up = [index_up, middle_up, ring_up, pinky_up]  # Exclure le pouce pour la main plate
        count_fingers = sum(fingers_up)
        
        # MAIN PLATE = 4 doigts tendus (sans le pouce) = TOGGLE PLAY/PAUSE
        # Vérifier en premier pour éviter les faux positifs avec les directions
        # On accepte 4 doigts sur 4 (sans pouce) car le pouce peut être difficile à détecter
        if count_fingers >= 4:
            return "TOGGLE_PLAY_PAUSE"
        
        # Pour détecter la direction, on regarde la position de l'index par rapport au poignet
        # Mais seulement si ce n'est PAS une main plate (count_fingers < 4)
        # INVERSE : La caméra est inversée par rapport à nous
        # Si l'index est pointé vers la droite sur l'écran (x de l'index > x du poignet) = RECULER (pour nous c'est gauche)
        # Si l'index est pointé vers la gauche sur l'écran (x de l'index < x du poignet) = AVANCER (pour nous c'est droite)
        if index_up and count_fingers < 4:  # Index tendu mais pas tous les doigts
            # Calculer la direction basée sur la position horizontale de l'index
            index_direction = index_tip.x - wrist.x
            
            # Seuil pour éviter les faux positifs
            if abs(index_direction) > 0.15:  # Seuil de 15% de la largeur de l'image
                # INVERSE : La caméra est inversée
                if index_direction > 0:
                    return "RECULER"  # Inversé : droite sur écran = reculer
                else:
                    return "AVANCER"  # Inversé : gauche sur écran = avancer
        
        # Si aucun geste reconnu, retourner None
        return None
    
    def close(self):
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()

