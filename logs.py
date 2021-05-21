import logging


def make_logger(log_name: str):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(f'logs/{log_name}.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
