from pathlib import Path
import logging


def root_path():
    return Path(__file__).parent


def set_up_logger(log_file_name=None, default_logging_level=logging.INFO):
    (root_path() / 'io' / 'out' / 'logs').mkdir(parents=True, exist_ok=True)
    if not log_file_name:
        log_path = root_path() / 'io' / 'out' / 'logs' / 'main.log'
    else:
        log_path = root_path() / 'io' / 'out' / 'logs' / (log_file_name + '.log')
    logging.basicConfig(filename=str(log_path), level=default_logging_level,
                        format='%(asctime)-5s %(name)-5s %(levelname)-10s %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S')
    logging.VERBOSE = 5
    logging.addLevelName(logging.VERBOSE, "VERBOSE")
    logging.Logger.verbose = lambda inst, msg, *args, **kwargs: inst.log(logging.VERBOSE, msg, *args, **kwargs)
    logging.verbose = lambda msg, *args, **kwargs: logging.log(logging.VERBOSE, msg, *args, **kwargs)