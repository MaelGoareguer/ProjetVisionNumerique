from __future__ import annotations
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aide")
        layout = QVBoxLayout(self)
        help_text = """<b>Utilisation:</b><br>
        • Sélectionnez le mode <b>MediaPipe</b> pour activer la détection des mains<br>
        • <b>Gestes reconnus:</b><br>
        &nbsp;&nbsp;Main plate = PLAY/PAUSE (toggle selon l'état actuel)<br>
        &nbsp;&nbsp;Index vers la droite = AVANCER<br>
        &nbsp;&nbsp;Index vers la gauche = RECULER<br>
        • <b>Touches clavier:</b> Espace=PLAY/PAUSE, →=AVANCER, ←=RECULER<br>
        • Consultez les métriques via le menu <b>Métriques</b> pour voir les performances"""
        layout.addWidget(QLabel(help_text))
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
