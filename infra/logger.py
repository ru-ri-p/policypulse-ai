# infra/logger.py
import logging
import os
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger.
    name should be the module name, e.g. get_logger("ingestion.tasks")
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        os.makedirs("logs", exist_ok=True)

        log_file = f"logs/{name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


if __name__ == "__main__":
    log = get_logger("test")
    log.info("This is an info message")
    log.warning("This is a warning")
    log.error("This is an error")
