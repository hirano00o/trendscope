"""Date utility functions for stock analysis."""

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta


def parse_date(date_input: str | datetime | date | None) -> date | None:
    """Parse various date input formats to date object.

    Converts string, datetime, or date objects to date objects for consistent
    date handling across the application.

    Args:
        date_input: Input date in string (YYYY-MM-DD), datetime, or date format

    Returns:
        Parsed date object or None if input is None

    Raises:
        ValueError: If date string format is invalid

    Example:
        >>> parse_date("2024-01-15")
        date(2024, 1, 15)
        >>> parse_date(datetime(2024, 1, 15, 10, 30))
        date(2024, 1, 15)
    """
    if date_input is None:
        return None

    if isinstance(date_input, datetime):
        return date_input.date()

    if isinstance(date_input, date):
        return date_input

    if isinstance(date_input, str):
        try:
            parsed_datetime = datetime.strptime(date_input, "%Y-%m-%d")
            return parsed_datetime.date()
        except ValueError as e:
            raise ValueError(
                f"Invalid date format: {date_input}. Expected YYYY-MM-DD"
            ) from e

    raise ValueError(f"Unsupported date input type: {type(date_input)}")


def get_trading_days(start_date: date, end_date: date) -> list[date]:
    """Get list of trading days (weekdays) between start and end dates.

    Returns all weekdays (Monday-Friday) in the specified date range,
    excluding weekends but not accounting for market holidays.

    Args:
        start_date: Start date of the range
        end_date: End date of the range (inclusive)

    Returns:
        List of trading days (weekdays) in the range

    Example:
        >>> start = date(2024, 1, 1)  # Monday
        >>> end = date(2024, 1, 5)    # Friday
        >>> len(get_trading_days(start, end))
        5
    """
    if start_date > end_date:
        return []

    trading_days = []
    current_date = start_date

    while current_date <= end_date:
        # Monday = 0, Sunday = 6, so weekday < 5 means Monday-Friday
        if current_date.weekday() < 5:
            trading_days.append(current_date)
        current_date += timedelta(days=1)

    return trading_days


def get_period_start_date(end_date: date, period: int, unit: str) -> date:
    """Calculate start date for a given period before end date.

    Calculates the start date by subtracting the specified period from the end date.
    Supports days, weeks, months, and years as time units.

    Args:
        end_date: End date of the period
        period: Number of time units to subtract
        unit: Time unit ("days", "weeks", "months", "years")

    Returns:
        Start date of the period

    Raises:
        ValueError: If time unit is not supported

    Example:
        >>> end = date(2024, 1, 15)
        >>> get_period_start_date(end, 10, "days")
        date(2024, 1, 5)
    """
    if unit == "days":
        return end_date - timedelta(days=period)
    elif unit == "weeks":
        return end_date - timedelta(weeks=period)
    elif unit == "months":
        return end_date - relativedelta(months=period)
    elif unit == "years":
        return end_date - relativedelta(years=period)
    else:
        raise ValueError(
            f"Invalid time unit: {unit}. Supported units: days, weeks, months, years"
        )


def validate_date_range(start_date: date, end_date: date) -> None:
    """Validate that date range is logical and within acceptable bounds.

    Checks that start date is before or equal to end date, and that
    end date is not in the future (since we can't get future stock data).

    Args:
        start_date: Start date of the range
        end_date: End date of the range

    Raises:
        ValueError: If date range is invalid

    Example:
        >>> validate_date_range(date(2024, 1, 1), date(2024, 1, 15))
        # No exception raised - valid range
    """
    if start_date > end_date:
        raise ValueError("Start date must be before end date")

    today = date.today()
    if end_date > today:
        raise ValueError("End date cannot be in the future")

