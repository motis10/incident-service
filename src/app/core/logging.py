"""
Logging infrastructure for the Netanya Incident Service.
Provides structured logging with correlation IDs for request tracing.
"""
import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO", enable_json: bool = False) -> None:
    """
    Set up structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Whether to use JSON formatting for logs
    """
    # Create formatter
    if enable_json:
        # JSON formatter for production/Cloud Run
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s", "lineno": %(lineno)d}'
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# Create application logger
logger = logging.getLogger("netanya_incident_service")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name, defaults to calling module
        
    Returns:
        Configured logger instance
    """
    if name:
        return logging.getLogger(f"netanya_incident_service.{name}")
    return logger
