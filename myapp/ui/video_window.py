from __future__ import annotations
import logging
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage

from myapp.video.video_player import VideoPlayer


class VideoWindow(QMainWindow):
    """
    Fenêtre séparée pour afficher la vidéo.
    Contrôlée par les gestes détectés dans la fenêtre principale.
    """
    def __init__(self, video_player: VideoPlayer, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger("myapp.video_window")
        self.video_player = video_player
        
        # Mettre à jour le titre de la fenêtre
        from pathlib import Path
        video_name = Path(video_player.video_path).name
        self.setWindowTitle(f"Vidéo – {video_name}")
        
        # UI
        self.video_label = QLabel("Chargement de la vidéo...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setScaledContents(True)
        
        # Label pour afficher les infos vidéo (position, durée)
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet("color: blue; font-size: 11px;")
        self.video_info_label.setAlignment(Qt.AlignCenter)
        
        # Label pour afficher l'état de lecture
        self.status_label = QLabel("État: PAUSE")
        self.status_label.setStyleSheet("color: orange; font-size: 12px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.video_info_label)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Timer pour mettre à jour la vidéo
        self.timer = QTimer(self)
        fps = self.video_player.fps if self.video_player.fps > 0 else 30
        self.timer.setInterval(int(1000 / max(1, fps)))
        self.timer.timeout.connect(self.update_frame)
        self.timer.start()
        
        # Afficher la première frame immédiatement
        self.update_frame()
        
        self.log.info(f"Fenêtre vidéo créée pour: {video_name}")
    
    def update_frame(self):
        """Met à jour l'affichage de la vidéo."""
        if not self.video_player:
            return
        
        result = self.video_player.get_frame()
        if result:
            frame, frame_num, total_frames = result
            if frame is None:
                self.log.warning("Frame vidéo est None")
                return
            
            # Mettre à jour les infos vidéo
            pos_sec = self.video_player.get_position()
            dur_sec = self.video_player.get_duration()
            self.video_info_label.setText(
                f"Frame: {frame_num}/{total_frames} | "
                f"Temps: {int(pos_sec//60)}:{int(pos_sec%60):02d} / {int(dur_sec//60)}:{int(dur_sec%60):02d}"
            )
            
            # Mettre à jour l'état de lecture
            if self.video_player.is_playing:
                self.status_label.setText("État: PLAY")
                self.status_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
            else:
                self.status_label.setText("État: PAUSE")
                self.status_label.setStyleSheet("color: orange; font-size: 12px; font-weight: bold;")
            
            # Mettre à jour la position si en lecture
            if self.video_player.is_playing:
                self.video_player.update()
            
            # Convertir et afficher la frame
            qimg = self._to_qimage(frame)
            if qimg:
                pixmap = QPixmap.fromImage(qimg)
                self.video_label.setPixmap(pixmap)
            else:
                self.log.warning("Impossible de convertir la frame en QImage")
        else:
            # Fin de vidéo
            self.video_player.pause()
            self.status_label.setText("État: FIN")
            self.status_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
            self.log.info("Fin de la vidéo atteinte")
    
    @staticmethod
    def _to_qimage(frame):
        """Convertit une frame OpenCV en QImage."""
        import cv2
        if frame is None:
            return None
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            frame = frame[:, :, ::-1].copy()  # BGR vers RGB
        h, w, _ = frame.shape
        return QImage(frame.data, w, h, 3*w, QImage.Format_RGB888)
    
    def closeEvent(self, e):
        """Libère les ressources lors de la fermeture."""
        try:
            self.timer.stop()
        except Exception:
            pass
        self.log.info("Fenêtre vidéo fermée")
        super().closeEvent(e)

