import os
import sys
import logging
from PyQt5 import QtWidgets

from UiTheme import UiTheme
from ui import QueryApp


def setup_logging():
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "query_viewer.log")
    logging.basicConfig(filename=log_file, level=logging.ERROR,
                        format="%(asctime)s [%(levelname)s]: %(message)s")


def main():
    app = QtWidgets.QApplication(sys.argv)
    setup_logging()
    window = QueryApp()
    window.show()
    app.aboutToQuit.connect(handle_app_exit)
    sys.exit(app.exec_())


def handle_app_exit():
    QtWidgets.QApplication.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"Error: {e}")
