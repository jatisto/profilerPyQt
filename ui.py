import threading
from re import sub

from PySide2.QtCore import (Qt, QTimer)
from PySide2.QtGui import (QIcon)
from PySide2.QtWidgets import *

import Constants
from UiTheme import UiTheme
from database import DatabaseManager
from settings import ConnectionSettings
from sql_highlighter import SQLHighlighter
from update_version import Updater
from utility_function import handle_errors, write_log

updater = Updater()


@handle_errors(log_file="ui.log", text='QueryApp')
class QueryApp(QMainWindow, UiTheme):

    def __init__(self):
        super().__init__()
        self.use_custom_query = None
        self.btn_reconnect_to_db = None
        self.btn_pg_stat_reset = None
        self.btn_execute_query_opr = None
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
        self.is_not_setting = None
        self.setWindowTitle("Интерфейс для работы с pg_stat_statements")
        self.setGeometry(100, 100, 1200, 800)

        self.db_connection = None
        self.dark_theme_enabled = False

        self.default_dbname = None
        self.default_host = None
        self.default_port = None
        self.default_username = None
        self.default_password = None

        self.load_default_connection_settings()
        self.init_ui()

        self.load_connection_settings()
        self.connect_to_db()

    def delayed_check_for_updates(self):
        self.check_for_updates()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(500, self.delayed_check_for_updates)

    def init_ui(self):
        layout = QVBoxLayout()
        UiTheme.set_dark_theme(self)

        self.q_system_tray_icon_build()
        self.setting_input_fields()

        # Поле поиска
        self.line_edit_search = QLineEdit(self)
        self.line_edit_search.setPlaceholderText("Найти")
        self.line_edit_search.setFixedWidth(300)
        self.line_edit_search.setToolTip("[Ctrl+F]")

        # Добавьте рамку, чтобы улучшить внешний вид поля поиска.
        search_frame = QFrame(self)
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setFrameShadow(QFrame.Raised)

        search_layout = QHBoxLayout(search_frame)
        search_layout.addWidget(self.line_edit_search, 1)
        search_layout.setContentsMargins(5, 5, 5, 5)

        # Инициализировать виджет таблицы для отображения результатов запроса
        layout.addWidget(self.combo_dbname)

        # Виджет таблицы для отображения данных
        self.table_widget_results = QTableWidget(self)
        self.table_widget_results.setColumnCount(5)

        self.table_widget_results.setHorizontalHeaderLabels(
            ["Запрос", "Строки", "Вызовы", "Начало запроса", "Время запуска"]
        )
        self.table_widget_results.setSortingEnabled(True)
        self.table_widget_results.cellClicked.connect(self.view_full_query)

        layout.addWidget(self.table_widget_results)

        self.setLayout(layout)

        self.btn_connect = QPushButton("Подключиться", self)
        self.btn_connect.clicked.connect(self.connect_to_db)
        self.btn_connect.setObjectName("btn_connect")

        self.btn_disconnect = QPushButton("Отключиться", self)
        self.btn_disconnect.clicked.connect(self.disconnect_from_db)
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.setObjectName("btn_disconnect")

        self.btn_execute_query = QPushButton("Выполнить", self)
        self.btn_execute_query.clicked.connect(self.execute_query)
        self.btn_execute_query.setObjectName("btn_execute_query")

        UiTheme.set_icon_and_tooltip(self.btn_execute_query, "icons/rocket_32.ico",
                                     f"[Ctrl+Enter] - Выполнить")

        self.btn_pg_stat_reset = QPushButton(self)
        self.btn_pg_stat_reset.clicked.connect(self.pg_stat_reset)
        self.btn_pg_stat_reset.setObjectName("btn_pg_stat_reset")

        UiTheme.set_icon_and_tooltip(self.btn_pg_stat_reset, "icons/reset_stastic.ico",
                                     f"Сброс статистики (ins upd del) [SELECT pg_stat_reset()]")

        self.btn_execute_query_opr = QPushButton(self)
        self.btn_execute_query_opr.clicked.connect(self.execute_custom_query)
        self.btn_execute_query_opr.setObjectName("btn_execute_query_opr")

        UiTheme.set_icon_and_tooltip(self.btn_execute_query_opr, "icons/statistics.ico",
                                     f"[Ctrl+Shift+Enter] - Статистика (ins upd del) в бд")

        self.btn_reset_stats = QPushButton(self)
        self.btn_reset_stats.clicked.connect(self.reset_stats)
        self.btn_reset_stats.setObjectName("btn_reset_stats")

        UiTheme.set_icon_and_tooltip(self.btn_reset_stats, "icons/reload_reset.ico",
                                     f" [Ctrl+R] - Сбросить статистику (pg_stat_statements) [SELECT pg_stat_statements_reset()]")

        self.btn_reconnect_to_db = QPushButton("", self)
        self.btn_reconnect_to_db.clicked.connect(self.reconnect_to_db)
        self.btn_reconnect_to_db.setObjectName("btn_reconnect_to_db")

        UiTheme.set_icon_and_tooltip_action(self.btn_reconnect_to_db, "icons/refresh-db.ico",
                                            f"Переподключиться: {self.combo_dbname.currentText()}", "action_reconnect")

        self.btn_save_settings = QPushButton("Сохранить", self)
        self.btn_save_settings.clicked.connect(self.save_connection_settings)
        self.btn_save_settings.setObjectName("btn_save_settings")

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

        settings_layout.addWidget(self.btn_connect)
        settings_layout.addWidget(self.btn_disconnect)
        settings_layout.addWidget(self.btn_save_settings)

        self.btn_check_updates = QPushButton(self)
        self.btn_check_updates.clicked.connect(self.check_for_updates)
        self.btn_check_updates.setVisible(True)
        self.btn_check_updates.setObjectName("btn_check_updates")

        UiTheme.set_icon_and_tooltip(self.btn_check_updates, "icons/update_check.ico",
                                     f"Проверьте наличие обновлений")

        self.btn_update = QPushButton("Обновить", self)
        self.btn_update.clicked.connect(self.update_application)
        self.btn_update.setVisible(False)  # Hide the button initially
        self.btn_update.setObjectName("btn_update")

        UiTheme.set_icon_and_tooltip(self.btn_update, "icons/update.ico",
                                     f"Обновить")

        self.btn_update.setVisible(False)
        self.btn_check_updates.setVisible(False)

        settings_widget = QWidget(self)
        settings_widget.setLayout(settings_layout)

        self.layout.addWidget(settings_widget)

        # Добавить поисковую рамку в макет
        self.layout.addWidget(search_frame, alignment=Qt.AlignCenter)

        # Макет таблицы
        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table_widget_results)

        self.layout.addLayout(table_layout)

        separator = QFrame()
        separator.setFrameShadow(
            QFrame.Sunken)  # Выберите вид разделителя: Sunken (впавший), Raised (выпавший) или Plain (прямой)

        # Отрегулируйте расположение кнопок для лучшего использования пространства
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_reconnect_to_db)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_reset_stats)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_pg_stat_reset)
        btn_layout.addWidget(self.btn_execute_query_opr)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_check_updates)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_execute_query)
        btn_layout.addStretch()

        # Внутри метода init_ui измените создание виджета QTextEdit, чтобы сделать его редактируемым.
        self.text_edit_full_query = QTextEdit(self)
        self.text_edit_full_query.setFontFamily("JetBrains Mono")
        self.text_edit_full_query.setPlaceholderText(
            "Введите список наименований таблиц, пример: NameTable1, NameTable2 и т.д и нажмите get_ins_upd_del [Ctrl, Shift + Enter], если требуется получить количество вставленных, обновлённых или удалённых записей.")
        self.layout.addWidget(self.text_edit_full_query)

        # Применить подсветку синтаксиса с помощью SQLHighlighter
        highlighter = SQLHighlighter(self.text_edit_full_query.document())

        self.layout.addLayout(btn_layout)

        central_widget = QWidget(self)
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        self.layout.addWidget(self.text_edit_full_query)

        self.line_edit_search.textChanged.connect(self.search_query)
        # Подключите сигнал currentCellChanged к методу view_full_query.
        self.table_widget_results.currentCellChanged.connect(self.view_full_query)
        # Назначьте экземпляр маркера переменной-члену для последующего доступа
        self.highlighter = highlighter

    def setting_input_fields(self):
        # Поля для настроек подключения
        self.line_edit_host = QLineEdit(self)
        self.line_edit_host.setPlaceholderText("Хост")
        self.line_edit_host.setText(self.default_host)
        self.line_edit_port = QLineEdit(self)
        self.line_edit_port.setPlaceholderText("Порт")
        self.line_edit_port.setText(self.default_port)
        self.line_edit_username = QLineEdit(self)
        self.line_edit_username.setPlaceholderText("Пользователь")
        self.line_edit_username.setText(self.default_username)
        self.line_edit_password = QLineEdit(self)
        self.line_edit_password.setPlaceholderText("Пароль")
        self.line_edit_password.setEchoMode(QLineEdit.Password)
        self.line_edit_password.setText(self.default_password)
        # Поле со списком для выбора базы данных
        self.combo_dbname = QComboBox(self)
        self.combo_dbname.setEditable(True)
        self.combo_dbname.setPlaceholderText("База данных")
        self.combo_dbname.setCurrentText(self.default_dbname)
        self.combo_dbname.currentIndexChanged.connect(self.on_database_changed)

    def q_system_tray_icon_build(self):
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
        self.tray_icon.show()

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
            with self.db_connection:
                results = self.db_connection.run_execute_query(query)
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
            with self.db_connection:
                results = self.db_connection.run_execute_query(query)
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

        with DatabaseManager(dbname, host, port, username, password) as self.db_connection:
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
        if not self.is_not_setting:
            self.show_error_message(self, "Ошибка", "Данные для подключения отсутствует.")
            return

        column = Constants.table_columns_default()
        self.table_widget_results.setHorizontalHeaderLabels(column)

        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        query = Constants.get_execute_query(self.combo_dbname.currentText())

        try:
            with self.db_connection:
                results = self.db_connection.run_execute_query(query)
                self.display_results(results)
                self.statusBar().showMessage("Запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")
            self.show_error_message("Ошибка выполнения запроса", e)
            write_log(f"Ошибка выполнения запроса: {e}")

    def search_query(self):
        if not self.is_not_setting:
            self.show_error_message(self, "Ошибка", "Данные для подключения отсутствует.")
            return

        column = Constants.table_columns_default()
        self.table_widget_results.setHorizontalHeaderLabels(column)

        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        try:
            querySearch = Constants.get_search_query(self.combo_dbname.currentText(), self.line_edit_search.text())

            with self.db_connection:
                results = self.db_connection.run_execute_query(querySearch)
                self.display_results(results)
                self.statusBar().showMessage("Запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")
            self.show_error_message(self, "Ошибка выполнения запроса", e)
            write_log(f"Ошибка выполнения запроса: {e}")

    def execute_custom_query(self):
        if not self.is_not_setting:
            self.show_error_message(self, "Ошибка", "Данные для подключения отсутствует.")
            return

        self.reconnect_to_db()
        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return

        table_names = self.get_table_names()
        at_least_one_non_empty = any(name and name.strip() for name in table_names)

        if not at_least_one_non_empty:
            self.show_error_message(self, "Ошибка", "Все имена таблиц пусты")
            return

        self.table_widget_results.setHorizontalHeaderLabels(Constants.table_columns_ins_upt_del())

        query_template = Constants.pg_stat_user_tables_query()
        query = query_template.format(", ".join(["'{}'".format(name) for name in table_names]))

        try:
            with self.db_connection:
                results = self.db_connection.run_execute_query(query)
                self.display_results(results)
                self.statusBar().showMessage("Пользовательский запрос выполнен успешно.")
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения пользовательского запроса: {e}")
            self.show_error_message(self, "Ошибка выполнения пользовательского запроса", e)
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
            return sub(r"[\n\t]+", " ", text)

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

    def view_full_query(self, row, column, is_modal=False):
        try:
            if column == 0:
                query = self.table_widget_results.item(row, column).text()

                # Установите текст в виджете QTextEdit
                self.text_edit_full_query.setPlainText(query)
                if is_modal:
                    pass

        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения поиска: {e}")
            write_log(f"{e}")

    def load_default_connection_settings(self):
        settings = ConnectionSettings.load_all_settings()

        if len(settings) == 0:
            self.default_dbname = "postgres"
            self.default_host = "localhost"
            self.default_port = "5432"
            self.default_username = "postgres"
            self.default_password = "123456"
            self.is_not_setting = True
            return

        else:
            self.is_not_setting = True
            actual_settings = [setting for setting in settings if setting["actual"]]

            self.default_dbname = actual_settings[0]["dbname"]
            self.default_host = actual_settings[0]["host"]
            self.default_port = actual_settings[0]["port"]
            self.default_username = actual_settings[0]["username"]
            self.default_password = actual_settings[0]["password"]

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
            self.reconnect_to_db()
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

    def reconnect_to_db(self):
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

    @staticmethod
    def show_error_message(self, title, message):
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.exec_()

    def check_for_updates(self):
        update_available, version_app = updater.check_update()

        if update_available:
            self.btn_update.setVisible(True)
            self.btn_check_updates.setVisible(False)
            self.update_application()
        else:
            self.statusBar().showMessage(f"Обновление отсутствует [{version_app}]")

    def update_application(self):
        version_app = updater.get_remote_version()
        QMessageBox.information(self, "Обновление", f"Доступна новая версия: {version_app}")
        reply = QMessageBox.question(self, 'Обновить?', 'Для обновления требуется закрыть приложение.<br>'
                                                        'После обновление приложение будет запущенно заново.<br><br>'
                                                        'Вы уверенны, что хотите закрыть приложение?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            threading.Thread(target=self.run_update_async).start()
            self.close()
        else:
            self.btn_update.setVisible(False)
            self.btn_check_updates.setVisible(True)

    @staticmethod
    def run_update_async():
        updater.run_update()
