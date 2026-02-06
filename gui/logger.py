import logging
import sys

def setup_logger():
    logger = logging.getLogger("TPLabel")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s][%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    #log ra terminal
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    #log ra file (tùy chọn)
    # fh = logging.FileHandler("tplabel.log", encoding="utf-8")
    # fh.setLevel(logging.DEBUG)
    # fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)
        # logger.addHandler(fh)

    return logger