"""Tests for date utility functions."""

import pytest
from datetime import datetime, date, timedelta
from trendscope_backend.utils.date import (
    parse_date,
    get_trading_days,
    get_period_start_date,
    validate_date_range,
)


class TestParseDate:
    """Test cases for parse_date function."""

    def test_parse_date_string_valid(self) -> None:
        """Test parsing valid date string."""
        result = parse_date("2024-01-15")
        expected = date(2024, 1, 15)
        assert result == expected

    def test_parse_date_datetime_object(self) -> None:
        """Test parsing datetime object."""
        dt = datetime(2024, 1, 15, 10, 30)
        result = parse_date(dt)
        expected = date(2024, 1, 15)
        assert result == expected

    def test_parse_date_date_object(self) -> None:
        """Test parsing date object returns same date."""
        input_date = date(2024, 1, 15)
        result = parse_date(input_date)
        assert result == input_date

    def test_parse_date_invalid_string(self) -> None:
        """Test parsing invalid date string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("invalid-date")

    def test_parse_date_none(self) -> None:
        """Test parsing None returns None."""
        result = parse_date(None)
        assert result is None


class TestGetTradingDays:
    """Test cases for get_trading_days function."""

    def test_get_trading_days_basic(self) -> None:
        """Test getting trading days for a basic period."""
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 5)    # Friday
        result = get_trading_days(start_date, end_date)
        assert len(result) == 5  # Monday to Friday

    def test_get_trading_days_exclude_weekends(self) -> None:
        """Test that weekends are excluded from trading days."""
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 7)    # Sunday
        result = get_trading_days(start_date, end_date)
        assert len(result) == 5  # Only weekdays

    def test_get_trading_days_empty_range(self) -> None:
        """Test empty date range returns empty list."""
        start_date = date(2024, 1, 5)
        end_date = date(2024, 1, 1)  # End before start
        result = get_trading_days(start_date, end_date)
        assert result == []


class TestGetPeriodStartDate:
    """Test cases for get_period_start_date function."""

    def test_get_period_start_date_days(self) -> None:
        """Test getting start date for days period."""
        end_date = date(2024, 1, 15)
        result = get_period_start_date(end_date, 10, "days")
        expected = date(2024, 1, 5)
        assert result == expected

    def test_get_period_start_date_weeks(self) -> None:
        """Test getting start date for weeks period."""
        end_date = date(2024, 1, 15)
        result = get_period_start_date(end_date, 2, "weeks")
        expected = date(2024, 1, 1)
        assert result == expected

    def test_get_period_start_date_months(self) -> None:
        """Test getting start date for months period."""
        end_date = date(2024, 3, 15)
        result = get_period_start_date(end_date, 2, "months")
        expected = date(2024, 1, 15)
        assert result == expected

    def test_get_period_start_date_years(self) -> None:
        """Test getting start date for years period."""
        end_date = date(2024, 3, 15)
        result = get_period_start_date(end_date, 1, "years")
        expected = date(2023, 3, 15)
        assert result == expected

    def test_get_period_start_date_invalid_unit(self) -> None:
        """Test invalid time unit raises ValueError."""
        end_date = date(2024, 1, 15)
        with pytest.raises(ValueError, match="Invalid time unit"):
            get_period_start_date(end_date, 10, "invalid")


class TestValidateDateRange:
    """Test cases for validate_date_range function."""

    def test_validate_date_range_valid(self) -> None:
        """Test valid date range passes validation."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 15)
        # Should not raise any exception
        validate_date_range(start_date, end_date)

    def test_validate_date_range_start_after_end(self) -> None:
        """Test start date after end date raises ValueError."""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 1)
        with pytest.raises(ValueError, match="Start date must be before end date"):
            validate_date_range(start_date, end_date)

    def test_validate_date_range_future_end_date(self) -> None:
        """Test future end date raises ValueError."""
        start_date = date(2024, 1, 1)
        end_date = date(2030, 1, 1)  # Future date
        with pytest.raises(ValueError, match="End date cannot be in the future"):
            validate_date_range(start_date, end_date)

    def test_validate_date_range_same_date(self) -> None:
        """Test same start and end date is valid."""
        same_date = date(2024, 1, 1)
        # Should not raise any exception
        validate_date_range(same_date, same_date)