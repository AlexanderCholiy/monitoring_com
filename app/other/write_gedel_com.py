import os

import pandas as pd
from colorama import Fore, Style, init

from database.db_conn import sql_queries


init(autoreset=True)


def write_gedel_com(file_path: str):
    if not os.path.exists(file_path):
        return

    df = pd.read_json(file_path)
    columns_to_keep = [
        'IP', 'Command SRP_0 (Gedel)', 'Command COM_1 (Gedel)',
        'Command SRP_0 (Gedel_Old)', 'Command COM_1 (Gedel_Old)'
    ]
    df = df.drop(df.columns.difference(columns_to_keep), axis=1)
    df = df[
        df['Command COM_1 (Gedel)'].str.contains('Command_OK')
        | df['Command SRP_0 (Gedel)'].str.contains('Command_OK')
        | df['Command COM_1 (Gedel_Old)'].str.contains('Command_OK')
        | df['Command SRP_0 (Gedel_Old)'].str.contains('Command_OK')
    ]
    df = df.reset_index(drop=True)

    def gedel_com(device_ip: str, device: str, correct_response: int) -> None:
        device_map = {
            'Command SRP_0 (Gedel_Old)': (0, 2),
            'Command COM_1 (Gedel_Old)': (1, 3),
            'Command SRP_0 (Gedel)': (0, 0),
            'Command COM_1 (Gedel)': (1, 1),
        }

        if device in device_map:
            COM_Device, COM_Type = device_map[device]
        else:
            return

        try:
            response: str = row[device].split('\n')[2]

            if device in ('Command SRP_0 (Gedel)', 'Command COM_1 (Gedel)'):
                response: list = response.split(' ')
                if len(response) < 6:
                    return
                # Пример ответа < 02 04 02 00 08 bc b9
                response: int = int(response[5], 16)
            else:
                response: list = response.split(' ')
                if len(response) < 3:
                    return
                # Пример ответа < 02 04 02 00 08 bc b9
                response: int = int(response[2], 16)

        except (ValueError, IndexError):
            return

        if response == correct_response:
            data = sql_queries(f'''
            SELECT
                COUNT(*)
            FROM
                Msys_COM
            WHERE
                COM_ModemMac IN (
                SELECT
                    ModemCounter
                FROM
                    MSys_Modems
                WHERE
                    ModemID = '{device_ip}'
                    AND ModemLevel IN (102, 2)
                )
                AND COM_Device = {COM_Device}
            ''')
            data = data[0][0] if data else data
            if data == 0:
                sql_queries(f'''
                INSERT INTO
                    MSys_COM (
                        COM_Device,
                        COM_Type,
                        COM_Pole,
                        COM_ModemMac
                    )
                VALUES (
                    {COM_Device},
                    {COM_Type},
                    (
                        SELECT TOP 1 ModemPole
                        FROM MSys_Modems
                        WHERE
                            ModemID = '{device_ip}'
                            AND ModemLevel IN (102, 2)
                    ),
                    (
                        SELECT TOP 1 ModemCounter
                        FROM MSys_Modems
                        WHERE
                            ModemID = '{device_ip}'
                            AND ModemLevel IN (102, 2)
                    )
                )
                ''')
            else:
                sql_queries(f'''
                UPDATE
                    MSys_COM
                SET
                    COM_Type = {COM_Type}
                WHERE
                    COM_Device = {COM_Device}
                    AND COM_ModemMac = (
                        SELECT TOP 1
                            ModemCounter
                        FROM
                            MSys_Modems
                        WHERE
                            ModemID = '{device_ip}'
                            AND ModemLevel IN (102, 2)
                    )
                ''')

    for index, row in df.iterrows():
        device_ip = row['IP']
        percent_complete = round((index / len(df)) * 100, 2)
        # Порядок важен, сначала проверяем ответ для старых SOM Gedel и если
        # ответ для нового будет положительным перезапишем его.
        print(
            (
                Fore.BLUE + Style.NORMAL +
                'Обновляем список COM/SRP Gedel в таблице MSys_COM:' +
                Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
            ), end='\r'
        )
        gedel_com(device_ip, 'Command SRP_0 (Gedel_Old)', 4)
        gedel_com(device_ip, 'Command COM_1 (Gedel_Old)', 4)
        gedel_com(device_ip, 'Command SRP_0 (Gedel)', 8)
        gedel_com(device_ip, 'Command COM_1 (Gedel)', 7)
    if len(df) > 0:
        print()
