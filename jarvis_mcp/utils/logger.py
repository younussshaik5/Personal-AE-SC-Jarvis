"""Structured logging for JARVIS."""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional


class JARVISLogger:
    """Centralized logger for JARVIS components."""

    def __init__(self, name: str, logs_dir: Optional[Path] = None):
        self.name = name
        self.logs_dir = logs_dir or Path.home() / ".claude" / "jarvis_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger(f"jarvis.{name}")
        if self.logger.handlers:
            return  # Already configured
        
        self.logger.setLevel(logging.DEBUG)

        # Console handler (human-readable)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console_fmt = logging.Formatter(
            '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console.setFormatter(console_fmt)
        self.logger.addHandler(console)

    def log_event(self, level: str, event: str, **kwargs):
        """Log a structured event."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": self.name,
            "event": event,
            **kwargs
        }
        getattr(self.logger, level)(json.dumps(log_data))

    def debug(self, event: str, **kwargs):
        self.log_event("debug", event, **kwargs)

    def info(self, event: str, **kwargs):
        self.log_event("info", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self.log_event("warning", event, **kwargs)

    def error(self, event: str, **kwargs):
        self.log_event("error", event, **kwargs)

    def critical(self, event: str, **kwargs):
        self.log_event("critical", event, **kwargs)


def get_logger(name: str) -> JARVISLogger:
    """Get a logger instance."""
    return JARVISLogger(name)


def setup_logger(name: str) -> logging.Logger:
    """Setup and return a basic Python logger."""
    logger = logging.getLogger(f"jarvis.{name}")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)
    
    return logger
