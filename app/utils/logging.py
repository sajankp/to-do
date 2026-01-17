import logging
import sys

import structlog
from structlog.types import EventDict, Processor

from app.config import get_settings

settings = get_settings()

UVICORN_LOGGERS = ["uvicorn.error", "uvicorn.access"]


def _drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`.
    We don't need it.
    """
    event_dict.pop("color_message", None)
    return event_dict


def _drop_internal_structlog_keys(_, __, event_dict: EventDict) -> EventDict:
    """
    Remove internal structlog metadata that shouldn't appear in production logs.
    """
    event_dict.pop("_record", None)
    event_dict.pop("_from_structlog", None)
    return event_dict


def setup_logging():
    """
    Configure structlog and standard logging.
    """

    # Shared processors for both structlog and standard logging
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Specific processors for structlog
    if settings.is_production:
        processors = shared_processors + [
            _drop_color_message_key,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Intercept standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            _drop_color_message_key,
            _drop_internal_structlog_keys,
            structlog.processors.JSONRenderer()
            if settings.is_production
            else structlog.dev.ConsoleRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # Configure uvicorn loggers to prevent duplicate output
    # By setting propagate=False, uvicorn won't print to its own handlers
    for logger_name in UVICORN_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.handlers = [handler]
        logger.propagate = False
