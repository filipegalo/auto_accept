"""Credential encryption and decryption utilities."""

import os
from base64 import b64decode, b64encode
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class CredentialCrypto:
    """Handle encryption and decryption of credentials."""

    ENCRYPTION_KEY_FILE = Path.home() / ".auto_accept" / ".key"
    ENCRYPTION_KEY_PERMISSIONS = 0o600

    @staticmethod
    def _get_or_create_key() -> bytes:
        """Get encryption key from file or create new one.

        Raises:
            RuntimeError: If key file cannot be accessed or created
        """
        try:
            if CredentialCrypto.ENCRYPTION_KEY_FILE.exists():
                with open(CredentialCrypto.ENCRYPTION_KEY_FILE, "rb") as f:
                    key_bytes = f.read()
                    assert isinstance(key_bytes, bytes)
                    return key_bytes

            # Create new encryption key
            new_key = Fernet.generate_key()
            assert isinstance(new_key, bytes)
            CredentialCrypto.ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Write key with restricted permissions
            with open(CredentialCrypto.ENCRYPTION_KEY_FILE, "wb") as f:
                f.write(new_key)
            os.chmod(
                CredentialCrypto.ENCRYPTION_KEY_FILE,
                CredentialCrypto.ENCRYPTION_KEY_PERMISSIONS,
            )

            return new_key
        except Exception as e:
            raise RuntimeError(f"Failed to manage encryption key: {e}") from e

    @staticmethod
    def encrypt_value(value: str) -> str:
        """Encrypt a string value.

        Args:
            value: String to encrypt

        Returns:
            Base64-encoded encrypted value

        Raises:
            RuntimeError: If encryption fails
        """
        try:
            key = CredentialCrypto._get_or_create_key()
            cipher = Fernet(key)
            encrypted = cipher.encrypt(value.encode())
            return b64encode(encrypted).decode()
        except Exception as e:
            raise RuntimeError(f"Failed to encrypt value: {e}") from e

    @staticmethod
    def decrypt_value(encrypted_value: str) -> str:
        """Decrypt an encrypted value.

        Args:
            encrypted_value: Base64-encoded encrypted value

        Returns:
            Decrypted string

        Raises:
            RuntimeError: If decryption fails or value is corrupted
        """
        try:
            key = CredentialCrypto._get_or_create_key()
            cipher = Fernet(key)
            encrypted_bytes = b64decode(encrypted_value.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted.decode()
            assert isinstance(decrypted_str, str)
            return decrypted_str
        except InvalidToken:
            raise RuntimeError(
                "Failed to decrypt credential: Invalid encryption key or corrupted data"
            ) from None
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt value: {e}") from e

    @staticmethod
    def encrypt_config(config: dict) -> dict:
        """Encrypt sensitive fields in configuration.

        Sensitive fields:
        - email (both Gmail and platform)
        - password (both Gmail and platform)

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with encrypted sensitive fields
        """
        encrypted = config.copy()

        # Encrypt sensitive fields
        sensitive_fields = [
            "email",
            "password",
            "platform_email",
            "platform_password",
        ]

        for field in sensitive_fields:
            if field in encrypted:
                encrypted[f"_enc_{field}"] = CredentialCrypto.encrypt_value(encrypted.pop(field))

        return encrypted

    @staticmethod
    def decrypt_config(config: dict) -> dict:
        """Decrypt sensitive fields in configuration.

        Args:
            config: Configuration dictionary with encrypted fields

        Returns:
            Configuration with decrypted sensitive fields

        Raises:
            RuntimeError: If decryption fails
        """
        decrypted = config.copy()

        # Decrypt sensitive fields
        sensitive_fields = ["email", "password", "platform_email", "platform_password"]

        for field in sensitive_fields:
            enc_field = f"_enc_{field}"
            if enc_field in decrypted:
                try:
                    decrypted[field] = CredentialCrypto.decrypt_value(decrypted.pop(enc_field))
                except RuntimeError:
                    # If decryption fails, raise error
                    raise RuntimeError(
                        f"Failed to decrypt {field}. The encryption key may have been lost or corrupted."
                    ) from None

        return decrypted
