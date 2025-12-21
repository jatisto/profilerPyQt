"""
Security utilities for password encryption and secure storage.

Uses cryptography library with Fernet (symmetric encryption).
Encryption key is stored in system keyring for maximum security.
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning("keyring library not available. Encryption key will be stored in file (less secure).")

from ..config import app_config


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class SecureStorage:
    """
    Secure storage for sensitive data (passwords, tokens).

    Uses Fernet symmetric encryption with a key stored in system keyring.
    Falls back to file-based storage if keyring is unavailable.
    """

    def __init__(self, service_name: Optional[str] = None):
        """
        Initialize secure storage.

        Args:
            service_name: Service name for keyring (default: app name)
        """
        self.service_name = service_name or app_config.app_short_name
        self.key_name = app_config.encryption_key_name
        self._cipher: Optional[Fernet] = None

    def _get_or_create_key(self) -> bytes:
        """
        Get encryption key from keyring or create new one.

        Returns:
            Encryption key (32 bytes)
        """
        if app_config.use_system_keyring and KEYRING_AVAILABLE:
            # Try to get key from system keyring
            try:
                key_str = keyring.get_password(self.service_name, self.key_name)
                if key_str:
                    logger.debug("Encryption key loaded from system keyring")
                    return key_str.encode()
            except Exception as e:
                logger.warning(f"Failed to access keyring: {e}")

        # Try to get key from file
        key_file = app_config.base_dir / ".encryption_key"
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key = f.read()
                logger.debug("Encryption key loaded from file")
                return key
            except Exception as e:
                logger.warning(f"Failed to read key file: {e}")

        # Generate new key
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()

        # Store in keyring
        if app_config.use_system_keyring and KEYRING_AVAILABLE:
            try:
                keyring.set_password(self.service_name, self.key_name, key.decode())
                logger.success("Encryption key stored in system keyring")
                return key
            except Exception as e:
                logger.warning(f"Failed to store key in keyring: {e}")

        # Fall back to file storage
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions on Unix-like systems
            if os.name != 'nt':
                os.chmod(key_file, 0o600)
            logger.info(f"Encryption key stored in file: {key_file}")
            return key
        except Exception as e:
            logger.error(f"Failed to store encryption key: {e}")
            raise EncryptionError(f"Cannot store encryption key: {e}") from e

    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher instance."""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            cipher = self._get_cipher()
            encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
            # Return as base64 string for JSON storage
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}") from e

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted string.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionError: If decryption fails
        """
        if not encrypted:
            return ""

        try:
            cipher = self._get_cipher()
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode('utf-8'))
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
            raise EncryptionError("Decryption failed: Invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Decryption failed: {e}") from e

    def is_encrypted(self, text: str) -> bool:
        """
        Check if text appears to be encrypted (basic heuristic).

        Args:
            text: Text to check

        Returns:
            True if text looks like it's encrypted
        """
        if not text:
            return False

        # Encrypted text should be base64-encoded Fernet token
        # Fernet tokens start with 'gAAAAA' after base64 encoding
        try:
            # Try to decode as base64
            decoded = base64.urlsafe_b64decode(text.encode('utf-8'))
            # Fernet tokens have a specific format
            return len(decoded) > 0 and text.startswith('Z0FBQ')  # Base64 of 'gAAA'
        except Exception:
            return False


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """
    Hash password using PBKDF2.

    Args:
        password: Password to hash
        salt: Salt bytes (if None, will be generated)

    Returns:
        (hashed_password, salt) tuple (both base64-encoded)

    Note:
        This is for password verification, not storage.
        For storage, use SecureStorage.encrypt() instead.
    """
    if salt is None:
        salt = os.urandom(32)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode('utf-8'))

    return (
        base64.urlsafe_b64encode(key).decode('utf-8'),
        base64.urlsafe_b64encode(salt).decode('utf-8')
    )


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """
    Verify password against hash.

    Args:
        password: Password to verify
        hashed: Expected hash (base64-encoded)
        salt: Salt used for hashing (base64-encoded)

    Returns:
        True if password matches
    """
    try:
        salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
        computed_hash, _ = hash_password(password, salt_bytes)
        return computed_hash == hashed
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False
