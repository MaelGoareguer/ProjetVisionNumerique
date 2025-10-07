import sys
from PySide6.QtWidgets import QApplication
from myapp.utils.config import load_settings
from myapp.utils.logger import setup_logging
from myapp.ui.main_window import MainWindow

def main():
    settings = load_settings(["settings.yaml"])
    setup_logging(settings.get("logging"))

    app = QApplication(sys.argv)
    win = MainWindow(settings)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
