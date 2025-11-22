from __future__ import annotations
import time
import json
import csv
from collections import defaultdict
from typing import Optional
from pathlib import Path
import logging

class PerformanceMetrics:
    """
    Système de mesure de performance pour la détection de mains et la reconnaissance de gestes.
    """
    def __init__(self):
        self.log = logging.getLogger("myapp.metrics")
        
        # Métriques de détection
        self.total_frames = 0
        self.frames_with_hand = 0  # Frames où une main était réellement présente
        self.frames_detected = 0    # Frames où une main a été détectée
        self.frames_with_hand_and_detected = 0  # Vrai positif
        self.frames_without_hand = 0
        self.frames_detected_without_hand = 0   # Faux positif
        
        # Métriques spécifiques YOLO (confiance, nombre de mains)
        self.detection_confidences = []  # Liste des confidences de détection
        self.hands_count_per_frame = []  # Nombre de mains détectées par frame
        
        # Métriques de reconnaissance de gestes
        self.gesture_declarations = {}  # {timestamp: gesture_name} - gestes déclarés manuellement
        self.gesture_predictions = {}   # {timestamp: gesture_name} - gestes prédits par le système
        self.gesture_confusion_matrix = defaultdict(lambda: defaultdict(int))
        
        # État actuel
        self.current_declared_gesture: Optional[str] = None
        self.declaration_timestamp: Optional[float] = None
        
        # État pour la vérité terrain (présence de main)
        self.hand_present_state: Optional[bool] = None  # None = non spécifié, True = main présente, False = pas de main
        self.hand_present_timestamp: Optional[float] = None
    
    def on_frame_processed(self, hand_detected: bool, hand_present: Optional[bool] = None, 
                          confidence: Optional[float] = None, num_hands: Optional[int] = None):
        """
        Appelé à chaque frame traitée.
        hand_detected: True si le système a détecté une main
        hand_present: True si une main est réellement présente (None si non spécifié)
        confidence: Confiance de la détection (pour YOLO)
        num_hands: Nombre de mains détectées (pour YOLO)
        """
        self.total_frames += 1
        
        # Utiliser l'état de vérité terrain si fourni, sinon utiliser l'état global
        if hand_present is None:
            hand_present = self.hand_present_state
        
        if hand_present is True:
            self.frames_with_hand += 1
            if hand_detected:
                self.frames_with_hand_and_detected += 1
        elif hand_present is False:
            self.frames_without_hand += 1
            if hand_detected:
                self.frames_detected_without_hand += 1
        
        if hand_detected:
            self.frames_detected += 1
            
            # Enregistrer les métriques spécifiques YOLO
            if confidence is not None:
                self.detection_confidences.append(confidence)
            if num_hands is not None:
                self.hands_count_per_frame.append(num_hands)
    
    def on_gesture_recognized(self, predicted_gesture: str):
        """
        Appelé quand un geste est reconnu par le système.
        """
        timestamp = time.time()
        self.gesture_predictions[timestamp] = predicted_gesture
        
        # Si un geste a été déclaré récemment (dans les 0.5 secondes), l'associer
        if self.current_declared_gesture and self.declaration_timestamp:
            time_diff = timestamp - self.declaration_timestamp
            if time_diff < 0.5:  # Fenêtre de 500ms
                true_gesture = self.current_declared_gesture
                self.gesture_confusion_matrix[true_gesture][predicted_gesture] += 1
                self.log.debug(f"Geste: {true_gesture} -> Prédit: {predicted_gesture}")
    
    def declare_gesture(self, gesture_name: str):
        """
        Déclare manuellement le geste effectué (appelé via touche clavier).
        """
        self.current_declared_gesture = gesture_name
        self.declaration_timestamp = time.time()
        self.gesture_declarations[self.declaration_timestamp] = gesture_name
        self.log.info(f"Geste déclaré: {gesture_name}")
    
    def set_hand_present(self, present: bool):
        """
        Définit l'état de vérité terrain pour la présence de main.
        present: True si une main est présente, False sinon
        """
        self.hand_present_state = present
        self.hand_present_timestamp = time.time()
        status = "présente" if present else "absente"
        self.log.info(f"Vérité terrain: main {status}")
    
    def clear_hand_present(self):
        """Réinitialise l'état de vérité terrain (non spécifié)."""
        self.hand_present_state = None
        self.hand_present_timestamp = None
        self.log.debug("Vérité terrain réinitialisée")
    
    def get_detection_metrics(self) -> dict:
        """
        Retourne les métriques de détection.
        """
        if self.total_frames == 0:
            return {
                "total_frames": 0,
                "detection_rate": 0.0,
                "false_positive_rate": 0.0,
                "true_positive_rate": 0.0
            }
        
        detection_rate = (self.frames_detected / self.total_frames) * 100 if self.total_frames > 0 else 0.0
        
        false_positive_rate = 0.0
        if self.frames_without_hand > 0:
            false_positive_rate = (self.frames_detected_without_hand / self.frames_without_hand) * 100
        
        true_positive_rate = 0.0
        if self.frames_with_hand > 0:
            true_positive_rate = (self.frames_with_hand_and_detected / self.frames_with_hand) * 100
        
        # Calculer les métriques spécifiques YOLO
        avg_confidence = 0.0
        if self.detection_confidences:
            avg_confidence = sum(self.detection_confidences) / len(self.detection_confidences)
        
        avg_hands_per_frame = 0.0
        if self.hands_count_per_frame:
            avg_hands_per_frame = sum(self.hands_count_per_frame) / len(self.hands_count_per_frame)
        
        max_hands = max(self.hands_count_per_frame) if self.hands_count_per_frame else 0
        
        return {
            "total_frames": self.total_frames,
            "frames_with_hand": self.frames_with_hand,
            "frames_detected": self.frames_detected,
            "frames_with_hand_and_detected": self.frames_with_hand_and_detected,
            "frames_without_hand": self.frames_without_hand,
            "frames_detected_without_hand": self.frames_detected_without_hand,
            "detection_rate": detection_rate,
            "false_positive_rate": false_positive_rate,
            "true_positive_rate": true_positive_rate,
            "avg_confidence": avg_confidence,
            "avg_hands_per_frame": avg_hands_per_frame,
            "max_hands_detected": max_hands,
            "total_detections": len(self.detection_confidences)
        }
    
    def get_gesture_metrics(self) -> dict:
        """
        Retourne les métriques de reconnaissance de gestes.
        """
        total_declarations = len(self.gesture_declarations)
        total_predictions = len(self.gesture_predictions)
        
        # Calculer la précision par geste
        gesture_precision = {}
        gesture_counts = defaultdict(int)
        gesture_correct = defaultdict(int)
        
        for true_gesture, predictions in self.gesture_confusion_matrix.items():
            total_for_gesture = sum(predictions.values())
            correct_for_gesture = predictions.get(true_gesture, 0)
            gesture_counts[true_gesture] = total_for_gesture
            gesture_correct[true_gesture] = correct_for_gesture
            
            if total_for_gesture > 0:
                gesture_precision[true_gesture] = (correct_for_gesture / total_for_gesture) * 100
            else:
                gesture_precision[true_gesture] = 0.0
        
        # Matrice de confusion complète
        confusion_matrix = dict(self.gesture_confusion_matrix)
        
        return {
            "total_declarations": total_declarations,
            "total_predictions": total_predictions,
            "gesture_precision": dict(gesture_precision),
            "gesture_counts": dict(gesture_counts),
            "gesture_correct": dict(gesture_correct),
            "confusion_matrix": {k: dict(v) for k, v in confusion_matrix.items()}
        }
    
    def reset(self):
        """
        Réinitialise toutes les métriques.
        """
        self.total_frames = 0
        self.frames_with_hand = 0
        self.frames_detected = 0
        self.frames_with_hand_and_detected = 0
        self.frames_without_hand = 0
        self.frames_detected_without_hand = 0
        
        self.detection_confidences.clear()
        self.hands_count_per_frame.clear()
        
        self.gesture_declarations.clear()
        self.gesture_predictions.clear()
        self.gesture_confusion_matrix.clear()
        
        self.current_declared_gesture = None
        self.declaration_timestamp = None
        self.hand_present_state = None
        self.hand_present_timestamp = None
        
        self.log.info("Métriques réinitialisées")
    
    def export_to_json(self, file_path: str | Path) -> bool:
        """
        Exporte toutes les métriques au format JSON.
        """
        try:
            data = {
                "detection_metrics": self.get_detection_metrics(),
                "gesture_metrics": self.get_gesture_metrics(),
                "timestamp": time.time()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.log.info(f"Métriques exportées en JSON: {file_path}")
            return True
        except Exception as e:
            self.log.exception(f"Erreur lors de l'export JSON: {e}")
            return False
    
    def export_to_csv(self, file_path: str | Path) -> bool:
        """
        Exporte les métriques au format CSV.
        """
        try:
            det_metrics = self.get_detection_metrics()
            gest_metrics = self.get_gesture_metrics()
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Métriques de détection
                writer.writerow(["Métrique", "Valeur"])
                writer.writerow(["Total de frames", det_metrics['total_frames']])
                writer.writerow(["Frames avec main détectée", det_metrics['frames_detected']])
                writer.writerow(["Frames avec main présente", det_metrics['frames_with_hand']])
                writer.writerow(["Vrais positifs", det_metrics['frames_with_hand_and_detected']])
                writer.writerow(["Faux positifs", det_metrics['frames_detected_without_hand']])
                writer.writerow(["Taux de détection (%)", f"{det_metrics['detection_rate']:.2f}"])
                writer.writerow(["Taux de faux positifs (%)", f"{det_metrics['false_positive_rate']:.2f}"])
                writer.writerow(["Taux de vrais positifs (%)", f"{det_metrics['true_positive_rate']:.2f}"])
                
                # Métriques spécifiques YOLO si disponibles
                if det_metrics.get('avg_confidence') is not None:
                    writer.writerow([])  # Ligne vide
                    writer.writerow(["Métriques YOLO"])
                    writer.writerow(["Confiance moyenne", f"{det_metrics['avg_confidence']:.3f}"])
                    writer.writerow(["Mains moyennes par frame", f"{det_metrics['avg_hands_per_frame']:.2f}"])
                    writer.writerow(["Nombre max de mains détectées", f"{det_metrics['max_hands_detected']}"])
                    writer.writerow(["Total de détections", f"{det_metrics['total_detections']}"])
                
                writer.writerow([])  # Ligne vide
                writer.writerow(["Reconnaissance de Gestes"])
                writer.writerow(["Geste", "Correct", "Total", "Précision (%)"])
                
                precision = gest_metrics['gesture_precision']
                counts = gest_metrics['gesture_counts']
                correct = gest_metrics['gesture_correct']
                
                for gesture in sorted(precision.keys()):
                    writer.writerow([
                        gesture,
                        correct.get(gesture, 0),
                        counts.get(gesture, 0),
                        f"{precision[gesture]:.2f}"
                    ])
            
            self.log.info(f"Métriques exportées en CSV: {file_path}")
            return True
        except Exception as e:
            self.log.exception(f"Erreur lors de l'export CSV: {e}")
            return False
    
    def export_confusion_matrix_image(self, file_path: str | Path) -> bool:
        """
        Génère une image visuelle de la matrice de confusion.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Backend non-interactif
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            self.log.error("matplotlib n'est pas installé. Installez-le: pip install matplotlib")
            return False
        
        try:
            gest_metrics = self.get_gesture_metrics()
            confusion = gest_metrics['confusion_matrix']
            
            if not confusion:
                self.log.warning("Aucune donnée de matrice de confusion disponible")
                return False
            
            # Obtenir tous les gestes uniques
            all_gestures = set()
            for true_gesture, predictions in confusion.items():
                all_gestures.add(true_gesture)
                all_gestures.update(predictions.keys())
            all_gestures = sorted(all_gestures)
            
            if not all_gestures:
                self.log.warning("Aucun geste dans la matrice de confusion")
                return False
            
            # Créer la matrice numpy
            n = len(all_gestures)
            matrix = np.zeros((n, n), dtype=int)
            
            for i, true_gesture in enumerate(all_gestures):
                predictions = confusion.get(true_gesture, {})
                for j, predicted_gesture in enumerate(all_gestures):
                    matrix[i, j] = predictions.get(predicted_gesture, 0)
            
            # Créer la figure
            fig, ax = plt.subplots(figsize=(max(8, n * 0.8), max(6, n * 0.7)))
            
            # Afficher la matrice avec colormap
            im = ax.imshow(matrix, cmap='Blues', aspect='auto')
            
            # Ajouter les valeurs dans chaque cellule
            for i in range(n):
                for j in range(n):
                    text = ax.text(j, i, matrix[i, j],
                                 ha="center", va="center", color="black" if matrix[i, j] < matrix.max() * 0.5 else "white",
                                 fontweight='bold')
            
            # Configurer les axes
            ax.set_xticks(np.arange(n))
            ax.set_yticks(np.arange(n))
            ax.set_xticklabels(all_gestures, rotation=45, ha='right')
            ax.set_yticklabels(all_gestures)
            
            # Labels
            ax.set_xlabel('Geste Prédit', fontsize=12, fontweight='bold')
            ax.set_ylabel('Geste Réel', fontsize=12, fontweight='bold')
            ax.set_title('Matrice de Confusion - Reconnaissance de Gestes', fontsize=14, fontweight='bold', pad=20)
            
            # Barre de couleur
            plt.colorbar(im, ax=ax, label='Nombre de prédictions')
            
            # Ajuster le layout
            plt.tight_layout()
            
            # Sauvegarder
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.log.info(f"Matrice de confusion exportée en image: {file_path}")
            return True
        except Exception as e:
            self.log.exception(f"Erreur lors de l'export de l'image: {e}")
            return False

