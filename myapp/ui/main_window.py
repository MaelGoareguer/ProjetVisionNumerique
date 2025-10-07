from __future__ import annotations
import logging, os
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMenuBar
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage, QAction

from myapp.video.camera import Camera
from myapp.ui.log_viewer import LogViewerDialog
from myapp.ui.help_dialog import HelpDialog
from myapp.ui.settings_dialog import SettingsDialog
from myapp.utils.config import save_settings
from myapp.utils.logger import setup_logging
from myapp.processing.hand_yolo import HandYolo

class MainWindow(QMainWindow):
    def __init__(self, settings: dict):
        super().__init__()
        self.setWindowTitle("MyApp – Webcam + YOLO")
        self.settings = settings
        self.log = logging.getLogger("myapp.ui")

        # Menus
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
  
        m_file = menubar.addMenu("Fichier")
        act_params = QAction("Paramètres…", self)
        act_quit = QAction("Quitter", self)
        m_file.addAction(act_params)
        m_file.addSeparator()
        m_file.addAction(act_quit)
        act_params.triggered.connect(self.open_settings)
        act_quit.triggered.connect(self.close)

        m_logs = menubar.addMenu("Logs")
        act_view_logs = QAction("Voir les logs…", self)
        m_logs.addAction(act_view_logs)
        act_view_logs.triggered.connect(self.open_logs)

        m_help = menubar.addMenu("Aide")
        act_help = QAction("Aide…", self)
        m_help.addAction(act_help)
        act_help.triggered.connect(self.open_help)

        # UI
        self.video_label = QLabel("Flux vidéo")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 360)

        btn_row = QHBoxLayout()
        self.btn_none = QPushButton("Aucun"); self.btn_none.setCheckable(True); self.btn_none.setChecked(True)
        self.btn_yolo = QPushButton("YOLO"); self.btn_yolo.setCheckable(True)
        btn_row.addWidget(self.btn_none); btn_row.addWidget(self.btn_yolo)

        self.btn_none.clicked.connect(lambda: self.set_processor("none"))
        self.btn_yolo.clicked.connect(lambda: self.set_processor("yolo"))

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addLayout(btn_row)
        central = QWidget(); central.setLayout(layout)
        self.setCentralWidget(central)

        # Caméra & timer
        self.camera: Optional[Camera] = None
        self._init_camera()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self._apply_timer_interval()

        # Processor
        self.current_processor = None
        self.current_mode = "none"

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

    # --- Processor ---
    def set_processor(self, mode: str):
        if self.current_processor:
            try:
                self.current_processor.close()
            except Exception:
                self.log.exception("close() processor")
            self.current_processor = None

        self.btn_none.setChecked(mode == "none")
        self.btn_yolo.setChecked(mode == "yolo")

        if mode == "yolo":
            try:
                eng_cfg = dict(self.settings.get("engines", {}).get("yolo", {}))
                self.current_processor = HandYolo(name="HandYolo", config=self.settings, **eng_cfg)
            except Exception:
                self.log.exception("Init HandYolo échouée")
                mode = "none"

        self.current_mode = mode
        self.log.info("Mode actif: %s", mode)

    # --- Affichage ---
    def update_frame(self):
        if not self.camera:
            return
        frame = self.camera.get_frame()
        if frame is None:
            return
        if self.current_processor:
            try:
                frame = self.current_processor.process_frame(frame)
            except Exception:
                self.log.exception("Erreur YOLO")
        qimg = self._to_qimage(frame)
        if qimg:
            self.video_label.setPixmap(QPixmap.fromImage(qimg))

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
