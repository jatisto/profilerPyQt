"""
Main Window - Primary Application UI

Material Design main window with query results table.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
    QLabel, QProgressBar, QHeaderView, QMenu, QTextEdit,
    QSplitter, QToolBar, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from loguru import logger

from ..config import app_config
from ..models import SettingsManager, SQLQueries
from ..controllers import DatabaseController
from .workers import QueryWorker, ResetStatsWorker
from .connection_dialog import ConnectionDialog


class MainWindow(QMainWindow):
    """
    Main application window with Material Design.

    Features:
    - Database connection management
    - Query execution (all, search, top 20)
    - Statistics reset
    - SQL query viewer
    - Keyboard shortcuts
    - Status bar with connection info
    """

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        # Initialize components
        self.settings_manager = SettingsManager()
        self.settings_manager.load()

        self.controller = DatabaseController()
        self.current_worker: Optional[QueryWorker] = None

        # Data
        self.current_results: List[Dict[str, Any]] = []
        self.current_columns: List[str] = SQLQueries.COLUMNS_DEFAULT

        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_statusbar()

        # Auto-connect if have active connection
        self.auto_connect()

    def setup_ui(self):
        """Setup user interface."""
        # Window settings
        self.setWindowTitle(f"{app_config.app_name} v{app_config.app_version}")
        self.resize(app_config.window_width, app_config.window_height)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Toolbar
        self.create_toolbar()

        # Search bar
        search_layout = self.create_search_bar()
        layout.addLayout(search_layout)

        # Splitter for table and SQL viewer
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results table
        self.table_widget = self.create_results_table()
        splitter.addWidget(self.table_widget)

        # SQL viewer
        self.sql_viewer = self.create_sql_viewer()
        splitter.addWidget(self.sql_viewer)

        # Set splitter proportions (70% table, 30% SQL viewer)
        splitter.setSizes([700, 300])

        layout.addWidget(splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        layout.addWidget(self.progress_bar)

    def create_toolbar(self):
        """Create toolbar with actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Connect action
        connect_action = QAction("Подключиться", self)
        connect_action.setShortcut(QKeySequence("Ctrl+O"))
        connect_action.triggered.connect(self.show_connection_dialog)
        toolbar.addAction(connect_action)

        # Disconnect action
        self.disconnect_action = QAction("Отключиться", self)
        self.disconnect_action.setShortcut(QKeySequence("Ctrl+D"))
        self.disconnect_action.setEnabled(False)
        self.disconnect_action.triggered.connect(self.disconnect)
        toolbar.addAction(self.disconnect_action)

        toolbar.addSeparator()

        # Execute all statements
        self.execute_action = QAction("Все запросы", self)
        self.execute_action.setShortcut(QKeySequence("Ctrl+Return"))
        self.execute_action.setEnabled(False)
        self.execute_action.triggered.connect(self.execute_all_statements)
        toolbar.addAction(self.execute_action)

        # Top 20 queries
        self.top20_action = QAction("TOP 20", self)
        self.top20_action.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        self.top20_action.setEnabled(False)
        self.top20_action.triggered.connect(self.execute_top20)
        toolbar.addAction(self.top20_action)

        toolbar.addSeparator()

        # Reset statistics
        self.reset_action = QAction("Сброс статистики", self)
        self.reset_action.setShortcut(QKeySequence("Ctrl+R"))
        self.reset_action.setEnabled(False)
        self.reset_action.triggered.connect(self.reset_statements_stats)
        toolbar.addAction(self.reset_action)

        # Reset global stats
        self.reset_global_action = QAction("Сброс глобальной статистики", self)
        self.reset_global_action.setEnabled(False)
        self.reset_global_action.triggered.connect(self.reset_global_stats)
        toolbar.addAction(self.reset_global_action)

        toolbar.addSeparator()

        # About action
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

    def create_search_bar(self) -> QHBoxLayout:
        """Create search bar layout."""
        layout = QHBoxLayout()

        # Search label
        search_label = QLabel("Поиск:")
        layout.addWidget(search_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска... (Ctrl+F)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setEnabled(False)
        layout.addWidget(self.search_input, 1)

        # Search button
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.execute_search)
        self.search_btn.setEnabled(False)
        layout.addWidget(self.search_btn)

        return layout

    def create_results_table(self) -> QTableWidget:
        """Create results table."""
        table = QTableWidget()
        table.setColumnCount(len(self.current_columns))
        table.setHorizontalHeaderLabels(self.current_columns)

        # Table settings
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)

        # Header settings
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Query column
        for i in range(1, len(self.current_columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Connect selection signal
        table.itemSelectionChanged.connect(self.on_row_selected)

        return table

    def create_sql_viewer(self) -> QTextEdit:
        """Create SQL viewer."""
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setPlaceholderText("Выберите запрос в таблице для просмотра полного текста...")
        viewer.setMaximumHeight(200)

        # Monospace font for SQL
        from PySide6.QtGui import QFont
        font = QFont("Consolas", 10)
        viewer.setFont(font)

        return viewer

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Focus search
        search_shortcut = QKeySequence("Ctrl+F")
        search_action = QAction(self)
        search_action.setShortcut(search_shortcut)
        search_action.triggered.connect(lambda: self.search_input.setFocus())
        self.addAction(search_action)

        # Refresh
        refresh_shortcut = QKeySequence("F5")
        refresh_action = QAction(self)
        refresh_action.setShortcut(refresh_shortcut)
        refresh_action.triggered.connect(self.execute_all_statements)
        self.addAction(refresh_action)

    def setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Connection status
        self.connection_label = QLabel("❌ Не подключено")
        self.statusbar.addPermanentWidget(self.connection_label)

        # Results count
        self.results_label = QLabel("")
        self.statusbar.addWidget(self.results_label)

    def auto_connect(self):
        """Auto-connect if active connection exists."""
        active_conn = self.settings_manager.get_active_connection()
        if active_conn:
            logger.info("Auto-connecting to active connection")
            self.connect_to_database(active_conn)

    def show_connection_dialog(self):
        """Show connection dialog."""
        dialog = ConnectionDialog(self.settings_manager, self)
        dialog.connected.connect(self.connect_to_database)
        dialog.exec()

    def connect_to_database(self, connection):
        """Connect to database."""
        try:
            success, message = self.controller.connect(
                host=connection.host,
                port=connection.port,
                database=connection.database,
                user=connection.user,
                password=connection.password,
                ssl_mode=connection.ssl_mode
            )

            if success:
                self.on_connected()
                self.statusbar.showMessage(f"✅ {message}", 5000)
            else:
                self.statusbar.showMessage(f"❌ {message}", 10000)

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.statusbar.showMessage(f"❌ Ошибка подключения: {str(e)}", 10000)

    def disconnect(self):
        """Disconnect from database."""
        success, message = self.controller.disconnect()

        if success:
            self.on_disconnected()
            self.statusbar.showMessage(message, 3000)

    def on_connected(self):
        """Handle successful connection."""
        self.connection_label.setText(f"✅ Подключено: {self.controller.current_database}")

        # Enable actions
        self.disconnect_action.setEnabled(True)
        self.execute_action.setEnabled(True)
        self.top20_action.setEnabled(True)
        self.reset_action.setEnabled(True)
        self.reset_global_action.setEnabled(True)
        self.search_input.setEnabled(True)
        self.search_btn.setEnabled(True)

        # Execute initial query
        QTimer.singleShot(100, self.execute_all_statements)

    def on_disconnected(self):
        """Handle disconnection."""
        self.connection_label.setText("❌ Не подключено")

        # Disable actions
        self.disconnect_action.setEnabled(False)
        self.execute_action.setEnabled(False)
        self.top20_action.setEnabled(False)
        self.reset_action.setEnabled(False)
        self.reset_global_action.setEnabled(False)
        self.search_input.setEnabled(False)
        self.search_btn.setEnabled(False)

        # Clear table
        self.table_widget.setRowCount(0)
        self.sql_viewer.clear()
        self.current_results.clear()

    def execute_all_statements(self):
        """Execute query to get all statements."""
        self.execute_query('all')

    def execute_search(self):
        """Execute search query."""
        search_text = self.search_input.text().strip()

        if not search_text:
            self.execute_all_statements()
            return

        # Check for special prefixes
        search_in_activity = search_text.startswith('all_')
        if search_in_activity:
            search_text = search_text[4:]

        self.execute_query('search', search_text=search_text, search_in_activity=search_in_activity)

    def execute_top20(self):
        """Execute TOP 20 query."""
        self.current_columns = SQLQueries.COLUMNS_TOP_20
        self.table_widget.setHorizontalHeaderLabels(self.current_columns)
        self.execute_query('top20')

    def execute_query(self, query_type: str, **kwargs):
        """
        Execute database query asynchronously.

        Args:
            query_type: Type of query
            **kwargs: Additional arguments
        """
        if not self.controller.is_connected():
            self.statusbar.showMessage("❌ Не подключено к БД", 3000)
            return

        # Cancel previous worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
            self.current_worker.wait()

        # Show progress
        self.progress_bar.setVisible(True)
        self.statusbar.showMessage("Выполнение запроса...", 0)

        # Create worker
        self.current_worker = QueryWorker(self.controller, query_type, **kwargs)

        # Connect signals
        self.current_worker.progress.connect(self.progress_bar.setValue)
        self.current_worker.finished.connect(self.on_query_finished)
        self.current_worker.error.connect(self.on_query_error)

        # Start worker
        self.current_worker.start()

    def on_query_finished(self, success: bool, results: List[Dict[str, Any]], message: str):
        """Handle query finished."""
        self.progress_bar.setVisible(False)

        if success:
            self.current_results = results
            self.display_results(results)
            self.statusbar.showMessage(f"✅ {message}", 3000)
        else:
            self.statusbar.showMessage(f"❌ {message}", 10000)

    def on_query_error(self, error_msg: str):
        """Handle query error."""
        self.progress_bar.setVisible(False)
        self.statusbar.showMessage(f"❌ {error_msg}", 10000)

    def display_results(self, results: List[Dict[str, Any]]):
        """Display query results in table."""
        self.table_widget.setRowCount(0)
        self.table_widget.setRowCount(len(results))

        for row_idx, row_data in enumerate(results):
            for col_idx, col_name in enumerate(self.current_columns):
                # Get value from dict (case-insensitive)
                value = None
                for key in row_data.keys():
                    if key.lower() == col_name.lower():
                        value = row_data[key]
                        break

                # Create table item
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.table_widget.setItem(row_idx, col_idx, item)

        self.results_label.setText(f"Результатов: {len(results)}")

    def on_row_selected(self):
        """Handle row selection."""
        selected_rows = self.table_widget.selectedItems()

        if not selected_rows:
            self.sql_viewer.clear()
            return

        # Get query text from first column
        row = selected_rows[0].row()
        query_item = self.table_widget.item(row, 0)

        if query_item:
            query_text = query_item.text()
            self.sql_viewer.setPlainText(query_text)

    def on_search_changed(self, text: str):
        """Handle search text change."""
        # Auto-search on text change (debounced)
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self.execute_search)
        self._search_timer.start(500)  # 500ms debounce

    def reset_statements_stats(self):
        """Reset pg_stat_statements statistics."""
        self.reset_stats('statements')

    def reset_global_stats(self):
        """Reset global PostgreSQL statistics."""
        reply = QMessageBox.question(
            self,
            "Сброс глобальной статистики",
            "Вы уверены? Это сбросит ВСЮ статистику PostgreSQL.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_stats('global')

    def reset_stats(self, reset_type: str):
        """Reset statistics."""
        # Show progress
        self.progress_bar.setVisible(True)
        self.statusbar.showMessage("Сброс статистики...", 0)

        # Create worker
        worker = ResetStatsWorker(self.controller, reset_type)

        # Connect signals
        worker.progress.connect(self.progress_bar.setValue)
        worker.finished.connect(self.on_reset_finished)

        # Start worker
        worker.start()

    def on_reset_finished(self, success: bool, _, message: str):
        """Handle reset finished."""
        self.progress_bar.setVisible(False)

        if success:
            self.statusbar.showMessage(f"✅ {message}", 3000)
            # Refresh data
            QTimer.singleShot(500, self.execute_all_statements)
        else:
            self.statusbar.showMessage(f"❌ {message}", 10000)

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"О программе {app_config.app_short_name}",
            f"""
            <h2>{app_config.app_name}</h2>
            <p>Версия: {app_config.app_version}</p>
            <p>Лицензия: {app_config.app_license}</p>
            <br>
            <p>Современное приложение для мониторинга<br>
            производительности запросов PostgreSQL.</p>
            <br>
            <p><b>Возможности:</b></p>
            <ul>
                <li>Просмотр статистики запросов (pg_stat_statements)</li>
                <li>Поиск и фильтрация запросов</li>
                <li>TOP-20 самых тяжелых запросов</li>
                <li>Безопасное подключение с шифрованием паролей</li>
                <li>Material Design интерфейс</li>
            </ul>
            """
        )

    def closeEvent(self, event):
        """Handle window close."""
        # Stop workers
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
            self.current_worker.wait()

        # Disconnect from database
        if self.controller.is_connected():
            self.controller.disconnect()

        super().closeEvent(event)
