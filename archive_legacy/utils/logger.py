"""
Logging configuration for JARVIS.
Provides structured logging with different levels and outputs.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging.handlers


class JsonFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data:
                continue
            log_data[key] = value

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """Format logs for console output with colors"""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        log_fmt = f"{color}{record.levelname:8}{reset} {record.name:25} {record.getMessage()}"

        if record.exc_info:
            log_fmt += f"\n{self.formatException(record.exc_info)}"

        return log_fmt


def get_logger(
    name: str,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = "logs",
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Formatters
    json_formatter = JsonFormatter()
    console_formatter = ConsoleFormatter()

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handlers
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Main log file
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "jarvis.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

        # Error-specific log file
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "errors.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        logger.addHandler(error_handler)

        # Performance logs
        perf_handler = logging.handlers.RotatingFileHandler(
            log_path / "performance.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(json_formatter)
        # Only log performance metrics (filter would be applied)
        logger.addHandler(perf_handler)

    return logger


def setup_root_logger(level: str = "INFO"):
    """Configure root logger for the entire application"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


# Usage examples:
# logger = get_logger(__name__, level="DEBUG")
# logger.info("Message", extra={"component": "orchestrator", "correlation_id": "123"})
# logger.error("Error occurred", exc_info=True)
