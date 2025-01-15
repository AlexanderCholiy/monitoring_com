import os
import argparse

from app.common.input_selection import input_selection
from app.common.log_timer import log_timer
from app.models.com_model import COM

COM_FIRMWARE_PATH: str = '/opt/bin/factories/som-factories'
ALLICS_CONTRILLERS: list[tuple[str]] = [
    ('v1.f', '1f-som-allics-factory'),
    ('Rev1.H', 'rschu20-som-allics-factory'),
    ('TMV', 'tmv-som-allics-factory'),
    ('WB7', 'wb7-som-allics-factory'),
]
GEDEL_CONTROLLERS: list[tuple[str]] = [
    ('v1.f', '1f-som-gedel-factory'),
    ('Rev1.H', 'rschu20-som-gedel-factory'),
    ('TMV', 'tmv-som-gedel-factory'),
    ('WB7', 'wb7-som-gedel-factory'),
]


@log_timer()
def check_com(conn_to_controllers: bool):
    com = COM()
    if conn_to_controllers:
        for controller_version, firmware in GEDEL_CONTROLLERS:
            com.send_com_firmware_to_controllers(
                com.unwork_com_ip(controller_version, [0, 1, 2, 3]),
                os.path.join(COM_FIRMWARE_PATH, firmware)
            )
        for controller_version, firmware in ALLICS_CONTRILLERS:
            com.send_com_firmware_to_controllers(
                com.unwork_com_ip(controller_version, [21]),
                os.path.join(COM_FIRMWARE_PATH, firmware)
            )
        com.restart_crontab()

    com.update_msys_com()

    if conn_to_controllers:
        com.find_new_com()

    com.update_com_status()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Программа для поиска COM на контроллерах.'
    )
    parser.add_argument(
        '--conn_to_controllers', type=input_selection,
        help=(
            'Укажите True для поиска COM с подключением к контроллерам ' +
            'или False для поиска новых COM по данным в БД.'
        ),
        required=False, default=False
    )

    parser_args = parser.parse_args()
    conn_to_controllers = parser_args.conn_to_controllers

    check_com(conn_to_controllers)
