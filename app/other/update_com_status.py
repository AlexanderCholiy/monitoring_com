from datetime import datetime, timedelta

from colorama import Fore, Style, init

from database.db_conn import sql_queries
from database.requests.update_com_status_records import (
    update_com_status_records
)


init(autoreset=True)


def update_process(percent_complete: float):
    print(
        (
            Fore.BLUE + Style.NORMAL +
            'Обновляем статусы в таблице MSys_COM: ' +
            Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
        ), end='\r'
    )


def update_com_srp_status() -> None:
    result = sql_queries(update_com_status_records())
    if not result:
        return

    current_date_time = datetime.now()
    for index, row in enumerate(result, start=1):
        percent_complete = round((index / len(result)) * 100, 2)
        update_process(percent_complete)
        COM_Device = row[0]
        COM_Status = row[2]
        COM_AlarmTimeStamp = row[4]
        ModemStatus = row[5]
        ModemCounter = row[6]
        SrpStatus = row[10]
        VBat = float(row[11]) if row[11] else 0
        Out2c = float(row[12]) if row[12] else 0
        Out1c = float(row[13]) if row[13] else 0
        Out1overc = row[17]
        Out2overc = row[18]
        Out1disc = row[19]
        Out2disc = row[20]

        if COM_AlarmTimeStamp is None:
            COM_AlarmTimeStamp = datetime(2000, 1, 1)
        time_difference = current_date_time - COM_AlarmTimeStamp

        # Показания COM не приходят или контроллер не в сети:
        if not COM_AlarmTimeStamp or ModemStatus == 1001:
            COM_Status = 7001
        # Показания не приходят более 24 часов:
        elif time_difference > timedelta(hours=24):
            COM_Status = 7002
        # Фильтр для SRP:
        elif COM_Device == 0:
            # Неисправна батарея:
            COM_Status = 7004 if SrpStatus == 1 else 7000
        # Фильтр для COM:
        # КЗ или обрыв:
        elif 1 in (Out1overc, Out2overc, Out1disc, Out2disc):
            COM_Status = 7003
        # Перегорела лампа (в сумме все 3 лампы должны давать 600мА).
        elif sum([Out1c, Out2c]) / 3 < 150:
            COM_Status = 7004
        # Неисправна батарея.
        elif VBat < 20:
            COM_Status = 7004
        else:
            COM_Status = 7000

        device_condition = (
            f'AND COM_Device = {COM_Device}'
        ) if COM_Device is not None else 'AND COM_Device IS NULL'

        sql_queries(f'''
        UPDATE
            Msys_COM
        SET
            COM_Status = {COM_Status}
        WHERE
            COM_ModemMac = '{ModemCounter}'
            {device_condition}
        ''')

    if len(result) > 0:
        print()
