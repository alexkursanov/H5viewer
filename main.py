import logging
import sys
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName('H5 Reader')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()