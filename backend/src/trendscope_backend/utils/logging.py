"""Logging utility functions for stock analysis."""

import functools
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: str | None = None,
    log_format: str | None = None,
    console_output: bool = True,
) -> logging.Logger:
    """Set up and configure a logger with file and/or console output.

    Creates a logger with customizable output format, file logging,
    and console output options for comprehensive logging management.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional file path for log output
        log_format: Custom log format string
        console_output: Whether to enable console output

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("stock_analysis", level=logging.DEBUG)
        >>> logger.info("Analysis started")
        >>> logger = setup_logger("app", log_file="/var/log/app.log")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Default format if none provided
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if file path provided
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get or create a logger instance.

    Convenience function to get a logger with consistent configuration.
    If the logger doesn't exist, creates it with default settings.

    Args:
        name: Logger name (defaults to calling module name)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module operation completed")
        >>> logger = get_logger("data_processor")
    """
    if name is None:
        # Get caller's module name
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "unknown")
        else:
            name = "unknown"

    logger = logging.getLogger(name)

    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        logger = setup_logger(name)

    return logger


def log_function_call(
    logger: logging.Logger | None = None,
    log_args: bool = False,
    log_result: bool = False,
    level: int = logging.INFO,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to log function calls with optional arguments and results.

    Logs function entry, exit, arguments, return values, and exceptions
    for debugging and monitoring purposes.

    Args:
        logger: Logger to use (defaults to function's module logger)
        log_args: Whether to log function arguments
        log_result: Whether to log function return value
        level: Log level for normal operations

    Returns:
        Decorator function

    Example:
        >>> @log_function_call(log_args=True, log_result=True)
        ... def calculate_price(symbol: str, multiplier: float = 1.0) -> float:
        ...     return 100.0 * multiplier
        >>> calculate_price("AAPL", 1.5)  # Logs call with args and result
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger if not provided
            func_logger = logger or get_logger(func.__module__)

            # Log function entry
            func_name = func.__name__
            log_msg = f"Calling {func_name}"

            if log_args:
                log_msg += f" with args={args}, kwargs={kwargs}"

            func_logger.log(level, log_msg)

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Log successful completion
                completion_msg = f"Finished {func_name}"
                if log_result:
                    completion_msg += f" returned: {result}"

                func_logger.log(level, completion_msg)

                return result

            except Exception as e:
                # Log exception
                func_logger.error(f"Exception in {func_name}: {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator


def log_performance(
    logger: logging.Logger | None = None,
    threshold_seconds: float = 0.0,
    slow_threshold_seconds: float = 5.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to log function execution time and performance metrics.

    Measures and logs function execution time, with different log levels
    for normal vs slow execution times to identify performance issues.

    Args:
        logger: Logger to use (defaults to function's module logger)
        threshold_seconds: Minimum execution time to log (0 = always log)
        slow_threshold_seconds: Threshold for warning about slow execution

    Returns:
        Decorator function

    Example:
        >>> @log_performance(threshold_seconds=0.1, slow_threshold_seconds=2.0)
        ... def analyze_stock_data(symbol: str) -> dict:
        ...     # Expensive operation
        ...     return {"symbol": symbol, "analysis": "complete"}
        >>> analyze_stock_data("AAPL")  # Logs execution time
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger if not provided
            func_logger = logger or get_logger(func.__module__)

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Calculate execution time
                execution_time = time.time() - start_time

                # Only log if above threshold
                if execution_time >= threshold_seconds:
                    func_name = func.__name__

                    # Choose log level based on execution time
                    if execution_time >= slow_threshold_seconds:
                        log_level = logging.WARNING
                        prefix = "SLOW Performance:"
                    else:
                        log_level = logging.INFO
                        prefix = "Performance:"

                    func_logger.log(
                        log_level,
                        f"{prefix} {func_name} took {execution_time:.4f} seconds",
                    )

        return wrapper

    return decorator

