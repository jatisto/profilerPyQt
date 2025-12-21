"""
Settings Manager with Encrypted Password Storage

Manages database connection settings with secure password encryption.
Uses Pydantic for validation and JSON for persistence.
"""

import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from ..config import app_config
from ..utils.security import SecureStorage, EncryptionError


class DatabaseConnection(BaseModel):
    """Database connection configuration with validation."""

    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database: str = Field(..., min_length=1, max_length=63)
    user: str = Field(..., min_length=1, max_length=63)
    password: str = Field(default="")
    ssl_mode: str = Field(default="prefer")
    is_active: bool = Field(default=False)
    name: Optional[str] = None  # User-friendly connection name

    @field_validator("ssl_mode")
    @classmethod
    def validate_ssl_mode(cls, v: str) -> str:
        """Validate SSL mode."""
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v not in valid_modes:
            raise ValueError(f"Invalid SSL mode. Must be one of: {valid_modes}")
        return v

    @field_validator("database", "user")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate PostgreSQL identifiers."""
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(
                f"Invalid identifier: '{v}'. "
                f"Must start with letter/underscore and contain only alphanumeric/underscore."
            )
        return v

    def get_connection_string(self, decrypt_password: bool = True) -> str:
        """
        Get connection string (for display, password masked).

        Args:
            decrypt_password: If True, use actual password; if False, mask it

        Returns:
            Connection string
        """
        password_display = "***" if not decrypt_password else self.password
        return f"{self.user}@{self.host}:{self.port}/{self.database}"

    def model_dump_json_safe(self) -> dict:
        """Dump model to dict with password masked."""
        data = self.model_dump()
        data['password'] = "***" if data['password'] else ""
        return data


class AppSettings(BaseModel):
    """Application settings."""

    theme: str = Field(default="dark")
    language: str = Field(default="ru")
    use_custom_titlebar: bool = Field(default=False)
    check_updates_on_startup: bool = Field(default=False)
    window_width: int = Field(default=1400, ge=800)
    window_height: int = Field(default=900, ge=600)


class SettingsManager:
    """
    Manages application and database connection settings.

    Features:
    - Encrypted password storage
    - Multiple database connections
    - Active connection tracking
    - Validation and error handling
    """

    def __init__(self, settings_file: Optional[Path] = None):
        """
        Initialize settings manager.

        Args:
            settings_file: Path to settings file (default: settings.json)
        """
        self.settings_file = settings_file or (app_config.base_dir / "settings.json")
        self.security = SecureStorage()
        self.connections: List[DatabaseConnection] = []
        self.app_settings = AppSettings()

        logger.debug(f"SettingsManager initialized with file: {self.settings_file}")

    def load(self) -> bool:
        """
        Load settings from file.

        Returns:
            True if successful, False otherwise
        """
        if not self.settings_file.exists():
            logger.info("Settings file not found, using defaults")
            return False

        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load app settings
            if 'app_settings' in data:
                self.app_settings = AppSettings(**data['app_settings'])
                logger.debug("App settings loaded")

            # Load connections
            if 'connections' in data:
                self.connections = []
                for conn_data in data['connections']:
                    # Decrypt password if encrypted
                    if 'password' in conn_data and conn_data['password']:
                        try:
                            conn_data['password'] = self.security.decrypt(conn_data['password'])
                        except EncryptionError:
                            logger.warning(f"Failed to decrypt password for {conn_data.get('host')}")
                            conn_data['password'] = ""

                    try:
                        connection = DatabaseConnection(**conn_data)
                        self.connections.append(connection)
                    except Exception as e:
                        logger.error(f"Failed to load connection: {e}")

                logger.info(f"Loaded {len(self.connections)} database connections")

            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return False

    def save(self) -> bool:
        """
        Save settings to file with encrypted passwords.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare connections data
            connections_data = []
            for conn in self.connections:
                conn_dict = conn.model_dump()

                # Encrypt password before saving
                if conn_dict['password']:
                    try:
                        conn_dict['password'] = self.security.encrypt(conn_dict['password'])
                    except EncryptionError as e:
                        logger.error(f"Failed to encrypt password: {e}")
                        return False

                connections_data.append(conn_dict)

            # Prepare full settings
            settings_data = {
                'app_settings': self.app_settings.model_dump(),
                'connections': connections_data
            }

            # Write to file
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            logger.success(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def add_connection(self, connection: DatabaseConnection) -> None:
        """
        Add new database connection.

        If is_active is True, deactivates all other connections.

        Args:
            connection: Database connection to add
        """
        # Deactivate other connections if this one is active
        if connection.is_active:
            for conn in self.connections:
                conn.is_active = False

        # Check for duplicates (same host, port, database, user)
        for i, existing in enumerate(self.connections):
            if (existing.host == connection.host and
                existing.port == connection.port and
                existing.database == connection.database and
                existing.user == connection.user):

                logger.info("Updating existing connection")
                self.connections[i] = connection
                return

        self.connections.append(connection)
        logger.info(f"Added new connection: {connection.get_connection_string(decrypt_password=False)}")

    def remove_connection(self, index: int) -> bool:
        """
        Remove connection by index.

        Args:
            index: Connection index

        Returns:
            True if successful
        """
        if 0 <= index < len(self.connections):
            removed = self.connections.pop(index)
            logger.info(f"Removed connection: {removed.get_connection_string(decrypt_password=False)}")
            return True
        return False

    def get_active_connection(self) -> Optional[DatabaseConnection]:
        """
        Get currently active connection.

        Returns:
            Active connection or None
        """
        for conn in self.connections:
            if conn.is_active:
                return conn
        return None

    def set_active_connection(self, index: int) -> bool:
        """
        Set connection as active by index.

        Args:
            index: Connection index

        Returns:
            True if successful
        """
        if 0 <= index < len(self.connections):
            # Deactivate all
            for conn in self.connections:
                conn.is_active = False

            # Activate selected
            self.connections[index].is_active = True
            logger.info(
                f"Activated connection: "
                f"{self.connections[index].get_connection_string(decrypt_password=False)}"
            )
            return True
        return False

    def get_all_connections(self) -> List[DatabaseConnection]:
        """Get all connections."""
        return self.connections.copy()

    def get_connection_names(self) -> List[str]:
        """
        Get list of connection names/identifiers for UI display.

        Returns:
            List of connection strings
        """
        return [
            conn.name or conn.get_connection_string(decrypt_password=False)
            for conn in self.connections
        ]

    def migrate_from_old_format(self, old_settings_file: Path) -> bool:
        """
        Migrate settings from old format (plaintext passwords).

        Args:
            old_settings_file: Path to old settings.json

        Returns:
            True if successful
        """
        try:
            if not old_settings_file.exists():
                return False

            with open(old_settings_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)

            if 'setting' in old_data:
                for old_conn in old_data['setting']:
                    try:
                        connection = DatabaseConnection(
                            host=old_conn.get('host', 'localhost'),
                            port=int(old_conn.get('port', 5432)),
                            database=old_conn.get('dbname', 'postgres'),
                            user=old_conn.get('username', 'postgres'),
                            password=old_conn.get('password', ''),
                            is_active=old_conn.get('actual', False)
                        )
                        self.add_connection(connection)
                    except Exception as e:
                        logger.error(f"Failed to migrate connection: {e}")

            # Load custom bar setting
            if 'custom_bar' in old_data:
                self.app_settings.use_custom_titlebar = old_data['custom_bar']

            logger.success(f"Migrated {len(self.connections)} connections from old format")
            return True

        except Exception as e:
            logger.error(f"Failed to migrate old settings: {e}")
            return False
