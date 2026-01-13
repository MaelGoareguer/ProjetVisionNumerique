from __future__ import annotations
import cv2
import numpy as np
from vision_numerique.processing.base import VideoProcessor

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
        self.last_volume_gesture = None  # Pour suivre le geste de volume actif
        self.last_hand_plate_spread_detected = False
        
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
        
        # Si aucune main n'est détectée, réinitialiser les états
        if not results.multi_hand_landmarks:
            self.last_hand_plate_detected = False
            self.last_hand_plate_spread_detected = False
            if self.last_volume_gesture is not None:
                self.last_volume_gesture = None
        
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
                current_hand_plate_spread = (gesture == "FULLSCREEN")
                
                # Détecter la transition : passage de "pas de main plate" à "main plate serrée"
                if current_hand_plate and not self.last_hand_plate_detected:
                    # Transition détectée : main plate serrée vient d'apparaître
                    if self.main_window:
                        self.main_window.toggle_play_pause()
                    self.log.debug("Transition main plate serrée détectée, toggle play/pause")
                
                # Détecter la transition : passage de "pas de main plate écartée" à "main plate écartée"
                if current_hand_plate_spread and not self.last_hand_plate_spread_detected:
                    # Transition détectée : main plate écartée vient d'apparaître
                    if self.main_window and self.main_window.video_window:
                        self.main_window.video_window.toggle_fullscreen()
                    self.log.debug("Transition main plate écartée détectée, toggle plein écran")
                
                # Gérer les gestes de navigation (avancer/reculer) - seulement si ce n'est pas une main plate
                if gesture == "AVANCER" and not current_hand_plate and not current_hand_plate_spread:
                    if self.main_window and self.main_window.video_player:
                        self.main_window.video_player.advance()
                        self.log.debug("Geste AVANCER détecté")
                elif gesture == "RECULER" and not current_hand_plate and not current_hand_plate_spread:
                    if self.main_window and self.main_window.video_player:
                        self.main_window.video_player.rewind()
                        self.log.debug("Geste RECULER détecté")
                
                # Gérer les gestes de volume (index vers le haut/bas)
                # Ajuster le volume en continu tant que le geste est maintenu
                if gesture in ["VOLUME_UP", "VOLUME_DOWN"] and not current_hand_plate and not current_hand_plate_spread:
                    if self.main_window and self.main_window.video_player:
                        # Ajuster le volume de manière continue et lente
                        delta = 0.02 if gesture == "VOLUME_UP" else -0.02  # 2% par frame (plus lent)
                        self.main_window.video_player.adjust_volume(delta)
                        # Logger seulement occasionnellement pour éviter le spam
                        if self.last_volume_gesture != gesture:
                            self.log.debug(f"Geste {gesture} détecté - ajustement continu")
                        self.last_volume_gesture = gesture
                else:
                    # Réinitialiser si le geste de volume n'est plus détecté
                    if self.last_volume_gesture is not None:
                        self.log.debug("Geste de volume terminé")
                        self.last_volume_gesture = None
                
                # Mettre à jour les états précédents
                self.last_hand_plate_detected = current_hand_plate
                self.last_hand_plate_spread_detected = current_hand_plate_spread
                
                # Afficher le geste
                if gesture == "TOGGLE_PLAY_PAUSE":
                    # Afficher l'état actuel
                    if self.main_window and self.main_window.is_playing:
                        gesture_display = "PLAY"
                    else:
                        gesture_display = "PAUSE"
                elif gesture in ["VOLUME_UP", "VOLUME_DOWN"]:
                    # Afficher le volume actuel
                    if self.main_window and self.main_window.video_player:
                        volume_percent = int(self.main_window.video_player.get_volume() * 100)
                        gesture_display = f"VOLUME: {volume_percent}%"
                    else:
                        gesture_display = gesture
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
        - Index vers le haut = VOLUME_UP
        - Index vers le bas = VOLUME_DOWN
        - Main plate serrée (tous doigts tendus, serrés) = TOGGLE_PLAY_PAUSE
        - Main plate écartée (tous doigts tendus, écartés) = FULLSCREEN
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
        middle_mcp = landmarks.landmark[9]
        ring_tip = landmarks.landmark[16]
        ring_pip = landmarks.landmark[14]
        ring_mcp = landmarks.landmark[13]
        pinky_tip = landmarks.landmark[20]
        pinky_pip = landmarks.landmark[18]
        pinky_mcp = landmarks.landmark[17]
        
        # Vérifier si les doigts sont tendus (tip au-dessus de pip)
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y
        
        # Vérifier si l'index est pointé (tendu) même s'il pointe vers le bas
        # L'index est pointé si la distance entre tip et pip est significative
        index_extended = abs(index_tip.y - index_pip.y) > 0.05  # Index tendu (peu importe la direction)
        
        # Pour le pouce, vérifier s'il est à droite (main droite) ou à gauche (main gauche) du MCP
        if is_right_hand:
            thumb_up = thumb_tip.x > thumb_mcp.x
        else:
            thumb_up = thumb_tip.x < thumb_mcp.x
        
        fingers_up = [index_up, middle_up, ring_up, pinky_up]  # Exclure le pouce pour la main plate
        count_fingers = sum(fingers_up)
        
        # Fonction utilitaire pour calculer les distances
        def calculate_distance(p1, p2):
            return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        
        # Calculer les directions pour vérifier si c'est un geste de navigation ou de volume
        index_direction_h = index_tip.x - wrist.x  # Direction horizontale
        index_direction_v = index_tip.y - wrist.y  # Direction verticale
        abs_h = abs(index_direction_h)
        abs_v = abs(index_direction_v)
        
        # Seuils et ratios
        min_threshold_h = 0.07  # Seuil minimum pour la navigation (horizontal) - compromis entre sensibilité et précision
        min_threshold_v = 0.10  # Seuil minimum pour le volume (vertical)
        
        # Calculer les ratios
        ratio_vertical = abs_v / abs_h if abs_h > 0.01 else 10.0  # Ratio vertical/horizontal
        ratio_horizontal = abs_h / abs_v if abs_v > 0.01 else 10.0  # Ratio horizontal/vertical
        
        # PRIORITÉ 1: MAIN PLATE = 4 doigts tendus (sans le pouce)
        # Mais vérifier d'abord que ce n'est PAS de la navigation (même si count_fingers >= 4)
        if count_fingers >= 4:
            # Vérifier si c'est vraiment de la navigation (mouvement horizontal marqué)
            # Si c'est de la navigation, ne pas traiter comme une main plate
            is_navigation = (index_up or index_extended) and abs_h > min_threshold_h and ratio_horizontal > 0.8
            
            # Si ce n'est pas de la navigation, c'est une main plate
            if not is_navigation:
                # Calculer la distance entre les extrémités des doigts pour détecter si ils sont écartés
                # Utiliser les distances entre les tips plutôt que les MCP pour une meilleure détection
                index_middle_tip_dist = calculate_distance(index_tip, middle_tip)
                middle_ring_tip_dist = calculate_distance(middle_tip, ring_tip)
                ring_pinky_tip_dist = calculate_distance(ring_tip, pinky_tip)
                
                # Calculer aussi une distance de référence (taille de la main) pour normaliser
                # Distance poignet-index comme référence de taille
                wrist_index_dist = calculate_distance(wrist, index_mcp)
                
                # Distance moyenne entre les extrémités des doigts
                avg_tip_spread = (index_middle_tip_dist + middle_ring_tip_dist + ring_pinky_tip_dist) / 3
                
                # Normaliser par la taille de la main pour être plus robuste
                # Si la distance moyenne entre les tips est > 42% de la taille de la main, considérer comme écartée
                if wrist_index_dist > 0:
                    normalized_spread = avg_tip_spread / wrist_index_dist
                    # Seuil légèrement réduit : si les doigts sont écartés de plus de 0.42x la taille de la main = FULLSCREEN
                    # Sinon = TOGGLE_PLAY_PAUSE (main plate serrée)
                    if normalized_spread > 0.42:
                        return "FULLSCREEN"
                    else:
                        return "TOGGLE_PLAY_PAUSE"
                else:
                    # Fallback : utiliser un seuil absolu
                    if avg_tip_spread > 0.16:  # Seuil absolu à 0.16
                        return "FULLSCREEN"
                    else:
                        return "TOGGLE_PLAY_PAUSE"
        
        # PRIORITÉ 2: Si ce n'est PAS une main plate (count_fingers < 4), vérifier volume et navigation
        # PRIORITÉ 2a: Vérifier d'abord le VOLUME (vertical) si l'index est pointé
        # Le volume doit être vraiment vertical (ratio vertical > 1.5) pour éviter les confusions
        if count_fingers < 4 and index_extended and abs_v > min_threshold_v and ratio_vertical > 1.5:
            # Index vers le haut (y plus petit = plus haut sur l'écran) = VOLUME_UP
            # Index vers le bas (y plus grand = plus bas sur l'écran) = VOLUME_DOWN
            if index_direction_v < 0:
                return "VOLUME_UP"  # index_tip.y < wrist.y = vers le haut
            else:
                return "VOLUME_DOWN"
        
        # PRIORITÉ 2b: Vérifier ensuite la NAVIGATION (horizontal) si l'index est levé OU pointé
        # La navigation doit être principalement horizontale (ratio horizontal > 0.8) pour être plus permissive
        # Le ratio de 0.8 permet la navigation même si l'index se baisse un peu
        if count_fingers < 4 and (index_up or index_extended) and abs_h > min_threshold_h and ratio_horizontal > 0.8:
            # INVERSE : La caméra est inversée par rapport à nous
            if index_direction_h > 0:
                return "RECULER"  # Inversé : droite sur écran = reculer
            else:
                return "AVANCER"  # Inversé : gauche sur écran = avancer
            
        
        # Si aucun geste reconnu, retourner None
        return None
    
    def close(self):
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()

