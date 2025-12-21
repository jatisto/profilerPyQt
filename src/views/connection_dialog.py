"""
Connection Dialog - Database Connection UI

Material Design dialog for managing database connections.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QPushButton,
    QLabel, QProgressBar, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from loguru import logger

from ..models import SettingsManager, DatabaseConnection
from ..controllers import DatabaseController
from .workers import ConnectWorker


class ConnectionDialog(QDialog):
    """
    Material Design dialog for database connection.

    Features:
    - Save/load connection profiles
    - Password visibility toggle
    - SSL mode selection
    - Connection testing
    - Progress indicator
    """

    # Signal emitted when successfully connected
    connected = Signal(DatabaseConnection)

    def __init__(self, settings_manager: SettingsManager, parent=None):
        """
        Initialize connection dialog.

        Args:
            settings_manager: SettingsManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.controller = DatabaseController()
        self.worker: Optional[ConnectWorker] = None

        self.setup_ui()
        self.load_connections()

    def setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("Подключение к PostgreSQL")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Подключение к базе данных")
        header.setObjectName("dialogHeader")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        # Connection profile selector
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Профиль:"))

        self.profile_combo = QComboBox()
        self.profile_combo.setPlaceholderText("Выберите сохраненное подключение")
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        profile_layout.addWidget(self.profile_combo, 1)

        self.delete_profile_btn = QPushButton("Удалить")
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.delete_profile_btn.setEnabled(False)
        profile_layout.addWidget(self.delete_profile_btn)

        layout.addLayout(profile_layout)

        # Connection form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Host
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        self.host_input.setText("localhost")
        form_layout.addRow("Хост:", self.host_input)

        # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5432)
        form_layout.addRow("Порт:", self.port_input)

        # Database
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("postgres")
        self.database_input.setText("postgres")
        form_layout.addRow("База данных:", self.database_input)

        # User
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("postgres")
        self.user_input.setText("postgres")
        form_layout.addRow("Пользователь:", self.user_input)

        # Password
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        password_layout.addWidget(self.password_input, 1)

        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setMaximumWidth(40)
        self.show_password_btn.toggled.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)

        form_layout.addRow("Пароль:", password_layout)

        # SSL Mode
        self.ssl_combo = QComboBox()
        self.ssl_combo.addItems([
            "prefer", "disable", "allow", "require", "verify-ca", "verify-full"
        ])
        form_layout.addRow("SSL режим:", self.ssl_combo)

        layout.addLayout(form_layout)

        # Save connection checkbox
        self.save_connection_check = QCheckBox("Сохранить подключение")
        self.save_connection_check.setChecked(True)
        layout.addWidget(self.save_connection_check)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.test_btn = QPushButton("Тест подключения")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.connect)
        self.connect_btn.setObjectName("primaryButton")
        button_layout.addWidget(self.connect_btn)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_connections(self):
        """Load saved connections."""
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Новое подключение --", None)

        connections = self.settings_manager.get_all_connections()
        for i, conn in enumerate(connections):
            display_text = conn.name or f"{conn.user}@{conn.host}:{conn.port}/{conn.database}"
            self.profile_combo.addItem(display_text, i)

        # Select active connection if exists
        active_conn = self.settings_manager.get_active_connection()
        if active_conn:
            for i in range(1, self.profile_combo.count()):
                idx = self.profile_combo.itemData(i)
                if idx is not None and connections[idx] == active_conn:
                    self.profile_combo.setCurrentIndex(i)
                    break

    def on_profile_selected(self, index: int):
        """Handle profile selection."""
        conn_idx = self.profile_combo.itemData(index)

        if conn_idx is None:
            # New connection - clear fields
            self.host_input.clear()
            self.port_input.setValue(5432)
            self.database_input.clear()
            self.user_input.clear()
            self.password_input.clear()
            self.ssl_combo.setCurrentText("prefer")
            self.delete_profile_btn.setEnabled(False)
        else:
            # Load connection
            connections = self.settings_manager.get_all_connections()
            if 0 <= conn_idx < len(connections):
                conn = connections[conn_idx]
                self.host_input.setText(conn.host)
                self.port_input.setValue(conn.port)
                self.database_input.setText(conn.database)
                self.user_input.setText(conn.user)
                self.password_input.setText(conn.password)
                self.ssl_combo.setCurrentText(conn.ssl_mode)
                self.delete_profile_btn.setEnabled(True)

    def delete_profile(self):
        """Delete selected profile."""
        conn_idx = self.profile_combo.itemData(self.profile_combo.currentIndex())
        if conn_idx is None:
            return

        reply = QMessageBox.question(
            self,
            "Удаление профиля",
            "Вы уверены, что хотите удалить этот профиль?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.remove_connection(conn_idx)
            self.settings_manager.save()
            self.load_connections()
            self.profile_combo.setCurrentIndex(0)

    def toggle_password_visibility(self, checked: bool):
        """Toggle password visibility."""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁")

    def get_connection_data(self) -> DatabaseConnection:
        """Get connection data from form."""
        return DatabaseConnection(
            host=self.host_input.text().strip(),
            port=self.port_input.value(),
            database=self.database_input.text().strip(),
            user=self.user_input.text().strip(),
            password=self.password_input.text(),
            ssl_mode=self.ssl_combo.currentText(),
            is_active=True
        )

    def test_connection(self):
        """Test database connection."""
        self.start_connection(test_only=True)

    def connect(self):
        """Connect to database."""
        self.start_connection(test_only=False)

    def start_connection(self, test_only: bool = False):
        """
        Start connection process.

        Args:
            test_only: If True, only test connection without accepting dialog
        """
        try:
            # Validate inputs
            if not self.database_input.text().strip():
                self.show_error("Введите имя базы данных")
                return

            if not self.user_input.text().strip():
                self.show_error("Введите имя пользователя")
                return

            # Disable buttons
            self.set_buttons_enabled(False)
            self.progress_bar.setVisible(True)
            self.status_label.setVisible(True)
            self.status_label.setText("Подключение...")
            self.status_label.setStyleSheet("")

            # Create worker
            self.worker = ConnectWorker(
                self.controller,
                host=self.host_input.text().strip(),
                port=self.port_input.value(),
                database=self.database_input.text().strip(),
                user=self.user_input.text().strip(),
                password=self.password_input.text(),
                ssl_mode=self.ssl_combo.currentText()
            )

            # Connect signals
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.finished.connect(
                lambda success, _, message: self.on_connection_finished(
                    success, message, test_only
                )
            )
            self.worker.error.connect(self.show_error)

            # Start worker
            self.worker.start()

        except Exception as e:
            self.show_error(f"Ошибка: {str(e)}")
            self.set_buttons_enabled(True)

    def on_connection_finished(self, success: bool, message: str, test_only: bool):
        """
        Handle connection finished.

        Args:
            success: Connection success
            message: Status message
            test_only: If True, don't accept dialog
        """
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)

        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: green;")

            # Save connection if requested
            if self.save_connection_check.isChecked() and not test_only:
                conn_data = self.get_connection_data()
                self.settings_manager.add_connection(conn_data)
                self.settings_manager.save()
                logger.info("Connection saved")

            # Accept dialog if not test only
            if not test_only:
                self.connected.emit(self.get_connection_data())
                self.accept()

        else:
            self.show_error(message)

    def show_error(self, message: str):
        """Show error message."""
        self.status_label.setVisible(True)
        self.status_label.setText(f"❌ {message}")
        self.status_label.setStyleSheet("color: red;")
        logger.error(message)

    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable buttons."""
        self.test_btn.setEnabled(enabled)
        self.connect_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)

    def closeEvent(self, event):
        """Handle dialog close."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
