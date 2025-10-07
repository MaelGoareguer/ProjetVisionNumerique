from __future__ import annotations
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aide")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Utilisation: Il vous suffit de sélectionner le mode YOLO pour activer la détection des mains."))
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
