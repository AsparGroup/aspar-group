import logging


def configure_json_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","service":"%(name)s","msg":"%(message)s"}',
    )
    return logging.getLogger(name)
