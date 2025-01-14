import os
import sys
from typing import Union
from contextlib import closing
import logging

import pymssql
from colorama import Style, Fore, init

CURRENT_DIR: str = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(CURRENT_DIR, '..')))
from config.config import settings_db  # noqa: E402


init(autoreset=True)

LOG_DIR: str = os.path.join(CURRENT_DIR, '..', 'log')
LOG_FILE_PATH: str = os.path.join(LOG_DIR, 'sql.log')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('sql_logger')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s __ %(levelname)s __ %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def sql_queries(request: str) -> Union[list[tuple], bool]:
    """
    Функция для выполнения запросов к базе данных.

    Parameters:
    ----------
    request : str
        SQL-запрос, который нужно выполнить.

    Return:
    ------
    - list: Возвращает результаты запроса SELECT для запросов, не требующих
    COMMIT.
    - bool: Возвращает True для запросов, требующих выполнения COMMIT.
    - bool: Возвращает False в случае ошибки выполнения запроса.

    Raises:
    ------
    - Raises Exception: В случае возникновения ошибки при выполнении запроса
    результаты будут записаны в .log файл.
    """

    try:
        with closing(pymssql.connect(
            user=settings_db.DB_USER,
            password=settings_db.DB_PSWD,
            host=settings_db.DB_HOST,
            database=settings_db.DB_NAME
        )) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(request)

                if cursor.description:
                    results = cursor.fetchall()
                    return results
                else:
                    connection.commit()
                    return True

    except Exception as e:
        print(
            Fore.RED + Style.DIM +
            'В ' +
            Style.RESET_ALL + Fore.WHITE + Style.BRIGHT +
            os.path.basename(__file__) +
            Style.RESET_ALL + Fore.RED + Style.DIM +
            ' произошла ошибка при выполнении запроса к БД:\n' +
            Style.RESET_ALL + Fore.WHITE + Style.BRIGHT +
            request + '\n' +
            Style.RESET_ALL + str(e)
        )
        logger.error(
            f'\nВ {__file__} произошла ошибка ' +
            f'при выполнении запроса к БД:\n{request}\n{str(e)}'
        )

        return False
