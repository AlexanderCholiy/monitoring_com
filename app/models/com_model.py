import asyncio
from typing import Union

from database.db_conn import sql_queries
from database.requests.select_unwork_com import select_unwork_com
from database.requests.select_com_to_check import select_com_to_check
from app.controllers.send_firmware import update_com
from app.controllers.restart_crontab import restart_crontab_main


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
