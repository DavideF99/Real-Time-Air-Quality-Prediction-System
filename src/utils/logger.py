"""
Logging System Module

Professional logging setup using Loguru library.

Features:
- Console output with color coding (INFO=green, ERROR=red, etc.)
- File output with rotation (creates new file when size limit reached)
- Different log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Automatic timestamp and context information

Learning Notes:
- Loguru is much simpler than Python's built-in logging module
- Logs help debug issues and monitor production systems
- Always log important operations (API calls, data processing, errors)
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from src.utils.config import get_config


class LoggerSetup:
    """
    Logger configuration and setup.
    
    This class initializes the logging system with appropriate
    settings for console and file output.
    """
    
    _initialized = False
    
    @classmethod
    def setup(cls, 
              log_level: Optional[str] = None,
              log_to_file: bool = True,
              log_dir: Optional[Path] = None) -> None:
        """
        Initialize the logging system.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to save logs to files
            log_dir: Directory for log files (uses config default if None)
            
        Learning Note: This method is idempotent - safe to call multiple times
        """
        
        if cls._initialized:
            return
        
        # Remove default handler
        logger.remove()
        
        # Get configuration
        config = get_config()
        
        if log_level is None:
            log_level = config.get_log_level()
        
        if log_dir is None:
            log_dir = config.get_log_dir()
        
        # Console handler with color formatting
        # Learning Note: <level> tag colorizes the output automatically
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=log_level,
            colorize=True
        )
        
        if log_to_file:
            # File handler for all logs
            logger.add(
                log_dir / "aqi_predictor_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level="DEBUG",  # Save everything to file
                rotation="00:00",  # Create new file at midnight
                retention="30 days",  # Keep logs for 30 days
                compression="zip"  # Compress old logs
            )
            
            # Separate file for errors only
            logger.add(
                log_dir / "errors_{time:YYYY-MM-DD}.log",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{extra}",
                level="ERROR",
                rotation="100 MB",  # Create new file when 100MB reached
                retention="90 days",  # Keep error logs longer
                compression="zip",
                backtrace=True,  # Show full traceback
                diagnose=True  # Show variable values in traceback
            )
        
        cls._initialized = True
        logger.info("Logging system initialized")
        logger.info(f"Log level: {log_level}")
        if log_to_file:
            logger.info(f"Log directory: {log_dir}")


def get_logger(name: str = None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        
    Returns:
        Logger instance
        
    Usage:
        from src.utils.logger import get_logger
        
        logger = get_logger(__name__)
        logger.info("This is an info message")
        logger.error("This is an error message")
        
    Learning Note: Using __name__ helps identify which module generated each log
    """
    
    # Initialize logging if not already done
    if not LoggerSetup._initialized:
        LoggerSetup.setup()
    
    # Loguru's logger is global, but we can bind context
    if name:
        return logger.bind(name=name)
    return logger


def log_function_call(func):
    """
    Decorator to automatically log function calls.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return arg1 + arg2
    
    This will log when the function is called and when it returns.
    
    Learning Note: Decorators wrap functions to add extra functionality
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


if __name__ == "__main__":
    """
    Test the logging system.
    
    Run this file directly to see different log levels:
    python src/utils/logger.py
    """
    
    # Initialize logging
    LoggerSetup.setup(log_level="DEBUG")
    
    # Get logger
    test_logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("LOGGING SYSTEM TEST")
    print("=" * 60 + "\n")
    
    # Test different log levels
    test_logger.debug("This is a DEBUG message (detailed information)")
    test_logger.info("This is an INFO message (general information)")
    test_logger.warning("This is a WARNING message (something to watch)")
    test_logger.error("This is an ERROR message (something went wrong)")
    
    # Test logging with context
    test_logger.info("Testing with context", city="Bangkok", temperature=32.5)
    
    # Test function decorator
    @log_function_call
    def sample_calculation(a, b):
        """Sample function to test decorator."""
        return a + b
    
    result = sample_calculation(10, 20)
    test_logger.info(f"Calculation result: {result}")
    
    # Simulate an error
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        test_logger.error(f"Caught an error: {e}")
    
    print("\n" + "=" * 60)
    print("LOGGING TEST COMPLETED! 🎉")
    print("=" * 60)
    print("\nCheck these locations for log files:")
    config = get_config()
    log_dir = config.get_log_dir()
    print(f"📁 {log_dir}")
    print("\nYou should see:")
    print("  - aqi_predictor_[DATE].log (all logs)")
    print("  - errors_[DATE].log (errors only)")