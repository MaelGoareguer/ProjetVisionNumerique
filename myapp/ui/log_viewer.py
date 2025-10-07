from __future__ import annotations
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QTextEdit,
    QDialogButtonBox, QPushButton, QFileDialog, QWidget, QHBoxLayout
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor


class LogViewerDialog(QDialog):
    def __init__(self, app_log_path: str, err_log_path: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Logs")
        self.app_log_path = app_log_path
        self.err_log_path = err_log_path

        self.tabs = QTabWidget()
        self.txt_app = QTextEdit(); self.txt_app.setReadOnly(True)
        self.txt_err = QTextEdit(); self.txt_err.setReadOnly(True)
        self.tabs.addTab(self.txt_app, "app.log")
        self.tabs.addTab(self.txt_err, "erreurs.log")

        self.btn_refresh = QPushButton("Rafraîchir")
        self.btn_refresh.clicked.connect(self.refresh)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_refresh)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).setText("Fermer")

        root = QVBoxLayout(self)
        root.addLayout(btn_row)
        root.addWidget(self.tabs)
        root.addWidget(buttons)

        # Refresh initial et toutes les 3s (léger)
        self.refresh()
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

    def _read_file(self, path: str) -> str:
        try:
            if path and os.path.isfile(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            return f"(fichier introuvable)\n{path}"
        except Exception as e:
            return f"(erreur lecture) {e}\n{path}"

    def refresh(self):
        self.txt_app.setPlainText(self._read_file(self.app_log_path))
        self.txt_err.setPlainText(self._read_file(self.err_log_path))
        # Scroll tout en bas du document c'est plus logique
        self.txt_app.moveCursor(QTextCursor.End)
        self.txt_err.moveCursor(QTextCursor.End)
