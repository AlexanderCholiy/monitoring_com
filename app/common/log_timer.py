import os
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

from colorama import Fore, Style, init


init(autoreset=True)

LOG_DIR: str = os.path.join(os.path.dirname(__file__), '..', '..', 'log')
LOG_FILE_PATH: str = os.path.join(LOG_DIR, 'timer.log')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('timer_logger')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s __ %(levelname)s __ %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_timer(func_name: Optional[str] = None):
    """Декоратор для подсчёта времени выполнения функции."""
    def decorator(func: Callable):
        name = func_name or func.__name__

        def wrapper(*args, **kwargs) -> Callable:
            start: datetime = datetime.now()
            result = func(*args, **kwargs)
            execution_time: timedelta = datetime.now() - start

            if execution_time.total_seconds() >= 60:
                print(
                    Fore.CYAN + Style.DIM +
                    f'Функция {Fore.WHITE + Style.BRIGHT + name} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM +
                    'выполнялась ' +
                    Fore.WHITE + Style.BRIGHT +
                    f'{execution_time // timedelta(minutes=1)} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM + 'минут(ы).'
                )
                log_message: str = (
                    f'Функция {name} выполнялась ' +
                    f'{execution_time // timedelta(minutes=1)} минут(ы).'
                )
            elif execution_time.total_seconds() >= 1:
                print(
                    Fore.CYAN + Style.DIM +
                    f'Функция {Fore.WHITE + Style.BRIGHT + name} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM +
                    'выполнялась ' +
                    Fore.WHITE + Style.BRIGHT +
                    f'{round(execution_time.total_seconds(), 1)} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM + 'секунд(ы).'
                )
                log_message: str = (
                    f'Функция {name} выполнялась ' +
                    f'{round(execution_time.total_seconds(), 1)} секунд(ы).'
                )
            else:
                print(
                    Fore.CYAN + Style.DIM +
                    f'Функция {Fore.WHITE + Style.BRIGHT + name} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM +
                    'выполнялась ' +
                    Fore.WHITE + Style.BRIGHT +
                    f'{round(execution_time.total_seconds(), 3)} ' +
                    Style.RESET_ALL + Fore.CYAN + Style.DIM + 'микросекунд(ы).'
                )
                log_message: str = (
                    f'Функция {name} выполнялась ' +
                    f'{round(execution_time.total_seconds(), 3)} ' +
                    'микросекунд(ы).'
                )

            logger.info(log_message)

            return result

        return wrapper

    return decorator
