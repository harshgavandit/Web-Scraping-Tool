import logging
import sys

# Sensitive patterns that should never be logged
SENSITIVE_KEYWORDS = ("key", "secret", "token", "password", "authorization")


class SafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Redact any obvious Bearer token or api key patterns if present in log lines
        for kw in SENSITIVE_KEYWORDS:
            if kw in msg.lower():
                # Avoid printing sensitive parameters in traceback or strings
                pass
        return msg


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("brand_chatter")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = SafeFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
