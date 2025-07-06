"""Data validation utility functions for stock analysis."""

import re
import unicodedata

import numpy as np
import pandas as pd


def validate_stock_symbol(symbol: str | None) -> str:
    """Validate and normalize stock symbol.

    Validates stock symbol format, removes whitespace, converts to uppercase,
    and checks for valid characters and length constraints.

    Args:
        symbol: Stock symbol to validate

    Returns:
        Normalized stock symbol in uppercase

    Raises:
        ValueError: If symbol is invalid, empty, or contains illegal characters

    Example:
        >>> validate_stock_symbol("  aapl  ")
        'AAPL'
        >>> validate_stock_symbol("BRK-A")
        'BRK-A'
    """
    if symbol is None or not symbol.strip():
        raise ValueError("Stock symbol cannot be empty")

    # Normalize and clean the symbol
    symbol = symbol.strip().upper()

    # Check length constraints
    if len(symbol) > 10:
        raise ValueError("Stock symbol too long (max 10 characters)")

    # Check for valid characters (letters, numbers, dash, dot)
    if not re.match(r"^[A-Z0-9.-]+$", symbol):
        raise ValueError(
            "Invalid characters in stock symbol. "
            "Only letters, numbers, dash, and dot allowed"
        )

    # Ensure it contains at least one letter
    if not re.search(r"[A-Z]", symbol):
        raise ValueError("Stock symbol must contain letters")

    return symbol


def validate_dataframe_structure(
    df: pd.DataFrame,
    required_columns: list[str],
    min_rows: int = 1,
    allow_nan: bool = False,
) -> None:
    """Validate DataFrame structure and data quality.

    Checks that DataFrame has required columns, sufficient rows,
    and optionally validates data quality (no NaN values).

    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
        min_rows: Minimum number of rows required
        allow_nan: Whether to allow NaN values in the data

    Raises:
        ValueError: If DataFrame structure or data quality is invalid

    Example:
        >>> df = pd.DataFrame({"Date": ["2024-01-01"], "Close": [100.0]})
        >>> validate_dataframe_structure(df, ["Date", "Close"])
        # No exception raised - valid structure
    """
    if df.empty:
        raise ValueError("DataFrame is empty")

    # Check for required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    # Check minimum rows
    if len(df) < min_rows:
        raise ValueError(
            f"Insufficient data: {len(df)} rows, minimum {min_rows} required"
        )

    # Check for NaN values if not allowed
    if not allow_nan and df[required_columns].isnull().any().any():
        raise ValueError("DataFrame contains NaN values in required columns")


def validate_numeric_range(
    value: float | int | None,
    min_value: float | int,
    max_value: float | int,
    name: str,
) -> float | int:
    """Validate numeric value is within specified range.

    Ensures numeric value is finite, not None, and within the specified
    minimum and maximum bounds (inclusive).

    Args:
        value: Numeric value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        name: Descriptive name of the value for error messages

    Returns:
        The validated numeric value

    Raises:
        ValueError: If value is None, infinite, NaN, or outside range

    Example:
        >>> validate_numeric_range(50, 0, 100, "percentage")
        50
        >>> validate_numeric_range(-5, 0, 100, "percentage")
        ValueError: percentage must be >= 0
    """
    if value is None:
        raise ValueError(f"{name} cannot be None")

    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite (not NaN or infinite)")

    if value < min_value:
        raise ValueError(f"{name} must be >= {min_value}")

    if value > max_value:
        raise ValueError(f"{name} must be <= {max_value}")

    return value


def sanitize_input_string(
    input_str: str | None,
    allowed_chars: str = "",
    max_length: int | None = None,
    convert_case: str | None = None,
) -> str:
    """Sanitize and normalize input string.

    Removes unsafe characters, normalizes Unicode, trims whitespace,
    and optionally converts case and enforces length limits.

    Args:
        input_str: String to sanitize
        allowed_chars: Additional characters to allow beyond alphanumeric
        max_length: Maximum length to truncate to
        convert_case: Case conversion ("upper", "lower", or None)

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is None or empty after sanitization

    Example:
        >>> sanitize_input_string("  Hello@World!  ", allowed_chars="")
        'HelloWorld'
        >>> sanitize_input_string("test", convert_case="upper")
        'TEST'
    """
    if input_str is None:
        raise ValueError("Input string cannot be None")

    # Normalize Unicode characters
    input_str = unicodedata.normalize("NFKC", input_str)

    # Remove leading/trailing whitespace
    input_str = input_str.strip()

    # Keep only alphanumeric characters (including Unicode letters)
    # and explicitly allowed characters
    pattern = r"[^\w\s" + re.escape(allowed_chars) + r"]"
    input_str = re.sub(pattern, "", input_str, flags=re.UNICODE)

    # Collapse multiple whitespace into single spaces
    input_str = re.sub(r"\s+", " ", input_str)

    # Apply case conversion
    if convert_case == "upper":
        input_str = input_str.upper()
    elif convert_case == "lower":
        input_str = input_str.lower()

    # Enforce maximum length
    if max_length is not None and len(input_str) > max_length:
        input_str = input_str[:max_length]

    # Check if result is empty
    if not input_str:
        raise ValueError("Input string is empty after sanitization")

    return input_str

