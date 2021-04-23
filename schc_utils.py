import logging as log


def init_logging(logfile):
    log.basicConfig(filename=logfile,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=log.DEBUG)


def print_and_log(text, level):
    print(text)
    if level == 'DEBUG':
        log.debug(text)
    elif level == 'INFO':
        log.info(text)
    elif level == 'WARNING':
        log.warning(text)
    elif level == 'ERROR':
        log.error(text)