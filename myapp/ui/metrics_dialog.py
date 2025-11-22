from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget, QTextEdit,
    QFileDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt
from myapp.utils.metrics import PerformanceMetrics
from pathlib import Path
import logging

class MetricsDialog(QDialog):
    """
    Fenêtre d'affichage des métriques de performance.
    """
    def __init__(self, metrics: PerformanceMetrics, parent=None):
        super().__init__(parent)
        self.metrics = metrics
        self.log = logging.getLogger("myapp.ui.metrics_dialog")
        self.setWindowTitle("Métriques de Performance")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Onglets
        tabs = QTabWidget()
        
        # Onglet Détection
        detection_tab = QWidget()
        detection_layout = QVBoxLayout()
        self.detection_table = QTableWidget()
        self.detection_table.setColumnCount(2)
        self.detection_table.setHorizontalHeaderLabels(["Métrique", "Valeur"])
        self.detection_table.horizontalHeader().setStretchLastSection(True)
        detection_layout.addWidget(QLabel("<b>Métriques de Détection</b>"))
        detection_layout.addWidget(self.detection_table)
        detection_tab.setLayout(detection_layout)
        tabs.addTab(detection_tab, "Détection")
        
        # Onglet Reconnaissance de Gestes
        gesture_tab = QWidget()
        gesture_layout = QVBoxLayout()
        
        # Précision par geste
        gesture_layout.addWidget(QLabel("<b>Précision par Geste</b>"))
        self.gesture_table = QTableWidget()
        self.gesture_table.setColumnCount(4)
        self.gesture_table.setHorizontalHeaderLabels(["Geste", "Correct", "Total", "Précision (%)"])
        self.gesture_table.horizontalHeader().setStretchLastSection(True)
        gesture_layout.addWidget(self.gesture_table)
        
        # Matrice de confusion
        gesture_layout.addWidget(QLabel("<b>Matrice de Confusion</b>"))
        self.confusion_text = QTextEdit()
        self.confusion_text.setReadOnly(True)
        self.confusion_text.setFontFamily("Courier")
        gesture_layout.addWidget(self.confusion_text)
        
        gesture_tab.setLayout(gesture_layout)
        tabs.addTab(gesture_tab, "Reconnaissance de Gestes")
        
        layout.addWidget(tabs)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Actualiser")
        btn_reset = QPushButton("Réinitialiser")
        btn_export = QPushButton("Exporter ▼")
        btn_close = QPushButton("Fermer")
        
        btn_refresh.clicked.connect(self.refresh_metrics)
        btn_reset.clicked.connect(self.reset_metrics)
        btn_export.clicked.connect(self.show_export_menu)
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # Actualiser immédiatement
        self.refresh_metrics()
    
    def refresh_metrics(self):
        """Actualise l'affichage des métriques."""
        # Métriques de détection
        det_metrics = self.metrics.get_detection_metrics()
        # Ajuster le nombre de lignes selon les métriques disponibles
        row_count = 8
        if det_metrics.get('avg_confidence') is not None:
            row_count += 3  # Ajouter les métriques YOLO
        
        self.detection_table.setRowCount(row_count)
        
        rows = [
            ("Total de frames", f"{det_metrics['total_frames']}"),
            ("Frames avec main détectée", f"{det_metrics['frames_detected']}"),
            ("Frames avec main présente", f"{det_metrics['frames_with_hand']}"),
            ("Vrais positifs", f"{det_metrics['frames_with_hand_and_detected']}"),
            ("Faux positifs", f"{det_metrics['frames_detected_without_hand']}"),
            ("Taux de détection (%)", f"{det_metrics['detection_rate']:.2f}"),
            ("Taux de vrais positifs (%)", f"{det_metrics['true_positive_rate']:.2f}"),
            ("Taux de faux positifs (%)", f"{det_metrics['false_positive_rate']:.2f}"),
        ]
        
        # Ajouter les métriques spécifiques YOLO si disponibles
        if det_metrics.get('avg_confidence') is not None:
            rows.extend([
                ("", ""),  # Séparateur
                ("Confiance moyenne", f"{det_metrics['avg_confidence']:.3f}"),
                ("Mains moyennes par frame", f"{det_metrics['avg_hands_per_frame']:.2f}"),
                ("Nombre max de mains détectées", f"{det_metrics['max_hands_detected']}"),
            ])
        
        for i, (label, value) in enumerate(rows):
            self.detection_table.setItem(i, 0, QTableWidgetItem(label))
            self.detection_table.setItem(i, 1, QTableWidgetItem(value))
        
        # Métriques de reconnaissance de gestes
        gest_metrics = self.metrics.get_gesture_metrics()
        precision = gest_metrics['gesture_precision']
        counts = gest_metrics['gesture_counts']
        correct = gest_metrics['gesture_correct']
        
        self.gesture_table.setRowCount(len(precision))
        for i, (gesture, prec) in enumerate(sorted(precision.items())):
            self.gesture_table.setItem(i, 0, QTableWidgetItem(gesture))
            self.gesture_table.setItem(i, 1, QTableWidgetItem(str(correct.get(gesture, 0))))
            self.gesture_table.setItem(i, 2, QTableWidgetItem(str(counts.get(gesture, 0))))
            self.gesture_table.setItem(i, 3, QTableWidgetItem(f"{prec:.2f}"))
        
        # Matrice de confusion
        confusion = gest_metrics['confusion_matrix']
        if confusion:
            # Obtenir tous les gestes uniques
            all_gestures = set()
            for true_gesture, predictions in confusion.items():
                all_gestures.add(true_gesture)
                all_gestures.update(predictions.keys())
            all_gestures = sorted(all_gestures)
            
            # Créer la matrice
            lines = ["Matrice de Confusion (Vrai → Prédit):\n"]
            lines.append(" " * 15 + " | " + " | ".join(f"{g:12s}" for g in all_gestures))
            lines.append("-" * (15 + 3 + len(all_gestures) * 15))
            
            for true_gesture in all_gestures:
                row = f"{true_gesture:15s} | "
                predictions = confusion.get(true_gesture, {})
                row += " | ".join(f"{predictions.get(g, 0):12d}" for g in all_gestures)
                lines.append(row)
            
            self.confusion_text.setPlainText("\n".join(lines))
        else:
            self.confusion_text.setPlainText("Aucune donnée de matrice de confusion disponible.\nDéclarez des gestes avec les touches clavier pour commencer.")
    
    def reset_metrics(self):
        """Réinitialise les métriques."""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir réinitialiser toutes les métriques ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.metrics.reset()
            self.refresh_metrics()
    
    def show_export_menu(self):
        """Affiche un menu pour choisir le format d'export."""
        menu = QMenu(self)
        
        act_json = menu.addAction("Exporter en JSON")
        act_csv = menu.addAction("Exporter en CSV")
        act_image = menu.addAction("Exporter matrice de confusion (Image PNG)")
        act_all = menu.addAction("Exporter tout (JSON + CSV + Image)")
        
        act_json.triggered.connect(lambda: self.export_metrics("json"))
        act_csv.triggered.connect(lambda: self.export_metrics("csv"))
        act_image.triggered.connect(lambda: self.export_metrics("image"))
        act_all.triggered.connect(lambda: self.export_metrics("all"))
        
        # Afficher le menu sous le bouton
        button = self.sender()
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def export_metrics(self, format_type: str):
        """Exporte les métriques dans le format spécifié."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter les métriques en JSON",
                f"metrics_{timestamp}.json",
                "Fichiers JSON (*.json);;Tous les fichiers (*.*)"
            )
            if file_path:
                if self.metrics.export_to_json(file_path):
                    QMessageBox.information(self, "Succès", f"Métriques exportées avec succès:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Erreur", "Erreur lors de l'export JSON.")
        
        elif format_type == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter les métriques en CSV",
                f"metrics_{timestamp}.csv",
                "Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
            )
            if file_path:
                if self.metrics.export_to_csv(file_path):
                    QMessageBox.information(self, "Succès", f"Métriques exportées avec succès:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Erreur", "Erreur lors de l'export CSV.")
        
        elif format_type == "image":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter la matrice de confusion en image",
                f"confusion_matrix_{timestamp}.png",
                "Images PNG (*.png);;Tous les fichiers (*.*)"
            )
            if file_path:
                if self.metrics.export_confusion_matrix_image(file_path):
                    QMessageBox.information(self, "Succès", f"Matrice de confusion exportée avec succès:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Erreur", "Erreur lors de l'export de l'image.\nAssurez-vous que matplotlib est installé: pip install matplotlib")
        
        elif format_type == "all":
            # Demander un dossier de destination
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Choisir le dossier de destination pour l'export"
            )
            if dir_path:
                dir_path = Path(dir_path)
                success_count = 0
                errors = []
                
                # JSON
                json_path = dir_path / f"metrics_{timestamp}.json"
                if self.metrics.export_to_json(json_path):
                    success_count += 1
                else:
                    errors.append("JSON")
                
                # CSV
                csv_path = dir_path / f"metrics_{timestamp}.csv"
                if self.metrics.export_to_csv(csv_path):
                    success_count += 1
                else:
                    errors.append("CSV")
                
                # Image
                img_path = dir_path / f"confusion_matrix_{timestamp}.png"
                if self.metrics.export_confusion_matrix_image(img_path):
                    success_count += 1
                else:
                    errors.append("Image (matplotlib requis)")
                
                if success_count == 3:
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"Tous les fichiers ont été exportés avec succès dans:\n{dir_path}"
                    )
                elif success_count > 0:
                    QMessageBox.warning(
                        self,
                        "Export partiel",
                        f"{success_count}/3 fichiers exportés avec succès.\n"
                        f"Erreurs: {', '.join(errors)}\n\n"
                        f"Dossier: {dir_path}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Erreur",
                        "Aucun fichier n'a pu être exporté.\n"
                        f"Erreurs: {', '.join(errors)}"
                    )

