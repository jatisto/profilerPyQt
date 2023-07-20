import cProfile
import os
import sys
import logging
from utility_function import handle_errors, write_log
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui import QueryApp


def setup_logging():
    log_dir = "log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "query_viewer.log")
    logging.basicConfig(filename=log_file, level=logging.ERROR,
                        format="%(asctime)s [%(levelname)s]: %(message)s")


@handle_errors(log_file="errors.log", text='main')
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
    try:
        main()
        # cProfile.run('main()')
    except Exception as e:
        logging.exception(f"Error: {0}", e)
