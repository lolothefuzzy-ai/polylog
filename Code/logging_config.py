"""
Structured Logging Configuration for Polylog6
==============================================

Provides:
- Rotating file handlers with size limits
- Structured JSON-like logging for analysis
- Decorators for automatic error tracking
- Context managers for operation tracking
- Thread-safe logging across all modules
"""

import logging
import logging.handlers
import json
import time
import traceback
import functools
from typing import Any, Callable, Optional, Dict
from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path

# Default log directory
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

# Global logger instances
_loggers: Dict[str, logging.Logger] = {}


class StructuredFormatter(logging.Formatter):
    """Formats log records with context information"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format as JSON for structured logging"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = "".join(traceback.format_exception(*record.exc_info))
        
        # Add extra fields if provided
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger with rotating file handler.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (rotating, size-based)
    log_file = LOG_DIR / f"{name.replace('.', '_')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,  # Keep 5 backups
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


def log_error(logger: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to automatically log exceptions and errors.
    
    Usage:
        @log_error()
        def my_function():
            ...
    
    Or with custom logger:
        @log_error(my_logger)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            try:
                logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned successfully")
                return result
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={"extra_data": {"function": func.__name__, "args": str(args)[:200]}}
                )
                raise
        
        return wrapper
    
    # Handle both @log_error and @log_error() syntax
    if callable(logger):
        func = logger
        logger = None
        return decorator(func)
    
    return decorator


def log_performance(logger: Optional[logging.Logger] = None, threshold_ms: float = 100.0) -> Callable:
    """
    Decorator to log function execution time and warn if threshold exceeded.
    
    Usage:
        @log_performance(threshold_ms=50)
        def expensive_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start) * 1000
                
                level = logging.WARNING if elapsed_ms > threshold_ms else logging.DEBUG
                logger.log(
                    level,
                    f"{func.__name__} took {elapsed_ms:.2f}ms",
                    extra={"extra_data": {"duration_ms": elapsed_ms, "threshold_ms": threshold_ms}}
                )
                
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                logger.error(
                    f"{func.__name__} failed after {elapsed_ms:.2f}ms: {str(e)}",
                    exc_info=True,
                    extra={"extra_data": {"duration_ms": elapsed_ms}}
                )
                raise
        
        return wrapper
    
    if callable(logger):
        func = logger
        logger = None
        threshold = threshold_ms
        return decorator(func)
    
    return decorator


@contextmanager
def log_operation(operation_name: str, logger: Optional[logging.Logger] = None, log_result: bool = True):
    """
    Context manager to automatically log operation start/end/duration.
    
    Usage:
        with log_operation("process_assembly", logger):
            # your code here
    """
    if logger is None:
        logger = get_logger("polylog.operations")
    
    start = time.time()
    logger.info(f"Starting: {operation_name}")
    
    try:
        yield logger
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        logger.error(
            f"Failed: {operation_name} after {elapsed_ms:.2f}ms: {str(e)}",
            exc_info=True,
            extra={"extra_data": {"operation": operation_name, "duration_ms": elapsed_ms}}
        )
        raise
    else:
        elapsed_ms = (time.time() - start) * 1000
        if log_result:
            logger.info(
                f"Completed: {operation_name} in {elapsed_ms:.2f}ms",
                extra={"extra_data": {"operation": operation_name, "duration_ms": elapsed_ms}}
            )


class LoggingContext:
    """Helper class for managing logging across multiple operations"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = get_logger(name, level)
    
    def info(self, msg: str, **extra_data):
        self.logger.info(msg, extra={"extra_data": extra_data} if extra_data else {})
    
    def debug(self, msg: str, **extra_data):
        self.logger.debug(msg, extra={"extra_data": extra_data} if extra_data else {})
    
    def warning(self, msg: str, **extra_data):
        self.logger.warning(msg, extra={"extra_data": extra_data} if extra_data else {})
    
    def error(self, msg: str, exc_info: bool = False, **extra_data):
        self.logger.error(msg, exc_info=exc_info, extra={"extra_data": extra_data} if extra_data else {})
    
    def critical(self, msg: str, **extra_data):
        self.logger.critical(msg, extra={"extra_data": extra_data} if extra_data else {})


# Pre-configured loggers for main modules
api_logger = get_logger("polylog.api")
engine_logger = get_logger("polylog.engine")
cache_logger = get_logger("polylog.cache")
placement_logger = get_logger("polylog.placement")
exploration_logger = get_logger("polylog.exploration")
validation_logger = get_logger("polylog.validation")


def clear_old_logs(days: int = 7):
    """Clean up log files older than specified days"""
    import os
    from pathlib import Path
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    for log_file in LOG_DIR.glob("*.log*"):
        if os.path.getmtime(log_file) < cutoff.timestamp():
            try:
                os.remove(log_file)
                api_logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                api_logger.error(f"Failed to delete log file {log_file}: {e}")


if __name__ == "__main__":
    # Test the logging system
    logger = get_logger("test")
    
    logger.info("Test info message", extra={"extra_data": {"test": True}})
    logger.debug("Test debug message")
    logger.warning("Test warning message")
    
    @log_error(logger)
    def test_func():
        logger.info("Inside test function")
        return "success"
    
    @log_performance(logger, threshold_ms=10)
    def slow_func():
        time.sleep(0.05)
        return "done"
    
    result = test_func()
    print(f"test_func result: {result}")
    
    result = slow_func()
    print(f"slow_func result: {result}")
    
    with log_operation("test_operation", logger):
        logger.info("Doing work...")
        time.sleep(0.02)
    
    print("\nLogging system test complete. Check ./logs/ directory for output.")
