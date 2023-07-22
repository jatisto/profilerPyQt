import re
from aifc import Error

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, \
    QLineEdit, QComboBox, QDialog, QTextEdit, QFrame, QAction, QApplication, QSystemTrayIcon, QMenu, QHeaderView, \
    QSpacerItem, QSizePolicy

import Constants
from database import DatabaseManager
from settings import ConnectionSettings
from sql_highlighter import SQLHighlighter
from utility_function import handle_errors, write_log


def set_button_color(button, color, text_color='color: white;', font_family='MesloLGS NF'):
    button.setStyleSheet(f"background-color: {color.name()};{text_color};font-family:{font_family}")


@handle_errors(log_file="ui.log", text='QueryApp')
class QueryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.highlighter = None
        self.text_edit_full_query = None
        self.btn_execute_custom_query = None
        self.table_widget_results = None
        self.line_edit_search = None
        self.line_edit_port = None
        self.line_edit_username = None
        self.line_edit_password = None
        self.combo_dbname = None
        self.btn_connect = None
        self.btn_disconnect = None
        self.btn_execute_query = None
        self.btn_reset_stats = None
        self.btn_save_settings = None
        self.action_save_settings = None
        self.action_reset_stats = None
        self.action_execute_query = None
        self.line_edit_host = None
        self.layout = None
        self.exit_action = None
        self.show_action = None
        self.tray_menu = None
        self.tray_icon = None
        self.setWindowTitle("Query Viewer")
        self.setGeometry(100, 100, 1200, 800)

        self.db_connection = None
        self.dark_theme_enabled = False
        self.default_dbname = "absolutBank_dev2_Actual"
        self.default_host = "localhost"
        self.default_port = "5432"
        self.default_username = "postgres"
        self.default_password = "123456"

        self.init_ui()
        self.load_connection_settings()
        self.connect_to_db()

    def init_ui(self):
        layout = QVBoxLayout()
        self.set_dark_theme(self.dark_theme_enabled)

        icon_path = "icons/icon.ico"
        self.setWindowIcon(QIcon(icon_path))

        # Создание системного трея
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon_path))

        # Создание контекстного меню для трея
        self.tray_menu = QMenu(self)
        self.show_action = QAction("Показать окно", self)
        self.exit_action = QAction("Выход", self)
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.exit_action)

        # Установка контекстного меню для трея
        self.tray_icon.setContextMenu(self.tray_menu)

        # Показать/скрыть главное окно приложения при нажатии на иконку в трее
        self.show_action.triggered.connect(self.show)
        self.tray_icon.activated.connect(self.tray_icon_clicked)

        # Отображение иконки в трее
        self.tray_icon.show()  # Добавьте эту строку

        # Поля для настроек подключения
        self.line_edit_host = QLineEdit(self)
        self.line_edit_host.setPlaceholderText("HOST")
        self.line_edit_host.setText(self.default_host)

        self.line_edit_port = QLineEdit(self)
        self.line_edit_port.setPlaceholderText("PORT")
        self.line_edit_port.setText(self.default_port)

        self.line_edit_username = QLineEdit(self)
        self.line_edit_username.setPlaceholderText("USER NAME")
        self.line_edit_username.setText(self.default_username)

        self.line_edit_password = QLineEdit(self)
        self.line_edit_password.setPlaceholderText("PASSWORD")
        self.line_edit_password.setEchoMode(QLineEdit.Password)
        self.line_edit_password.setText(self.default_password)

        # Combo box for database selection
        self.combo_dbname = QComboBox(self)
        self.combo_dbname.setEditable(True)
        self.combo_dbname.setPlaceholderText("DATABASE NAME")
        self.combo_dbname.setCurrentText(self.default_dbname)
        self.combo_dbname.currentIndexChanged.connect(self.on_database_changed)

        # Search field
        self.line_edit_search = QLineEdit(self)
        self.line_edit_search.setPlaceholderText("SEARCH BY QUERY")

        # Add a frame to enhance the visual appearance of the search field
        search_frame = QFrame(self)
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setFrameShadow(QFrame.Raised)

        search_layout = QHBoxLayout(search_frame)
        search_layout.addWidget(self.line_edit_search, 1)
        search_layout.setContentsMargins(5, 5, 5, 5)

        # Initialize the table widget for displaying query results
        layout.addWidget(self.combo_dbname)

        # Table widget for data display
        self.table_widget_results = QTableWidget(self)
        self.table_widget_results.setColumnCount(5)

        self.table_widget_results.setHorizontalHeaderLabels(
            ["QUERY", "ROWS", "CALLS", "QUERY_START", "BACKEND_START"]
        )
        self.table_widget_results.setSortingEnabled(True)
        # self.table_widget_results.cellDoubleClicked.connect(self.view_full_query)
        self.table_widget_results.cellClicked.connect(self.view_full_query)

        layout.addWidget(self.table_widget_results)

        self.setLayout(layout)

        # Кнопки для подключения и отключения от базы данных
        self.btn_connect = QPushButton("CONNECT", self)
        self.btn_connect.clicked.connect(self.connect_to_db)

        self.btn_disconnect = QPushButton("TERMINATE CONNECTION", self)
        self.btn_disconnect.clicked.connect(self.disconnect_from_db)
        self.btn_disconnect.setEnabled(False)

        # Кнопки для выполнения запросов и сброса статистики
        self.btn_execute_query = QPushButton("PERFORM REQUEST", self)
        self.btn_execute_query.clicked.connect(self.execute_query)

        # Кнопки для выполнения запросов и сброса статистики
        self.btn_execute_query_opr = QPushButton("GET_INS_UPD_DEL", self)
        self.btn_execute_query_opr.clicked.connect(self.execute_custom_query)

        self.btn_reset_stats = QPushButton("PG_STAT_STATEMENTS_RESET", self)
        self.btn_reset_stats.clicked.connect(self.reset_stats)

        self.btn_pg_stat_reset = QPushButton("PG_STAT_RESET", self)
        self.btn_pg_stat_reset.clicked.connect(self.pg_stat_reset)

        self.btn_reconnect_to_db = QPushButton("RECONNECT_TO_DB", self)
        self.btn_reconnect_to_db.clicked.connect(self.reconnect_to_db)

        # Кнопка сохранения настроек
        self.btn_save_settings = QPushButton("SAVE SETTING", self)
        self.btn_save_settings.clicked.connect(self.save_connection_settings)

        self.setFocusPolicy(Qt.StrongFocus)

        # Main layout
        self.layout = QVBoxLayout()

        # Внешний вид настроек подключения
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.line_edit_host)
        settings_layout.addWidget(self.line_edit_port)
        settings_layout.addWidget(self.line_edit_username)
        settings_layout.addWidget(self.line_edit_password)
        settings_layout.addWidget(self.combo_dbname)

        set_button_color(self.btn_disconnect, QColor(204, 36, 29))  # Red
        set_button_color(self.btn_connect, QColor(152, 195, 121), "color: black;")  # Green
        set_button_color(self.btn_save_settings, QColor(97, 175, 239), "color: black;")  # Blue

        settings_layout.addWidget(self.btn_connect)
        settings_layout.addWidget(self.btn_disconnect)
        settings_layout.addWidget(self.btn_save_settings)

        settings_widget = QWidget()
        settings_widget.setLayout(settings_layout)

        self.layout.addWidget(settings_widget)

        # Добавить поисковую рамку в макет
        self.layout.addWidget(search_frame, alignment=Qt.AlignCenter)

        # Макет таблицы
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table_widget_results)

        self.layout.addLayout(table_layout)

        # Set colors using the set_button_color function
        set_button_color(self.btn_reconnect_to_db, QColor(204, 36, 29))  # Red
        set_button_color(self.btn_execute_query, QColor(152, 195, 121), "color: black;")  # Green
        set_button_color(self.btn_reset_stats, QColor(97, 175, 239), "color: black;")  # Blue
        set_button_color(self.btn_pg_stat_reset, QColor(97, 175, 239), "color: black;")  # Blue
        set_button_color(self.btn_execute_query_opr, QColor(97, 175, 239), "color: black;")  # Blue

        # Отрегулируйте расположение кнопок для лучшего использования пространства
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_reconnect_to_db)
        btn_layout.addWidget(self.btn_reset_stats)
        btn_layout.addWidget(self.btn_pg_stat_reset)
        btn_layout.addWidget(self.btn_execute_query_opr)
        btn_layout.addWidget(self.btn_execute_query)
        btn_layout.addStretch()

        # Inside the init_ui method, modify the creation of the QTextEdit widget to make it editable.
        self.text_edit_full_query = QTextEdit(self)
        self.text_edit_full_query.setFontFamily("JetBrains Mono")
        self.text_edit_full_query.setPlaceholderText("Введите ваш пользовательский запрос")
        self.layout.addWidget(self.text_edit_full_query)

        # Apply syntax highlighting with the SQLHighlighter
        highlighter = SQLHighlighter(self.text_edit_full_query.document())

        self.layout.addLayout(btn_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.layout.addWidget(self.text_edit_full_query)

        self.line_edit_search.textChanged.connect(self.search_query)
        # Подключите сигнал currentCellChanged к методу view_full_query.
        self.table_widget_results.currentCellChanged.connect(self.view_full_query)
        # self.btn_execute_query_opr.clicked.connect(self.execute_custom_query)
        # Assign the highlighter instance to the member variable for later access
        self.highlighter = highlighter

    def set_dark_theme(self, enabled):
        self.dark_theme_enabled = enabled
        if enabled:
            theme = "OneDarkVividItalic"
            try:
                with open("themes/{}.qss".format(theme), "r") as theme_file:
                    self.setStyleSheet(theme_file.read())
            except:
                print("Error: Couldn't open the file.")
        else:
            self.setStyleSheet("")

    def execute_query_shortcut(self):
        if self.btn_execute_query.isEnabled():
            self.execute_query()

    def reset_stats_shortcut(self):
        if self.btn_reset_stats.isEnabled():
            self.reset_stats()

    def save_settings_shortcut(self):
        if self.btn_save_settings.isEnabled():
            self.save_connection_settings()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self.line_edit_search.setFocus()
        elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Return:
            selected_row = self.table_widget_results.currentRow()
            selected_column = self.table_widget_results.currentColumn()
            if selected_column == 0:
                self.view_full_query(selected_row, selected_column)
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q:
            QApplication.quit()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Return:
            self.execute_query_shortcut()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_R:
            self.reset_stats_shortcut()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save_settings_shortcut()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_L:
            self.combo_dbname.setFocus()
        elif event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_Return:
            self.execute_custom_query()
        elif event.key() == Qt.Key_Escape:
            self.combo_dbname.clearFocus()
        super().keyPressEvent(event)

    def reset_stats(self):
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = "SELECT pg_stat_statements_reset();"
        try:
            results = self.db_connection.execute_query(query)
            self.display_results(results)
            self.statusBar().showMessage("Сброс статистики прошёл успешно.")
            self.reconnect_to_db()
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")

    def pg_stat_reset(self):
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = "SELECT pg_stat_reset();"
        try:
            results = self.db_connection.execute_query(query)
            self.display_results(results)
            self.statusBar().showMessage("Сброс статистики прошёл успешно.")
            self.reconnect_to_db()
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")

    def connect_to_db(self):
        dbname = self.combo_dbname.currentText()
        host = self.line_edit_host.text()
        port = self.line_edit_port.text()
        username = self.line_edit_username.text()
        password = self.line_edit_password.text()

        self.db_connection = DatabaseManager(dbname, host, port, username, password)
        if self.db_connection.connect():
            self.statusBar().showMessage("Подключение успешно")
            self.btn_disconnect.setEnabled(True)
        else:
            self.statusBar().showMessage("Ошибка подключения")

    def disconnect_from_db(self):
        if self.db_connection:
            self.db_connection.disconnect()
            self.db_connection = None
            self.statusBar().showMessage("Подключение прервано")
            self.btn_disconnect.setEnabled(False)

    def execute_query(self):
        column = Constants.table_columns_default()
        self.table_widget_results.setHorizontalHeaderLabels(column)

        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = Constants.get_execute_query(self.combo_dbname.currentText())

        try:
            results = self.db_connection.execute_query(query)
            self.display_results(results)
            self.statusBar().showMessage("Запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")
            write_log(f"Ошибка выполнения запроса: {e}")

    def search_query(self):
        self.table_widget_results.setHorizontalHeaderLabels(Constants.table_columns_default())
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = Constants.get_search_query(self.combo_dbname.currentText(), self.line_edit_search.text())

        try:
            results = self.db_connection.execute_query(query)
            self.display_results(results)
            self.statusBar().showMessage("Поиск выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения поиска: {e}")
            write_log(f"Ошибка выполнения запроса: {e}")

    def execute_custom_query(self):
        self.reconnect_to_db()
        self.table_widget_results.setHorizontalHeaderLabels(Constants.table_columns_ins_upt_del())
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        table_names = self.get_table_names()
        query_template = Constants.pg_stat_user_tables_query()
        query = query_template.format(", ".join(["'{}'".format(name) for name in table_names]))

        try:
            results = self.db_connection.execute_query(query)
            self.display_results(results)
            self.statusBar().showMessage("Пользовательский запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения пользовательского запроса: {e}")
            write_log(f"Ошибка выполнения пользовательского запроса: {e}")

    def execute_selected_query(self):
        if self.use_custom_query:
            self.execute_custom_query()
        else:
            self.execute_query()

    def get_table_names(self):
        input_text = self.text_edit_full_query.toPlainText()
        input_text = input_text.replace("'", "")
        table_names = input_text.split(',')
        table_names = [name.strip() for name in table_names]
        return table_names

    @staticmethod
    def removing_line_breaks(results):
        def replace_line_breaks(text):
            # Заменяем переносы строк и табуляции на пробелы
            return re.sub(r"[\n\t]+", " ", text)

        results = [list(row) for row in results]
        for row in results:
            row[0] = replace_line_breaks(row[0])
        results = [tuple(row) for row in results]
        return results

    def display_results(self, results):
        # Отобразить результаты в таблице
        self.table_widget_results.clearContents()
        self.table_widget_results.setRowCount(len(results))

        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table_widget_results.setItem(row_idx, col_idx, item)

        # Установите ширину столбца «pg.query», чтобы он занимал 1/3 ширины таблицы.
        table_width = self.table_widget_results.viewport().size().width()
        self.table_widget_results.setColumnWidth(0, table_width // 2)

    def resizeEvent(self, event):
        # Изменение размера таблицы при изменении размера окна
        self.table_widget_results.horizontalHeader().setStretchLastSection(True)

    def view_full_query(self, row, column):
        try:
            if column == 0:
                query = self.table_widget_results.item(row, column).text()

                # Установите текст в виджете QTextEdit
                self.text_edit_full_query.setPlainText(query)

        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения поиска: {e}")
            write_log(f"{e}")

    def load_connection_settings(self):
        databases = ConnectionSettings.load()
        self.combo_dbname.addItems(databases)
        self.combo_dbname.setCurrentText(self.default_dbname)

    def save_connection_settings(self):
        new_settings = {
            "setting": [
                {
                    "dbname": self.combo_dbname.currentText(),
                    "host": self.line_edit_host.text(),
                    "port": self.line_edit_port.text(),
                    "username": self.line_edit_username.text(),
                    "password": self.line_edit_password.text(),
                    "actual": True
                }
            ]
        }

        if ConnectionSettings.save(new_settings):
            self.statusBar().showMessage("Настройки успешно сохранены.")
        else:
            self.statusBar().showMessage("Ошибка при сохранении настроек.")
            write_log(f"Ошибка при сохранении настроек")

    def on_database_changed(self, index):
        selected_db = self.combo_dbname.currentText()
        self.clear_table_results()
        self.connect_to_db()

    def clear_table_results(self):
        self.table_widget_results.clearContents()
        self.table_widget_results.setRowCount(0)

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        QApplication.quit()
        event.accept()

    def show_system_menu(self, pos):
        menu = QMenu(self)
        show_action = menu.addAction("Показать окно")
        exit_action = menu.addAction("Выход")

        action = menu.exec_(pos)
        if action == show_action:
            self.show()
        elif action == exit_action:
            QApplication.quit()

    def reconnect_to_db(self):
        # Disconnect from the current database if connected
        if self.db_connection:
            self.db_connection.disconnect()
            self.db_connection = None

        # Reconnect to the database with the current connection settings
        dbname = self.combo_dbname.currentText()
        host = self.line_edit_host.text()
        port = self.line_edit_port.text()
        username = self.line_edit_username.text()
        password = self.line_edit_password.text()

        self.db_connection = DatabaseManager(dbname, host, port, username, password)
        if self.db_connection.connect():
            self.statusBar().showMessage("Подключение успешно")
            self.btn_disconnect.setEnabled(True)
        else:
            self.statusBar().showMessage("Ошибка подключения")
