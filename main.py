import sys

from PyQt5 import QtWidgets

from ui import QueryApp
from utility_function import handle_errors


@handle_errors(log_file="main.log", text='main')
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = QueryApp()
    window.show()
    app.aboutToQuit.connect(handle_app_exit)
    sys.exit(app.exec_())


def handle_app_exit():
    QtWidgets.QApplication.quit()


if __name__ == "__main__":
    main()
