#!/usr/bin/env python3
"""
Structured logging for JARVIS with JSON output and log rotation.
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JARVISLogger:
    """Centralized logger for JARVIS components."""

    def __init__(self, name: str, logs_dir: Optional[Path] = None):
        from pathlib import Path
        self.name = name
        self.logs_dir = logs_dir or Path.cwd() / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        self.logger = logging.getLogger(f"jarvis.{name}")
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

        # JSON file handler (structured)
        json_file = self.logs_dir / f"{name}.jsonl"
        json_handler = logging.handlers.RotatingFileHandler(
            json_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)

        # Error-specific file
        error_file = self.logs_dir / "errors" / f"{name}_error.jsonl"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10*1024*1024,
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)

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


class JSONFormatter(logging.Formatter):
    """Format log record as JSON."""
    def format(self, record):
        log_object = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage()
        }
        # Extract extra fields if present
        extra = getattr(record, '__dict__', {})
        if 'component' in extra:
            log_object["component"] = extra['component']
        if 'event' in extra:
            log_object["event"] = extra['event']
        return json.dumps(log_object)


# Convenience function for other modules
def get_logger(name: str) -> JARVISLogger:
    return JARVISLogger(name)