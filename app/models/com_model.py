import os
import asyncio
from typing import Union
from datetime import datetime

from colorama import Fore, Style, init

from database.db_conn import sql_queries
from database.requests.select_unwork_com import select_unwork_com
from database.requests.select_com_to_check import select_com_to_check
from database.requests.update_com_table_by_somrecords import (
    update_com_table_by_somrecords
)
from database.requests.update_com_srp_records import (
    select_mac, select_last_record_datetime, update_srp_value,
    select_com_value, update_com_value, add_com_value
)
from database.requests.select_controllers_to_connect import (
    select_controllers_to_connect
)
from app.controllers.send_firmware import update_com
from app.controllers.restart_crontab import restart_crontab_main
from app.controllers.find_com import controllers_connect_com_main
from app.other.write_conn_controllers_log import write_conn_controllers_log
from app.other.write_gedel_com import write_gedel_com
from app.other.write_allics_com import write_allics_com


init(autoreset=True)
CURRENT_DIR: str = os.path.dirname(__file__)
RESULTS_COM_PATH: str = os.path.join(
    CURRENT_DIR, '..', '..', 'data', 'find_com.json'
)


class COM:
    def __init__(self):
        pass

    def unwork_com_ip(
        self, controller_version: str, com_types_id: list[int]
    ) -> Union[list[str], bool]:
        """
        Список ip контроллеров у которых есть COM, но они не присылают свои
        показания.

        Parameters:
        ----------
        - modem_version: Версия контроллера.
        - com_types_id: ID версии COM.
        """
        result = sql_queries(
            select_unwork_com(controller_version, com_types_id)
        )
        if result:
            return [row[0] for row in result]
        return result

    def send_com_firmware_to_controllers(
        self,
        controllers_ip: list[str], firmware_folder_path: str, timeout: int = 60
    ) -> None:
        """
        Отправка прошивки для корректной работы COM на контроллеры.

        Parameters:
        ----------
        - controllers_ip: ip адреса контроллеров.
        - firmware_folder_path: папка с прошивкой контроллера.
        - timeout: время ожидания выполнения команды.
        """
        update_com(controllers_ip, firmware_folder_path, timeout)

    @property
    def com_to_check(self) -> Union[list[tuple[str, str]], bool]:
        """
        Cписок устройств содержащий в себе кортежи из пары ip и id типа
        устройства для COM которые не скидывали свои показания, или прислали
        свои показания 3 дня назад, или у которых некорректная дата показаний.
        """
        return sql_queries(select_com_to_check())

    def restart_crontab(
        self, connect_timeout: int = 30, command_timeout: int = 30
    ):
        """
        Подключение к контроллерам РЩУ в асинхронном режиме для ручной передачи
        показаний COM и SRP и перезапуска crontab.
        """
        asyncio.run(restart_crontab_main(
            self.com_to_check, connect_timeout, command_timeout
            )
        )

    def update_msys_com(self, n_days: int = 100):
        """
        Добавляем в MSys_COM список новых COM, которые сохранили свои показания
        в таблице MSys_SomRecords за последние n дней. Далее по показаниям в
        таблице MSys_SomRecords устанавливаем тип устройства и дату последних
        показаний COM и SRP.
        """
        def update_process(messega: str, percent_complete: float):
            print(
                (
                    Fore.BLUE + Style.NORMAL +
                    messega +
                    Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
                ), end='\r'
            )

        if not sql_queries(update_com_table_by_somrecords(n_days)):
            return

        modems_mac = sql_queries(select_mac())
        if not modems_mac:
            return

        for index, row in enumerate(modems_mac, start=1):
            modem_mac = row[0]
            percent_complete = round((index / len(modems_mac)) * 100, 2)
            srp_datetime = sql_queries(
                select_last_record_datetime(modem_mac, True)
            )
            if not srp_datetime:
                update_process(
                    'Обновляем список SRP в таблице MSys_COM: ',
                    percent_complete
                )
                continue

            record_srp_datetime = datetime.strptime(
                (str(srp_datetime[0][0]) + ' ' + str(srp_datetime[0][1])),
                '%Y-%m-%d %H:%M:%S'
            )
            sql_queries(update_srp_value(modem_mac, record_srp_datetime))
            update_process(
                'Обновляем список SRP в таблице MSys_COM: ', percent_complete
            )
        else:
            print()

        for index, row in enumerate(modems_mac, start=1):
            modem_mac = row[0]
            percent_complete = round((index / len(modems_mac)) * 100, 2)
            com_datetime = sql_queries(
                select_last_record_datetime(modem_mac, False)
            )
            if not com_datetime:
                update_process(
                    'Обновляем список COM в таблице MSys_COM: ',
                    percent_complete
                )
                continue

            record_com_datetime = datetime.strptime(
                (str(com_datetime[0][0]) + ' ' + str(com_datetime[0][1])),
                '%Y-%m-%d %H:%M:%S'
            )
            com_position = sql_queries(select_com_value(modem_mac))
            if not com_position:
                update_process(
                    'Обновляем список COM в таблице MSys_COM: ',
                    percent_complete
                )
                continue
            com_position_value = com_position[0][0]
            if com_position_value > 0:
                sql_queries(update_com_value(modem_mac, record_com_datetime))
            else:
                sql_queries(add_com_value(modem_mac, record_com_datetime))

            update_process(
                'Обновляем список COM в таблице MSys_COM: ', percent_complete
            )

        else:
            print()

    @property
    def controllers_to_connect(self) -> list[str]:
        controllers_ip = sql_queries(select_controllers_to_connect())
        return [row[0] for row in controllers_ip] if controllers_ip else list()

    def find_new_com(
        self, connect_timeout: int = 30, command_timeout: int = 30
    ):
        """
        Подключение к контроллерам РЩУ для поиска SRP и COM.

        Parameters:
        ----------
        - connect_timeout: время в течение которого мы должны успеть
        подключиться к контроллеру.
        - command_timeout: время за которое команда должна быть выполнена.
        """
        asyncio.run(
            controllers_connect_com_main(
                self.controllers_to_connect[:3], connect_timeout, command_timeout
            )
        )

        write_conn_controllers_log(RESULTS_COM_PATH)
        write_gedel_com(RESULTS_COM_PATH)
        write_allics_com(RESULTS_COM_PATH)
