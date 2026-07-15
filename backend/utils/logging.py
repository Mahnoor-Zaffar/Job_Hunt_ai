import logging
import sys

from backend.core.request_id import REQUEST_ID_CTX


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CTX.get("-")
        return True


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("job_hunting")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIDFilter())
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
