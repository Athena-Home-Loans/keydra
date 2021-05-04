import logging
import os

from pythonjsonlogger import jsonlogger


def setup_logging(log_level):
    logger = logging.getLogger()

    logger.setLevel(log_level)

    handler = logging.StreamHandler()

    handler.setFormatter(
        jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(lambda)s %(message)s'
        )
    )

    logger.addHandler(handler)
    logger.removeHandler(logger.handlers[0])


def get_logger():
    logger = logging.getLogger()

    logger = logging.LoggerAdapter(
        logger,
        {'lambda': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '')}
    )

    return logger
