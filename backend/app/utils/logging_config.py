import logging
from logging.handlers import RotatingFileHandler
import os


def configure_logging(app) -> None:
    log_dir = os.path.join(app.instance_path, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "guardian_ledger.log")

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )

    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))

    # Don't let request bodies (passwords, tokens) ever hit the log.
    # Anything that needs auditing goes through approval_logs in the DB
    # with an explicit, reviewed set of fields instead.
