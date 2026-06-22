import logging
import json
import sys
from datetime import datetime, timezone


class SystemJSONFormatter(logging.Formatter):

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "fastapi_backend",
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": f"{record.module}.py",
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def get_system_logger(name="license_plate_api"):

    logger = logging.getLogger(name)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SystemJSONFormatter())

    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


log = get_system_logger()
