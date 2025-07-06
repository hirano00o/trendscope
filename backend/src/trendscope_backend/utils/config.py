"""Configuration management utility functions for stock analysis."""

import json
import os
from collections.abc import Callable
from typing import Any


class ConfigManager:
    """Configuration manager for application settings.

    Manages application configuration with support for loading from files,
    environment variables, and programmatic access to configuration values.

    Example:
        >>> config = ConfigManager({"api_timeout": 30})
        >>> config.get("api_timeout")
        30
        >>> config.set("debug_mode", True)
        >>> config.get("debug_mode")
        True
    """

    def __init__(self, initial_config: dict[str, Any] | None = None) -> None:
        """Initialize ConfigManager with optional initial configuration.

        Args:
            initial_config: Initial configuration dictionary
        """
        self._config: dict[str, Any] = initial_config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default

        Raises:
            KeyError: If key doesn't exist and no default provided

        Example:
            >>> config = ConfigManager({"timeout": 30})
            >>> config.get("timeout")
            30
            >>> config.get("missing", "default")
            'default'
        """
        if key in self._config:
            return self._config[key]
        elif default is not None:
            return default
        else:
            raise KeyError(f"Configuration key '{key}' not found")

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key to set
            value: Value to set

        Example:
            >>> config = ConfigManager()
            >>> config.set("api_key", "secret")
            >>> config.get("api_key")
            'secret'
        """
        self._config[key] = value

    def load_from_file(self, file_path: str) -> None:
        """Load configuration from JSON file.

        Args:
            file_path: Path to JSON configuration file

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON

        Example:
            >>> config = ConfigManager()
            >>> config.load_from_file("config.json")
        """
        with open(file_path) as f:
            file_config = json.load(f)
            self._config.update(file_config)

    def save_to_file(self, file_path: str) -> None:
        """Save current configuration to JSON file.

        Args:
            file_path: Path where to save configuration

        Example:
            >>> config = ConfigManager({"setting": "value"})
            >>> config.save_to_file("config.json")
        """
        with open(file_path, "w") as f:
            json.dump(self._config, f, indent=2)

    @classmethod
    def from_env_vars(cls, prefix: str = "") -> "ConfigManager":
        """Create ConfigManager from environment variables.

        Args:
            prefix: Environment variable prefix to filter by

        Returns:
            ConfigManager instance with environment variables

        Example:
            >>> # With env vars: MYAPP_TIMEOUT=30, MYAPP_DEBUG=true
            >>> config = ConfigManager.from_env_vars("MYAPP_")
            >>> config.get("TIMEOUT")
            '30'
        """
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix from key
                config_key = key[len(prefix) :]
                env_config[config_key] = value

        return cls(env_config)


def get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value from environment variables.

    Convenience function to get configuration values from environment
    without creating a ConfigManager instance.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Configuration value from environment or default

    Raises:
        ValueError: If key not found and no default provided

    Example:
        >>> # With environment variable API_KEY=secret
        >>> get_config_value("API_KEY")
        'secret'
        >>> get_config_value("MISSING", "default")
        'default'
    """
    value = os.environ.get(key)
    if value is not None:
        return value
    elif default is not None:
        return default
    else:
        raise ValueError(f"Configuration value not found: {key}")


def set_config_value(key: str, value: str) -> None:
    """Set configuration value in environment variables.

    Args:
        key: Environment variable name
        value: Value to set

    Example:
        >>> set_config_value("API_TIMEOUT", "30")
        >>> os.environ["API_TIMEOUT"]
        '30'
    """
    os.environ[key] = value


def validate_config(
    config: dict[str, Any],
    required_keys: list[str],
    validators: dict[str, Callable[[Any], bool]] | None = None,
) -> None:
    """Validate configuration dictionary.

    Checks that all required keys are present and optionally validates
    values using custom validator functions.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of keys that must be present
        validators: Optional dict of key -> validator function mappings

    Raises:
        ValueError: If required keys missing or validation fails

    Example:
        >>> config = {"timeout": 30, "retries": 3}
        >>> required = ["timeout", "retries"]
        >>> validators = {"timeout": lambda x: x > 0}
        >>> validate_config(config, required, validators)
        # No exception raised - validation passed
    """
    # Check for missing required keys
    missing_keys = set(required_keys) - set(config.keys())
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {sorted(missing_keys)}")

    # Run custom validators if provided
    if validators:
        failed_validations = []
        for key, validator in validators.items():
            if key in config:
                try:
                    if not validator(config[key]):
                        failed_validations.append(key)
                except Exception as e:
                    failed_validations.append(f"{key} ({e})")

        if failed_validations:
            raise ValueError(
                f"Configuration validation failed for keys: {failed_validations}"
            )

