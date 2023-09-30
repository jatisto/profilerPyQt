import threading
from re import sub

from PySide2.QtCore import (Qt, QTimer, QUrl)
from PySide2.QtGui import (QIcon, QDesktopServices, QPainter, QColor, QPalette)
from PySide2.QtWidgets import *

import Constants
from Bar import Bar
from UiTheme import UiTheme
from database import DatabaseManager
from settings import ConnectionSettings
from sql_highlighter import SQLHighlighter
from update_version import Updater
from utility_function import handle_errors, Log

updater = Updater()
version_app = updater.get_remote_version()


@handle_errors(log_file="ui.log", text='QueryApp')
class QueryApp(QMainWindow, UiTheme):

    def __init__(self):
        super().__init__()
        self.btn_check_updates = None
        self.btn_update = None
        self.btn_execute_top_20_query = None
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
        self.setGeometry(100, 100, 1200, 800)

        self.db_connection = None
        self.dark_theme_enabled = False

        self.default_dbname = None
        self.default_host = None
        self.default_port = None
        self.default_username = None
        self.default_password = None
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Получение палитры окна
        palette = self.palette()

        # Установка цветов
        palette.setColor(QPalette.WindowText, palette.color(QPalette.Active, QPalette.WindowText))
        palette.setColor(QPalette.Window, palette.color(QPalette.Active, QPalette.Window))

        self.load_default_connection_settings()
        self.init_ui()

        self.load_connection_settings()
        self.connect_to_db()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(255, 0, 0))  # Установка желаемого цвета (в данном случае - красный)
        painter.drawRect(0, 0, self.width(), 30)  # Рисование прямоугольника с заданными координатами и размерами

    def delayed_check_for_updates(self):
        """
        Выполняет отложенную проверку наличия обновлений приложения.
        :return: None
        """
        self.check_for_updates()

    def showEvent(self, event):
        """
        Обрабатывает событие отображения главного окна.

        :param event: Событие отображения окна.
        :type event: QShowEvent
        :return: None
        """
        super().showEvent(event)
        QTimer.singleShot(500, self.delayed_check_for_updates)

    def init_ui(self):
        """
        Инициализирует элементы пользовательского интерфейса.

        :return: None
        """
        layout = QVBoxLayout()
        UiTheme.set_dark_theme(self)
        version_app_value = version_app.replace("\n", "")
        title_text = f"Интерфейс для работы с pg_stat_statements v{version_app_value}"
        bar = Bar(self, title_text)
        self.setMenuWidget(bar)
        self.q_system_tray_icon_build()
        self.setting_input_fields()

        # Поле поиска
        self.line_edit_search = QLineEdit(self)
        self.line_edit_search.setPlaceholderText("Найти")
        self.line_edit_search.setFixedWidth(300)
        self.line_edit_search.setToolTip(
            "[Ctrl+F] - Поиск происходит динамически при вводе текста\n")

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
        self.table_widget_results.setColumnCount(10)

        self.table_widget_results.setHorizontalHeaderLabels(Constants.table_columns_default())
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

        self.btn_execute_top_20_query = QPushButton("TOP 20", self)
        self.btn_execute_top_20_query.clicked.connect(self.execute_top_20_query)
        self.btn_execute_top_20_query.setObjectName("btn_execute_top_20_query")

        UiTheme.set_icon_and_tooltip(self.btn_execute_top_20_query, "icons/rocket_32.ico",
                                     f"[Ctrl+Shift+Alt+Enter] - Запрос показывает 20 запросов, занимающих много времени:\n"
                                     f"\n-- Последний столбец особенно примечателен: он показывает процент общего времени, потраченного на один запрос."
                                     f"\n-- Это поможет вам выяснить, насколько влияет запрос на общую производительность или не влияет.")

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

        self.btn_check_updates = QPushButton(self, "", self.layout)
        self.btn_check_updates.clicked.connect(self.check_for_updates)
        self.btn_check_updates.setVisible(True)
        self.btn_check_updates.setObjectName("btn_check_updates")

        UiTheme.set_icon_and_tooltip(self.btn_check_updates, "icons/update_check.ico",
                                     f"Проверьте наличие обновлений")

        self.btn_update = QPushButton(self, self.layout)
        self.btn_update.clicked.connect(self.loading_file)
        self.btn_update.setObjectName("btn_update")
        self.btn_update.setText("Скачать")

        UiTheme.set_icon_and_tooltip(self.btn_update, "icons/update.ico",
                                     f"Скачать")

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
        btn_layout.addWidget(self.btn_execute_top_20_query)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_execute_query)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(separator)
        btn_layout.addWidget(self.btn_check_updates)
        btn_layout.addWidget(self.btn_update)
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
        """
            Создает поля ввода для настроек подключения к базе данных.

            :return: None
        """

        self.line_edit_host = QLineEdit(self, self.layout)
        self.line_edit_host.setPlaceholderText("Хост")
        self.line_edit_host.setText(self.default_host)
        self.line_edit_port = QLineEdit(self, self.layout)
        self.line_edit_port.setPlaceholderText("Порт")
        self.line_edit_port.setText(self.default_port)
        self.line_edit_username = QLineEdit(self, self.layout)
        self.line_edit_username.setPlaceholderText("Пользователь")
        self.line_edit_username.setText(self.default_username)
        self.line_edit_password = QLineEdit(self, self.layout)
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
        """
        Создает и настраивает системный трей и его иконку.

        :return: None
        """

        icon_path = "icons/icon.ico"
        self.setWindowIcon(QIcon(icon_path))
        # Создание системного трея
        self.tray_icon = QSystemTrayIcon(self, self.layout)
        self.tray_icon.setIcon(QIcon(icon_path))
        # Установка контекстного меню для трея
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        # Отображение иконки в трее
        self.tray_icon.show()

    def execute_query_shortcut(self):
        """
        Выполняет запрос при нажатии сочетания клавиш (сокращение).

        :return: None
        """

        if self.btn_execute_query.isEnabled():
            self.execute_query()

    def reset_stats_shortcut(self):
        """
            Сбрасывает статистику при нажатии сочетания клавиш (сокращение).

            :return: None
        """

        if self.btn_reset_stats.isEnabled():
            self.reset_stats()

    def save_settings_shortcut(self):
        """
        Сохраняет настройки подключения при нажатии сочетания клавиш (сокращение).

        :return: None
        """

        if self.btn_save_settings.isEnabled():
            self.save_connection_settings()

    def keyPressEvent(self, event):
        """
            Обрабатывает события нажатия клавиш, включая горячие клавиши для выполнения запросов,
            сброса статистики и сохранения настроек.

            :param event: Событие нажатия клавиши.
            :type event: QKeyEvent
            :return: None
        """

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
        elif event.modifiers() == (
                Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier) and event.key() == Qt.Key_Return:
            self.execute_top_20_query()
        elif event.key() == Qt.Key_Escape:
            self.combo_dbname.clearFocus()
        super().keyPressEvent(event)

    def reset_stats(self):
        """
        Сбрасывает статистику в базе данных.

        :return: None
        """

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
        """
        Сбрасывает статистику PostgreSQL.

        :return: None
        """

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
        """
        Устанавливает соединение с базой данных на основе введенных пользователем параметров.

        :return: None
        """

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
        """
        Отключается от базы данных.

        :return: None
        """

        if self.db_connection:
            self.db_connection.disconnect()
            self.db_connection = None
            self.statusBar().showMessage("Подключение прервано")
            self.btn_disconnect.setEnabled(False)

    def execute_query(self):
        """
        Выполняет запрос к базе данных.

        :return: None
        """

        query = Constants.get_execute_query(self.combo_dbname.currentText())
        columns = Constants.table_columns_default()
        results = self.execute_query_base(query, columns)
        if results is not None:
            self.display_results(results)

    def search_query(self):
        """
        Выполняет поисковый запрос к базе данных.

        :return: None
        """

        querySearch = Constants.get_search_query(self.combo_dbname.currentText(), self.line_edit_search.text())
        columns = Constants.table_columns_default()  # Используйте соответствующий список колонок
        results = self.execute_query_base(querySearch, columns)
        if results is not None:
            self.display_results(results)

    def execute_custom_query(self):
        """
        Запрос для получения количества удалённых, обновлённых и изменённых записей в таблицах.

        :return: None
        """

        self.reconnect_to_db()
        table_names = self.get_table_names()
        at_least_one_non_empty = any(name and name.strip() for name in table_names)
        if not at_least_one_non_empty:
            self.show_error_message(self, "Ошибка", "Все имена таблиц пусты")
            return

        query_template = Constants.pg_stat_user_tables_query()
        query = query_template.format(", ".join(["'{}'".format(name) for name in table_names]))
        columns = Constants.table_columns_ins_upt_del()  # Используйте соответствующий список колонок
        results = self.execute_query_base(query, columns)
        if results is not None:
            self.display_results(results, False)

    def execute_top_20_query(self):
        """
         Запрос для получения топ-20 самых тяжелых запросов.

         :return: None
         """

        query = Constants.get_20_top_query(self.combo_dbname.currentText())
        columns = Constants.top_20_query()  # Используйте соответствующий список колонок
        results = self.execute_query_base(query, columns)
        if results is not None:
            self.display_results(results, False)

    def execute_query_base(self, query, columns):
        """
        Выполняет запрос к базе данных и возвращает результаты.

        :param query: SQL-запрос к базе данных.
        :type query: str
        :param columns: Список столбцов для отображения результатов.
        :type columns: list
        :return: Результаты выполнения запроса.
        :rtype: list
        """

        if not self.is_not_setting:
            self.show_error_message(self, "Ошибка", "Данные для подключения отсутствует.")
            return None

        self.table_widget_results.setHorizontalHeaderLabels(columns)

        if not self.db_connection:
            self.statusBar().showMessage("Не установлено соединение с БД.")
            return None

        try:
            with self.db_connection:
                results = self.db_connection.run_execute_query(query)
                self.statusBar().showMessage("Запрос выполнен успешно.")
                return results
        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения запроса: {e}")
            self.show_error_message(self, "Ошибка выполнения запроса", e)
            Log.info(f"Ошибка выполнения запроса: {e}")
            return None

    def execute_selected_query(self):
        """
        Выполняет выбранный запрос.

        :return: None
        """

        if self.use_custom_query:
            self.execute_custom_query()
        else:
            self.execute_query()

    def get_table_names(self):
        """
        Извлекает имена таблиц из ввода пользователя.

        :return: Список имен таблиц.
        :rtype: list
        """

        input_text = self.text_edit_full_query.toPlainText()
        input_text = input_text.replace("'", "")
        table_names = input_text.split(',')
        table_names = [name.strip() for name in table_names]
        return table_names

    @staticmethod
    def removing_line_breaks(results):
        """
        Изменяет форматирование результатов запроса.

        :param results: Результаты запроса.
        :type results: list
        :return: Результаты с измененным форматированием.
        :rtype: list
        """

        def replace_line_breaks(text):
            # Заменяем переносы строк и табуляции на пробелы
            return sub(r"[\n\t]+", " ", text)

        results = [list(row) for row in results]
        for row in results:
            row[0] = replace_line_breaks(row[0])
        results = [tuple(row) for row in results]
        return results

    def display_results(self, results, is_set_length_columns=True):
        """
            Отображает результаты запроса в виде таблицы.

            :param results: Результаты запроса.
            :type results: list
            :param is_set_length_columns: Устанавливать ли ширину столбцов автоматически.
            :type is_set_length_columns: bool
            :param length_two_columns: Ширина первых двух столбцов.
            :type length_two_columns: int
            :return: None
        """

        self.table_widget_results.clearContents()
        self.table_widget_results.setRowCount(len(results))
        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table_widget_results.setItem(row_idx, col_idx, item)

        if is_set_length_columns:
            # Установите ширину первых двух столбцов на 1/3 ширины таблицы.
            table_width = self.table_widget_results.viewport().size().width()
            self.table_widget_results.setColumnWidth(0, table_width // 2)

        # Установите ширину остальных столбцов на основе наименований.
        for col_idx in range(1, self.table_widget_results.columnCount()):
            self.table_widget_results.resizeColumnToContents(col_idx)

    def resizeEvent(self, event):
        """
        Обрабатывает событие изменения размера окна.

        :param event: Событие изменения размера окна.
        :type event: QResizeEvent
        :return: None
        """

        self.table_widget_results.horizontalHeader().setStretchLastSection(True)

    def view_full_query(self, row, column, is_modal=False):
        """
        Отображает полный текст запроса.

        :param row: Индекс строки в таблице результатов.
        :type row: int
        :param column: Индекс столбца в таблице результатов.
        :type column: int
        :param is_modal: Отображать ли в модальном режиме.
        :type is_modal: bool
        :return: None
        """

        try:
            if column == 0 or column == 1:
                query = self.table_widget_results.item(row, column).text()

                # Установите текст в виджете QTextEdit
                self.text_edit_full_query.setPlainText(query)
                if is_modal:
                    pass

        except Exception as e:
            self.statusBar().showMessage(f"Ошибка выполнения поиска: {e}")
            Log.info(f"{e}")

    def load_default_connection_settings(self):
        """
        Загружает настройки подключения по умолчанию.

        :return: None
        """

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
        """
        Загружает настройки подключения из сохраненных данных.

        :return: None
        """

        databases = ConnectionSettings.load()
        self.combo_dbname.addItems(databases)
        self.combo_dbname.setCurrentText(self.default_dbname)

    def save_connection_settings(self):
        """
        Сохраняет текущие настройки подключения.

        :return: None
        """

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
            Log.info(f"Ошибка при сохранении настроек")

    def on_database_changed(self, index):
        """
        Обновляет настройки подключения при изменении выбранной базы данных.

        :param index: Индекс выбранной базы данных.
        :type index: int
        :return: None
        """

        selected_db = self.combo_dbname.currentText()
        settings = ConnectionSettings.load_all_settings()

        actual_settings = [setting for setting in settings if setting["dbname"] == selected_db]

        self.line_edit_host.setText(actual_settings[0]["host"])
        self.line_edit_port.setText(actual_settings[0]["port"])
        self.line_edit_username.setText(actual_settings[0]["username"])
        self.line_edit_password.setText(actual_settings[0]["password"])

        self.clear_table_results()
        self.connect_to_db()

    def clear_table_results(self):
        """
        Очищает таблицу с результатами запросов.

        :return: None
        """

        self.table_widget_results.clearContents()
        self.table_widget_results.setRowCount(0)

    def tray_icon_clicked(self, reason):
        """
        Обрабатывает события клика по иконке в системном трее.

        :param reason: Причина события клика.
        :type reason: QSystemTrayIcon.ActivationReason
        :return: None
        """

        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        """
        Обрабатывает событие закрытия приложения.

        :param event: Событие закрытия приложения.
        :type event: QCloseEvent
        :return: None
        """

        QApplication.quit()
        event.accept()

    def reconnect_to_db(self):
        """
        Переподключается к базе данных с текущими настройками.

        :return: None
        """

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
        """
        Отображает окно с сообщением об ошибке.

        :param title: Заголовок окна.
        :type title: str
        :param message: Текст сообщения об ошибке.
        :type message: str
        :return: None
        """

        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.exec_()

    def check_for_updates(self):
        """
        Проверяет наличие обновлений приложения.

        :return: None
        """

        update_available, local_version = updater.check_update()

        if update_available:
            self.btn_update.setVisible(True)
            self.btn_check_updates.setVisible(False)

    def update_application(self):
        """
        Инициирует процесс обновления приложения.

        :return: None
        """

        threading.Thread(target=self.run_update_async).start()
        self.close()

    def loading_file(self):
        """
        Открывает ссылку для загрузки файла.

        :return: None
        """

        QDesktopServices.openUrl(QUrl(updater.get_download_link()))
        QTimer.singleShot(200, lambda: self.btn_update.setVisible(False))

    def update_application_auto(self):
        """
        Автоматически предлагает обновление приложения.

        :return: None
        """

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
        """
        Запуск обновления в асинхронном режиме

        :return: None
        """

        updater.run_update()
