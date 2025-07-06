"""Tests for configuration management utility functions."""

import os
import tempfile

import pytest

from trendscope_backend.utils.config import (
    ConfigManager,
    get_config_value,
    set_config_value,
    validate_config,
)


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_config_manager_init_default(self) -> None:
        """Test ConfigManager initialization with default values."""
        config = ConfigManager()
        assert config.get("api_timeout", 30) == 30
        assert config.get("max_data_points", 1000) == 1000

    def test_config_manager_init_with_dict(self) -> None:
        """Test ConfigManager initialization with dictionary."""
        initial_config = {
            "api_timeout": 60,
            "max_data_points": 2000,
            "cache_enabled": True,
        }
        config = ConfigManager(initial_config)
        assert config.get("api_timeout") == 60
        assert config.get("max_data_points") == 2000
        assert config.get("cache_enabled") is True

    def test_config_manager_get_existing_key(self) -> None:
        """Test getting existing configuration value."""
        config = ConfigManager({"test_key": "test_value"})
        assert config.get("test_key") == "test_value"

    def test_config_manager_get_nonexistent_key_with_default(self) -> None:
        """Test getting nonexistent key returns default value."""
        config = ConfigManager()
        assert config.get("nonexistent", "default") == "default"

    def test_config_manager_get_nonexistent_key_no_default(self) -> None:
        """Test getting nonexistent key without default raises KeyError."""
        config = ConfigManager()
        with pytest.raises(KeyError):
            config.get("nonexistent")

    def test_config_manager_set_value(self) -> None:
        """Test setting configuration value."""
        config = ConfigManager()
        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"

    def test_config_manager_update_existing_value(self) -> None:
        """Test updating existing configuration value."""
        config = ConfigManager({"existing_key": "old_value"})
        config.set("existing_key", "new_value")
        assert config.get("existing_key") == "new_value"

    def test_config_manager_load_from_file(self) -> None:
        """Test loading configuration from JSON file."""
        config_data = {
            "api_key": "test_key",
            "timeout": 30,
            "features": ["feature1", "feature2"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(config_data, f)
            f.flush()

            config = ConfigManager()
            config.load_from_file(f.name)

            assert config.get("api_key") == "test_key"
            assert config.get("timeout") == 30
            assert config.get("features") == ["feature1", "feature2"]

            # Cleanup
            os.unlink(f.name)

    def test_config_manager_load_from_nonexistent_file(self) -> None:
        """Test loading from nonexistent file raises FileNotFoundError."""
        config = ConfigManager()
        with pytest.raises(FileNotFoundError):
            config.load_from_file("nonexistent_file.json")

    def test_config_manager_save_to_file(self) -> None:
        """Test saving configuration to JSON file."""
        config = ConfigManager(
            {
                "setting1": "value1",
                "setting2": 42,
                "setting3": True,
            }
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config.save_to_file(f.name)

            # Load and verify
            import json

            with open(f.name) as read_f:
                saved_data = json.load(read_f)

            assert saved_data["setting1"] == "value1"
            assert saved_data["setting2"] == 42
            assert saved_data["setting3"] is True

            # Cleanup
            os.unlink(f.name)

    def test_config_manager_from_env_vars(self) -> None:
        """Test loading configuration from environment variables."""
        # Set test environment variables
        os.environ["TRENDSCOPE_API_TIMEOUT"] = "60"
        os.environ["TRENDSCOPE_MAX_POINTS"] = "5000"
        os.environ["TRENDSCOPE_DEBUG"] = "true"

        try:
            config = ConfigManager.from_env_vars("TRENDSCOPE_")
            assert config.get("API_TIMEOUT") == "60"
            assert config.get("MAX_POINTS") == "5000"
            assert config.get("DEBUG") == "true"
        finally:
            # Cleanup environment variables
            del os.environ["TRENDSCOPE_API_TIMEOUT"]
            del os.environ["TRENDSCOPE_MAX_POINTS"]
            del os.environ["TRENDSCOPE_DEBUG"]


class TestConfigUtilityFunctions:
    """Test cases for configuration utility functions."""

    def test_get_config_value_existing(self) -> None:
        """Test getting existing config value."""
        os.environ["TEST_CONFIG_VALUE"] = "test_result"
        try:
            result = get_config_value("TEST_CONFIG_VALUE")
            assert result == "test_result"
        finally:
            del os.environ["TEST_CONFIG_VALUE"]

    def test_get_config_value_with_default(self) -> None:
        """Test getting config value with default."""
        result = get_config_value("NONEXISTENT_CONFIG", "default_value")
        assert result == "default_value"

    def test_get_config_value_nonexistent_no_default(self) -> None:
        """Test getting nonexistent config value without default raises error."""
        with pytest.raises(ValueError, match="Configuration value not found"):
            get_config_value("NONEXISTENT_CONFIG")

    def test_set_config_value(self) -> None:
        """Test setting config value in environment."""
        set_config_value("TEST_SET_CONFIG", "test_value")
        assert os.environ["TEST_SET_CONFIG"] == "test_value"
        # Cleanup
        del os.environ["TEST_SET_CONFIG"]

    def test_validate_config_valid(self) -> None:
        """Test validating valid configuration."""
        config = {
            "api_timeout": 30,
            "max_data_points": 1000,
            "cache_enabled": True,
        }
        required_keys = ["api_timeout", "max_data_points"]
        # Should not raise any exception
        validate_config(config, required_keys)

    def test_validate_config_missing_keys(self) -> None:
        """Test validating config with missing required keys."""
        config = {
            "api_timeout": 30,
        }
        required_keys = ["api_timeout", "max_data_points", "cache_enabled"]
        with pytest.raises(ValueError, match="Missing required configuration keys"):
            validate_config(config, required_keys)

    def test_validate_config_with_validators(self) -> None:
        """Test validating config with custom validators."""
        config = {
            "api_timeout": 30,
            "max_data_points": 1000,
        }
        validators = {
            "api_timeout": lambda x: x > 0,
            "max_data_points": lambda x: x > 100,
        }
        # Should not raise any exception
        validate_config(config, list(config.keys()), validators)

    def test_validate_config_failed_validation(self) -> None:
        """Test config validation failure."""
        config = {
            "api_timeout": -5,  # Invalid: negative timeout
            "max_data_points": 50,  # Invalid: too few data points
        }
        validators = {
            "api_timeout": lambda x: x > 0,
            "max_data_points": lambda x: x > 100,
        }
        with pytest.raises(ValueError, match="Configuration validation failed"):
            validate_config(config, list(config.keys()), validators)
