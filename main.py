import os
import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui import QueryApp


def setup_logging():
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "query_viewer.log")
    logging.basicConfig(filename=log_file, level=logging.ERROR,
                        format="%(asctime)s [%(levelname)s]: %(message)s")


def main():
    os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
    app = QApplication(sys.argv)

    setup_logging()
    dark_theme_enabled = True
    window = QueryApp()
    window.set_dark_theme(dark_theme_enabled)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
