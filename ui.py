import re

import psycopg2
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, \
    QLabel, QLineEdit, QComboBox, QDialog, QTextEdit, QFrame, QAction, QShortcut, QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt

import logging
import datetime

from database import DatabaseManager
from settings import ConnectionSettings
from utility_function import handle_errors, write_log


@handle_errors(log_file="ui.log", text='QueryApp')
class QueryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.exit_action = None
        self.show_action = None
        self.tray_menu = None
        self.tray_icon = None
        write_log(f"Start")
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


        # Fields for connection settings
        self.line_edit_host = QLineEdit(self)
        self.line_edit_host.setPlaceholderText("Хост")
        self.line_edit_host.setText(self.default_host)

        self.line_edit_port = QLineEdit(self)
        self.line_edit_port.setPlaceholderText("Порт")
        self.line_edit_port.setText(self.default_port)

        self.line_edit_username = QLineEdit(self)
        self.line_edit_username.setPlaceholderText("Имя пользователя")
        self.line_edit_username.setText(self.default_username)

        self.line_edit_password = QLineEdit(self)
        self.line_edit_password.setPlaceholderText("Пароль")
        self.line_edit_password.setEchoMode(QLineEdit.Password)
        self.line_edit_password.setText(self.default_password)

        # Combo box for database selection
        self.combo_dbname = QComboBox(self)
        self.combo_dbname.setEditable(True)
        self.combo_dbname.setPlaceholderText("Имя базы данных")
        self.combo_dbname.setCurrentText(self.default_dbname)
        self.combo_dbname.currentIndexChanged.connect(self.on_database_changed)

        # Search field
        self.line_edit_search = QLineEdit(self)
        self.line_edit_search.setPlaceholderText("Поиск по query")

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
            ["pg.query", "pg.rows", "pg.calls", "pa.query_start", "pa.backend_start"]
        )
        self.table_widget_results.setSortingEnabled(True)
        self.table_widget_results.cellDoubleClicked.connect(self.view_full_query)

        layout.addWidget(self.table_widget_results)

        self.setLayout(layout)

        # Buttons for connecting and disconnecting from the database
        self.btn_connect = QPushButton("Подключиться к БД", self)
        self.btn_connect.clicked.connect(self.connect_to_db)

        self.btn_disconnect = QPushButton("Прервать подключение", self)
        self.btn_disconnect.clicked.connect(self.disconnect_from_db)
        self.btn_disconnect.setEnabled(False)

        # Buttons for executing queries and resetting statistics
        self.btn_execute_query = QPushButton("Выполнить запрос", self)
        self.btn_execute_query.clicked.connect(self.execute_query)

        self.btn_reset_stats = QPushButton("Сбросить статистику", self)
        self.btn_reset_stats.clicked.connect(self.reset_stats)

        # Button for saving settings
        self.btn_save_settings = QPushButton("Сохранить настройки", self)
        self.btn_save_settings.clicked.connect(self.save_connection_settings)

        self.action_execute_query = QAction("Выполнить запрос", self)
        self.action_reset_stats = QAction("Сбросить статистику", self)
        self.action_save_settings = QAction("Сохранить настройки", self)

        shortcut_execute_query = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return), self)
        shortcut_reset_stats = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_R), self)
        shortcut_save_settings = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_S), self)

        shortcut_execute_query.activated.connect(self.execute_query_shortcut)
        shortcut_reset_stats.activated.connect(self.reset_stats_shortcut)
        shortcut_save_settings.activated.connect(self.save_settings_shortcut)

        self.setFocusPolicy(Qt.StrongFocus)

        # Main layout
        self.layout = QVBoxLayout()

        # Connection settings layout
        settings_layout = QHBoxLayout()
        # settings_layout.addWidget(QLabel("Connection:"))
        settings_layout.addWidget(self.line_edit_host)
        settings_layout.addWidget(self.line_edit_port)
        settings_layout.addWidget(self.line_edit_username)
        settings_layout.addWidget(self.line_edit_password)
        settings_layout.addWidget(self.combo_dbname)
        settings_layout.addWidget(self.btn_connect)
        settings_layout.addWidget(self.btn_disconnect)
        settings_layout.addWidget(self.btn_save_settings)

        settings_widget = QWidget()
        settings_widget.setLayout(settings_layout)

        self.layout.addWidget(settings_widget)

        # Add search frame to the layout
        self.layout.addWidget(search_frame, alignment=Qt.AlignCenter)

        # Table layout
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table_widget_results)

        self.layout.addLayout(table_layout)

        # Adjust button layout for better space utilization
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_execute_query)
        btn_layout.addWidget(self.btn_reset_stats)
        btn_layout.addStretch()

        self.layout.addLayout(btn_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.line_edit_search.textChanged.connect(self.search_query)

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
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_L:
            self.combo_dbname.setFocus()
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
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = "SELECT DISTINCT\n" \
                "    pg.query,\n" \
                "    pg.rows,\n" \
                "    pg.calls,\n" \
                "    pa.query_start,\n" \
                "    pa.backend_start\n" \
                "FROM pg_stat_statements pg\n" \
                "    JOIN pg_database db ON pg.dbid = db.oid\n" \
                "    JOIN pg_authid auth ON pg.userid = auth.oid\n" \
                "    JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid\n" \
                f"WHERE db.datname = '{self.combo_dbname.currentText()}'\n" \
                "ORDER BY pa.query_start DESC;"

        try:
            results = self.db_connection.execute_query(query)
            results = self.removing_line_breaks(results)
            self.display_results(results)
            self.statusBar().showMessage("Запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")
            write_log(f"Ошибка выполнения запроса: {e}")

    def search_query(self):
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = "SELECT DISTINCT\n" \
                "    pg.query,\n" \
                "    pg.rows,\n" \
                "    pg.calls,\n" \
                "    pa.query_start,\n" \
                "    pa.backend_start\n" \
                "FROM pg_stat_statements pg\n" \
                "    JOIN pg_database db ON pg.dbid = db.oid\n" \
                "    JOIN pg_authid auth ON pg.userid = auth.oid\n" \
                "    JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid\n" \
                f"WHERE db.datname = '{self.combo_dbname.currentText()}'\n" \
                f"AND pg.query LIKE '%{self.line_edit_search.text()}%'\n" \
                "ORDER BY pa.query_start DESC;"

        try:
            results = self.db_connection.execute_query(query)
            results = self.removing_line_breaks(results)
            self.display_results(results)
            self.statusBar().showMessage("Поиск выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения поиска: {e}")
            write_log(f"Ошибка выполнения запроса: {e}")

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
        # Display results in the table
        self.table_widget_results.clearContents()
        self.table_widget_results.setRowCount(len(results))

        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table_widget_results.setItem(row_idx, col_idx, item)

        # Set the width of the "pg.query" column to occupy 1/3 of the table width
        table_width = self.table_widget_results.viewport().size().width()
        self.table_widget_results.setColumnWidth(0, table_width // 2)

    def resizeEvent(self, event):
        # Resize the table on window resize
        self.table_widget_results.horizontalHeader().setStretchLastSection(True)

    def view_full_query(self, row, column):
        # View the full query on double-clicking the cell with the query
        if column == 0:
            query = self.table_widget_results.item(row, column).text()

            dialog = QDialog(self)
            dialog.setWindowTitle("Полный запрос")
            dialog.setGeometry(200, 200, 800, 600)

            layout = QVBoxLayout()

            text_edit_query = QTextEdit()
            text_edit_query.setPlainText(query)
            text_edit_query.setReadOnly(True)
            text_edit_query.setFontFamily("Courier New")
            layout.addWidget(text_edit_query)

            dialog.setLayout(layout)

            # Apply the dark theme stylesheet to the dialog
            if self.dark_theme_enabled:
                dialog.setStyleSheet(self.styleSheet())

            dialog.exec_()

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
        event.ignore()
        self.hide()
        self.show_system_menu(self.mapToGlobal(self.geometry().topRight()))

    def show_system_menu(self, pos):
        menu = QMenu(self)
        show_action = menu.addAction("Показать окно")
        exit_action = menu.addAction("Выход")

        action = menu.exec_(pos)
        if action == show_action:
            self.show()
        elif action == exit_action:
            QApplication.quit()
