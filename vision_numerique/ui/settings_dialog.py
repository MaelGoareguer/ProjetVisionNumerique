from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QDialogButtonBox,
    QSpinBox, QLineEdit, QComboBox, QPushButton, QFileDialog, QGroupBox
)
from PySide6.QtCore import Signal

class SettingsDialog(QDialog):
    """Fenêtre de paramètres pour éditer settings.yaml et notifier les changements."""
    settingsChanged = Signal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self._settings = settings 

        # --- Widgets caméra ---
        cam_grp = QGroupBox("Caméra")
        cam_form = QFormLayout(cam_grp)
        self.sb_cam_index = QSpinBox(); self.sb_cam_index.setRange(0, 16)
        self.sb_width = QSpinBox(); self.sb_width.setRange(160, 7680); self.sb_width.setSingleStep(10)
        self.sb_height = QSpinBox(); self.sb_height.setRange(120, 4320); self.sb_height.setSingleStep(10)
        self.sb_fps = QSpinBox(); self.sb_fps.setRange(1, 240)

        cam = settings.get("camera", {})
        self.sb_cam_index.setValue(int(cam.get("index", 0)))
        res = cam.get("resolution", [1280, 720])
        self.sb_width.setValue(int(res[0] if len(res) > 0 else 1280))
        self.sb_height.setValue(int(res[1] if len(res) > 1 else 720))
        self.sb_fps.setValue(int(cam.get("fps", 30)))

        cam_form.addRow("Index:", self.sb_cam_index)
        cam_form.addRow("Largeur:", self.sb_width)
        cam_form.addRow("Hauteur:", self.sb_height)
        cam_form.addRow("FPS:", self.sb_fps)
        
        # --- Boutons OK/Cancel ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # --- Layout principal ---
        root = QVBoxLayout(self)
        root.addWidget(cam_grp)
        root.addWidget(buttons)

    def get_settings(self) -> dict:
        """Construit un nouveau dict settings depuis les widgets."""
        s = dict(self._settings)  # copie superficielle
        # caméra
        s["camera"] = {
            "index": int(self.sb_cam_index.value()),
            "resolution": [int(self.sb_width.value()), int(self.sb_height.value())],
            "fps": int(self.sb_fps.value()),
        }
        
        if "_settings_path" in self._settings:
            s["_settings_path"] = self._settings["_settings_path"]
        return s

    def accept(self):
        self.settingsChanged.emit(self.get_settings())
        super().accept()
