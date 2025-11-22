from __future__ import annotations
import logging, os
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMenuBar, QFileDialog, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage, QAction, QKeyEvent

from myapp.video.camera import Camera
from myapp.video.video_player import VideoPlayer
from myapp.ui.log_viewer import LogViewerDialog
from myapp.ui.help_dialog import HelpDialog
from myapp.ui.settings_dialog import SettingsDialog
from myapp.ui.metrics_dialog import MetricsDialog
from myapp.ui.video_window import VideoWindow
from myapp.ui.video_window import VideoWindow
from myapp.utils.config import save_settings
from myapp.utils.logger import setup_logging
from myapp.utils.metrics import PerformanceMetrics
from myapp.processing.hand_mediapipe import HandMediaPipe

class MainWindow(QMainWindow):
    def __init__(self, settings: dict):
        super().__init__()
        self.setWindowTitle("MyApp – Webcam + MediaPipe")
        self.settings = settings
        self.log = logging.getLogger("myapp.ui")
        
        # Système de métriques
        self.metrics = PerformanceMetrics()

        # Menus
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
  
        m_file = menubar.addMenu("Fichier")
        act_open_video = QAction("Ouvrir une vidéo…", self)
        act_params = QAction("Paramètres…", self)
        act_quit = QAction("Quitter", self)
        m_file.addAction(act_open_video)
        m_file.addSeparator()
        m_file.addAction(act_params)
        m_file.addSeparator()
        m_file.addAction(act_quit)
        act_open_video.triggered.connect(self.open_video)
        act_params.triggered.connect(self.open_settings)
        act_quit.triggered.connect(self.close)

        m_logs = menubar.addMenu("Logs")
        act_view_logs = QAction("Voir les logs…", self)
        m_logs.addAction(act_view_logs)
        act_view_logs.triggered.connect(self.open_logs)
        
        m_metrics = menubar.addMenu("Métriques")
        act_view_metrics = QAction("Voir les métriques…", self)
        m_metrics.addAction(act_view_metrics)
        act_view_metrics.triggered.connect(self.open_metrics)

        m_help = menubar.addMenu("Aide")
        act_help = QAction("Aide…", self)
        m_help.addAction(act_help)
        act_help.triggered.connect(self.open_help)

        # UI
        self.video_label = QLabel("Flux vidéo")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        # Permettre le redimensionnement automatique pour garder les proportions
        self.video_label.setScaledContents(True)

        btn_row = QHBoxLayout()
        self.btn_none = QPushButton("Aucun"); self.btn_none.setCheckable(True); self.btn_none.setChecked(True)
        self.btn_mediapipe = QPushButton("MediaPipe"); self.btn_mediapipe.setCheckable(True)
        btn_row.addWidget(self.btn_none); btn_row.addWidget(self.btn_mediapipe)

        self.btn_none.clicked.connect(lambda: self.set_processor("none"))
        self.btn_mediapipe.clicked.connect(lambda: self.set_processor("mediapipe"))
        
        # Label pour afficher les instructions de gestes et l'état
        self.instructions_label = QLabel(
            "Gestes: Main plate = PLAY/PAUSE | Index droite = AVANCER | Index gauche = RECULER\n"
            "La vidéo s'ouvrira dans une fenêtre séparée. La caméra reste active ici.\n"
            "Vérité terrain: H = Main présente | N = Pas de main | C = Réinitialiser"
        )
        self.instructions_label.setStyleSheet("color: gray; font-size: 10px;")
        self.instructions_label.setAlignment(Qt.AlignCenter)
        
        # Label pour afficher les infos vidéo (position, durée)
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet("color: blue; font-size: 11px;")
        self.video_info_label.setAlignment(Qt.AlignCenter)
        
        # Label pour afficher l'état (caméra active)
        self.status_label = QLabel("État: Caméra active")
        self.status_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addLayout(btn_row)
        layout.addWidget(self.status_label)
        layout.addWidget(self.video_info_label)
        layout.addWidget(self.instructions_label)
        central = QWidget(); central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Activer la capture des touches clavier
        self.setFocusPolicy(Qt.StrongFocus)

        # Source vidéo (caméra ou fichier vidéo)
        self.camera: Optional[Camera] = None
        self.video_player: Optional[VideoPlayer] = None
        self.video_window: Optional[VideoWindow] = None  # Fenêtre séparée pour la vidéo
        self._init_camera()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self._apply_timer_interval()

        # Processor
        self.current_processor = None
        self.current_mode = "none"
        
        # Compteur pour sauter des frames (optimisation performance)
        self.frame_skip_counter = 0
        
        # État de lecture vidéo
        self.is_playing = True  # Par défaut en lecture

    # --- Caméra / Timer ---
    def _init_camera(self):
        cam_cfg = self.settings.get("camera", {})
        self._release_camera_if_needed()
        self.camera = Camera(
            index=cam_cfg.get("index", 0),
            resolution=tuple(cam_cfg.get("resolution", (1280, 720))),
            fps=cam_cfg.get("fps", 30),
        )
        self.log.info("Caméra initialisée.")

    def _release_camera_if_needed(self):
        if getattr(self, "camera", None):
            try:
                self.camera.release()
            except Exception:
                self.log.exception("Libération caméra")
            self.camera = None

    def _apply_timer_interval(self):
        if self.video_player:
            fps = self.video_player.fps
        else:
            fps = int(self.settings.get("camera", {}).get("fps", 30) or 30)
        self.timer.stop()
        self.timer.start(int(1000 / max(1, fps)))

    # --- Menus ---
    def open_logs(self):
        log_cfg = self.settings.get("logging", {})
        handlers = log_cfg.get("handlers", {})
        app_log = os.path.abspath(handlers.get("file", "log/app.log"))
        log_dir = os.path.dirname(app_log) or "log"
        err_log = os.path.abspath(os.path.join(log_dir, "erreurs.log"))
        dlg = LogViewerDialog(app_log, err_log, self)
        dlg.resize(900, 600)
        dlg.exec()

    def open_help(self):
        dlg = HelpDialog(self)
        dlg.resize(520, 300)
        dlg.exec()
    
    def open_metrics(self):
        dlg = MetricsDialog(self.metrics, self)
        dlg.exec()
    
    def open_video(self):
        """Ouvre un fichier vidéo dans une fenêtre séparée."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir une vidéo",
            "",
            "Fichiers vidéo (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            try:
                # Fermer la fenêtre vidéo précédente si elle existe
                if self.video_window:
                    self.video_window.close()
                    self.video_window = None
                
                # Libérer la vidéo précédente si elle existe
                if self.video_player:
                    self.video_player.release()
                    self.video_player = None
                
                # Charger la nouvelle vidéo
                self.video_player = VideoPlayer(file_path)
                self.video_player.pause()  # Commencer en pause
                
                # Créer et afficher la fenêtre vidéo séparée
                self.video_window = VideoWindow(self.video_player, parent=self)
                self.video_window.show()
                
                # La caméra reste active dans la fenêtre principale
                # Les gestes détectés contrôleront la vidéo via self.video_player
                
                from pathlib import Path
                video_name = Path(file_path).name
                self.log.info(f"Vidéo chargée dans fenêtre séparée: {video_name} (FPS: {self.video_player.fps})")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible d'ouvrir la vidéo:\n{str(e)}"
                )
                self.log.exception("Erreur ouverture vidéo")
                # Nettoyer en cas d'erreur
                if self.video_player:
                    try:
                        self.video_player.release()
                    except:
                        pass
                    self.video_player = None
    
    def toggle_play_pause(self):
        """Bascule entre play et pause de la vidéo (si une vidéo est chargée)."""
        if self.video_player:
            self.video_player.toggle_play_pause()
            self.is_playing = self.video_player.is_playing
            if self.is_playing:
                self.log.info("Lecture vidéo activée")
            else:
                self.log.info("Pause vidéo activée")
        else:
            self.log.debug("Aucune vidéo chargée pour toggle play/pause")

    # --- Processor ---
    def set_processor(self, mode: str):
        if self.current_processor:
            try:
                self.current_processor.close()
            except Exception:
                self.log.exception("close() processor")
            self.current_processor = None

        self.btn_none.setChecked(mode == "none")
        self.btn_mediapipe.setChecked(mode == "mediapipe")

        if mode == "mediapipe":
            try:
                eng_cfg = dict(self.settings.get("engines", {}).get("mediapipe", {}))
                processor = HandMediaPipe(name="HandMediaPipe", config=self.settings, **eng_cfg)
                # Connecter le callback de métriques
                processor.metrics_callback = self.metrics
                # Passer la référence à la fenêtre principale pour accéder à l'état play/pause
                processor.main_window = self
                self.current_processor = processor
                self.log.info("MediaPipe initialisé avec succès")
            except Exception as e:
                self.log.exception("Init HandMediaPipe échouée: %s", str(e))
                # Afficher un message d'erreur à l'utilisateur
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Erreur MediaPipe",
                    f"Impossible d'initialiser MediaPipe:\n{str(e)}\n\n"
                    "Assurez-vous que mediapipe est installé:\n"
                    "pip install mediapipe"
                )
                mode = "none"
                self.current_processor = None
                # Remettre les boutons dans le bon état
                self.btn_none.setChecked(True)
                self.btn_mediapipe.setChecked(False)

        self.current_mode = mode
        self.log.info("Mode actif: %s", mode)

    # --- Affichage ---
    def update_frame(self):
        """Met à jour l'affichage de la caméra dans la fenêtre principale."""
        frame = None
        
        # La fenêtre principale affiche toujours la caméra
        # La vidéo est affichée dans une fenêtre séparée (video_window)
        if self.camera:
            frame = self.camera.get_frame()
            if frame is None:
                return
            self.video_info_label.setText("")  # Pas d'info pour la caméra
        else:
            # Pas de caméra - afficher un message
            self.video_label.setText("Aucune caméra disponible")
            return
        
        if frame is None:
            self.log.warning("Frame est None après récupération")
            return
        
        # Traiter la frame seulement si on a un processeur
        if self.current_processor:
            try:
                frame = self.current_processor.process_frame(frame)
                if frame is None:
                    self.log.warning("Frame est None après traitement")
                    return
            except Exception as e:
                self.log.exception("Erreur traitement: %s", str(e))
                # Continuer quand même avec la frame originale
        
        # Convertir et afficher
        qimg = self._to_qimage(frame)
        if qimg:
            # Utiliser une conversion directe sans redimensionnement à chaque fois
            # Le redimensionnement se fera automatiquement par Qt
            pixmap = QPixmap.fromImage(qimg)
            self.video_label.setPixmap(pixmap)
        else:
            self.log.warning("Impossible de convertir la frame en QImage")

    @staticmethod
    def _to_qimage(frame):
        import cv2
        if frame is None: return None
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            frame = frame[:, :, ::-1].copy()
        h, w, _ = frame.shape
        return QImage(frame.data, w, h, 3*w, QImage.Format_RGB888)

    def closeEvent(self, e):
        try: self.timer.stop()
        except Exception: pass
        if self.current_processor:
            try: self.current_processor.close()
            except Exception: pass
        self._release_camera_if_needed()
        # Fermer la fenêtre vidéo si elle existe
        if self.video_window:
            try: self.video_window.close()
            except Exception: pass
        if self.video_player:
            try: self.video_player.release()
            except Exception: pass
        super().closeEvent(e)
        
    # ---------- UI actions ----------
    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        dlg.settingsChanged.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self, new_settings: dict):
        """Applique les changements, sauve YAML, reconfigure logging/caméra à chaud."""
        # sauvegarder d'abord
        save_settings(new_settings)
        self.settings = new_settings
        # reconfigure logging
        setup_logging(self.settings.get("logging"))
        logging.getLogger("myapp").info("Configuration rechargée depuis la fenêtre Paramètres.")

        # reconfigure caméra + timer
        self._init_camera()
        self._apply_timer_interval()
    
    # --- Gestion des touches clavier ---
    def keyPressEvent(self, event: QKeyEvent):
        """Gère les touches clavier pour déclarer les gestes et la vérité terrain."""
        key = event.key()
        
        # Mapping des touches aux gestes de contrôle vidéo
        if key == Qt.Key_Space:
            # Espace = Toggle Play/Pause
            self.toggle_play_pause()
            self.metrics.declare_gesture("TOGGLE_PLAY_PAUSE")
            self.log.info("Geste déclaré via clavier: TOGGLE_PLAY_PAUSE")
        elif key == Qt.Key_Right:
            self.metrics.declare_gesture("AVANCER")
            self.log.info("Geste déclaré via clavier: AVANCER")
        elif key == Qt.Key_Left:
            self.metrics.declare_gesture("RECULER")
            self.log.info("Geste déclaré via clavier: RECULER")
        # Touches pour la vérité terrain (présence de main)
        elif key == Qt.Key_H:
            # H = Hand present (main présente)
            self.metrics.set_hand_present(True)
            self.status_label.setText("État: Main présente (vérité terrain)")
            self.status_label.setStyleSheet("color: blue; font-size: 12px; font-weight: bold;")
        elif key == Qt.Key_N:
            # N = No hand (pas de main)
            self.metrics.set_hand_present(False)
            self.status_label.setText("État: Pas de main (vérité terrain)")
            self.status_label.setStyleSheet("color: purple; font-size: 12px; font-weight: bold;")
        elif key == Qt.Key_C:
            # C = Clear (réinitialiser la vérité terrain)
            self.metrics.clear_hand_present()
            self.status_label.setText("État: Caméra active")
            self.status_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
        else:
            super().keyPressEvent(event)
