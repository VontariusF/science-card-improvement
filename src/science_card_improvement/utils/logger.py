"""Structured logging configuration with multiple output formats."""
import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, MutableMapping, Optional, Type, Union

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from structlog.types import Processor

from science_card_improvement.config.settings import get_settings


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for logging."""

    def default(self, obj: Any) -> Any:
        """Handle special types."""
        if isinstance(obj, (datetime, Path)):
            return str(obj)
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> structlog.BoundLogger:
    """Setup structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Output format (json, console, colored)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    settings = get_settings()

    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format

    # Configure Python logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[],
    )

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    logging.root.addHandler(console_handler)

    # Add file handler if enabled
    if settings.log_file_enabled or log_file:
        if log_file:
            file_path = log_file
        elif settings.logs_dir:
            file_path = settings.logs_dir / f"{settings.app_name.lower().replace(' ', '_')}.log"
        else:
            file_path = Path("logs") / f"{settings.app_name.lower().replace(' ', '_')}.log"

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(file_path),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logging.root.addHandler(file_handler)

    # Configure structlog processors
    shared_processors: list[Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        CallsiteParameterAdder(
            parameters=[
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
    ]

    # Add environment context
    def add_environment(
        logger: Any,
        method_name: str,
        event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        """Add environment context to logs."""
        event_dict["environment"] = settings.environment
        event_dict["app_name"] = settings.app_name
        event_dict["app_version"] = settings.app_version
        return event_dict

    shared_processors.append(add_environment)

    # Configure output format
    renderer: Any
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer(
            serializer=lambda obj, **kwargs: json.dumps(obj, cls=CustomJSONEncoder)
        )
    elif log_format == "colored":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib processor formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    # Apply formatter to all handlers
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)

    return structlog.get_logger()


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    _logger: Optional[structlog.BoundLogger] = None

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get a logger instance bound to this class."""
        if self._logger is None:
            self._logger = structlog.get_logger(self.__class__.__name__)
        return self._logger

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log error message with optional exception."""
        if exception:
            kwargs["exception"] = str(exception)
            kwargs["exception_type"] = type(exception).__name__
        self.logger.error(message, **kwargs)

    def log_critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(message, **kwargs)


class RequestLogger:
    """Context manager for logging requests with timing."""

    def __init__(self, logger: structlog.BoundLogger, operation: str, **context: Any) -> None:
        """Initialize request logger."""
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> "RequestLogger":
        """Start timing and log request."""
        self.start_time = datetime.utcnow()
        self.logger.info(
            f"Starting {self.operation}",
            operation=self.operation,
            **self.context,
        )
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> bool:
        """Log request completion with duration."""
        if self.start_time is None:
            duration_ms = 0
        else:
            duration_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                operation=self.operation,
                duration_ms=duration_ms,
                status="success",
                **self.context,
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                operation=self.operation,
                duration_ms=duration_ms,
                status="error",
                exception=str(exc_val),
                exception_type=exc_type.__name__,
                **self.context,
            )
        return False


# Initialize default logger
logger = setup_logging()


# Convenience functions
def log_debug(message: str, **kwargs: Any) -> None:
    """Log debug message."""
    logger.debug(message, **kwargs)


def log_info(message: str, **kwargs: Any) -> None:
    """Log info message."""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log warning message."""
    logger.warning(message, **kwargs)


def log_error(message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
    """Log error message with optional exception."""
    if exception:
        kwargs["exception"] = str(exception)
        kwargs["exception_type"] = type(exception).__name__
    logger.error(message, **kwargs)


def log_critical(message: str, **kwargs: Any) -> None:
    """Log critical message."""
    logger.critical(message, **kwargs)
