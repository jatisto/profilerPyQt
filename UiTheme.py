from PySide2.QtGui import QIcon, QPixmap


class UiTheme(object):

    @staticmethod
    def set_dark_theme(main_window):
        theme = "MewMaterialDesignUi_2"
        try:
            with open("themes/{}.qss".format(theme), "r") as theme_file:
                main_window.setStyleSheet(theme_file.read())
        except Exception as err:
            print(f"Error: Couldn't open the file. {err}")

    @staticmethod
    def set_icon_and_tooltip(button, icon_path, tooltip_text):
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setToolTip(tooltip_text)

    @staticmethod
    def set_icon_and_tooltip_action(button, icon_path, tooltip_text, action_name):
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setToolTip(tooltip_text)

    @staticmethod
    def set_icon_and_tooltip_qm(widget, icon_path, tooltip):
        pixmap = QPixmap(icon_path)
        widget.setIconPixmap(pixmap)
        widget.setToolTip(tooltip)
