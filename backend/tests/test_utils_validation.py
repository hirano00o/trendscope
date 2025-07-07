"""Tests for data validation utility functions."""

import numpy as np
import pandas as pd
import pytest

from trendscope_backend.utils.validation import (
    sanitize_input_string,
    validate_dataframe_structure,
    validate_numeric_range,
    validate_stock_symbol,
)


class TestValidateStockSymbol:
    """Test cases for validate_stock_symbol function."""

    def test_validate_stock_symbol_valid_us(self) -> None:
        """Test valid US stock symbols."""
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMD"]
        for symbol in valid_symbols:
            result = validate_stock_symbol(symbol)
            assert result == symbol.upper()

    def test_validate_stock_symbol_valid_with_dash(self) -> None:
        """Test valid stock symbols with dash."""
        result = validate_stock_symbol("BRK-A")
        assert result == "BRK-A"

    def test_validate_stock_symbol_valid_with_dot(self) -> None:
        """Test valid stock symbols with dot."""
        result = validate_stock_symbol("BRK.A")
        assert result == "BRK.A"

    def test_validate_stock_symbol_lowercase(self) -> None:
        """Test lowercase symbol gets converted to uppercase."""
        result = validate_stock_symbol("aapl")
        assert result == "AAPL"

    def test_validate_stock_symbol_with_whitespace(self) -> None:
        """Test symbol with whitespace gets trimmed."""
        result = validate_stock_symbol("  AAPL  ")
        assert result == "AAPL"

    def test_validate_stock_symbol_empty_string(self) -> None:
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol cannot be empty"):
            validate_stock_symbol("")

    def test_validate_stock_symbol_none(self) -> None:
        """Test None raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol cannot be empty"):
            validate_stock_symbol(None)

    def test_validate_stock_symbol_invalid_characters(self) -> None:
        """Test symbol with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="Invalid characters in stock symbol"):
            validate_stock_symbol("AAPL@")

    def test_validate_stock_symbol_too_long(self) -> None:
        """Test symbol too long raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol too long"):
            validate_stock_symbol("VERYLONGSYMBOL")

    def test_validate_stock_symbol_numbers_only(self) -> None:
        """Test numeric-only symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol must contain letters"):
            validate_stock_symbol("12345")


class TestValidateDataframeStructure:
    """Test cases for validate_dataframe_structure function."""

    def test_validate_dataframe_structure_valid(self) -> None:
        """Test valid DataFrame with required columns."""
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=5),
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [105.0, 106.0, 107.0, 108.0, 109.0],
                "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            }
        )
        # Should not raise any exception
        validate_dataframe_structure(df, ["Date", "Close"])

    def test_validate_dataframe_structure_missing_columns(self) -> None:
        """Test DataFrame missing required columns raises ValueError."""
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=5),
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_dataframe_structure(df, ["Date", "Close", "High"])

    def test_validate_dataframe_structure_empty_dataframe(self) -> None:
        """Test empty DataFrame raises ValueError."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame is empty"):
            validate_dataframe_structure(df, ["Date"])

    def test_validate_dataframe_structure_insufficient_rows(self) -> None:
        """Test DataFrame with insufficient rows raises ValueError."""
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=2),
                "Close": [100.0, 101.0],
            }
        )
        with pytest.raises(ValueError, match="Insufficient data"):
            validate_dataframe_structure(df, ["Date", "Close"], min_rows=5)

    def test_validate_dataframe_structure_nan_values(self) -> None:
        """Test DataFrame with NaN values raises ValueError."""
        df = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=5),
                "Close": [100.0, np.nan, 102.0, 103.0, 104.0],
            }
        )
        with pytest.raises(ValueError, match="DataFrame contains NaN values"):
            validate_dataframe_structure(df, ["Date", "Close"])


class TestValidateNumericRange:
    """Test cases for validate_numeric_range function."""

    def test_validate_numeric_range_valid(self) -> None:
        """Test valid numeric value within range."""
        result = validate_numeric_range(50, 0, 100, "test_value")
        assert result == 50

    def test_validate_numeric_range_at_boundaries(self) -> None:
        """Test values at range boundaries."""
        assert validate_numeric_range(0, 0, 100, "test") == 0
        assert validate_numeric_range(100, 0, 100, "test") == 100

    def test_validate_numeric_range_below_minimum(self) -> None:
        """Test value below minimum raises ValueError."""
        with pytest.raises(ValueError, match="test_value must be >= 0"):
            validate_numeric_range(-5, 0, 100, "test_value")

    def test_validate_numeric_range_above_maximum(self) -> None:
        """Test value above maximum raises ValueError."""
        with pytest.raises(ValueError, match="test_value must be <= 100"):
            validate_numeric_range(150, 0, 100, "test_value")

    def test_validate_numeric_range_float_values(self) -> None:
        """Test float values within range."""
        result = validate_numeric_range(3.14, 0.0, 10.0, "pi")
        assert result == 3.14

    def test_validate_numeric_range_none_value(self) -> None:
        """Test None value raises ValueError."""
        with pytest.raises(ValueError, match="test_value cannot be None"):
            validate_numeric_range(None, 0, 100, "test_value")

    def test_validate_numeric_range_infinite_value(self) -> None:
        """Test infinite value raises ValueError."""
        with pytest.raises(ValueError, match="test_value must be finite"):
            validate_numeric_range(float("inf"), 0, 100, "test_value")

    def test_validate_numeric_range_nan_value(self) -> None:
        """Test NaN value raises ValueError."""
        with pytest.raises(ValueError, match="test_value must be finite"):
            validate_numeric_range(float("nan"), 0, 100, "test_value")


class TestSanitizeInputString:
    """Test cases for sanitize_input_string function."""

    def test_sanitize_input_string_basic(self) -> None:
        """Test basic string sanitization."""
        result = sanitize_input_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_input_string_remove_special_chars(self) -> None:
        """Test removal of special characters."""
        result = sanitize_input_string("Hello@#$%World!", allowed_chars="")
        assert result == "HelloWorld"

    def test_sanitize_input_string_allow_specific_chars(self) -> None:
        """Test allowing specific characters."""
        result = sanitize_input_string("AAPL-B.C", allowed_chars="-.")
        assert result == "AAPL-B.C"

    def test_sanitize_input_string_max_length(self) -> None:
        """Test maximum length enforcement."""
        long_string = "A" * 100
        result = sanitize_input_string(long_string, max_length=10)
        assert len(result) == 10
        assert result == "A" * 10

    def test_sanitize_input_string_empty_result(self) -> None:
        """Test empty result after sanitization raises ValueError."""
        with pytest.raises(
            ValueError, match="Input string is empty after sanitization"
        ):
            sanitize_input_string("@#$%", allowed_chars="")

    def test_sanitize_input_string_none_input(self) -> None:
        """Test None input raises ValueError."""
        with pytest.raises(ValueError, match="Input string cannot be None"):
            sanitize_input_string(None)

    def test_sanitize_input_string_unicode_normalization(self) -> None:
        """Test Unicode normalization."""
        # Test string with accented characters
        result = sanitize_input_string("café")
        assert result == "café"

    def test_sanitize_input_string_case_conversion(self) -> None:
        """Test case conversion."""
        result = sanitize_input_string("hello world", convert_case="upper")
        assert result == "HELLO WORLD"

        result = sanitize_input_string("HELLO WORLD", convert_case="lower")
        assert result == "hello world"
