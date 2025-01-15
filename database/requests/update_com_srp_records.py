from datetime import datetime


def select_mac() -> str:
    return ('''
        SELECT DISTINCT COM_ModemMac
        FROM Msys_COM
        WHERE COM_ModemMac IS NOT NULL
    ''')


def select_last_record_datetime(modem_mac: str, srp_status: bool) -> str:
    """
    Parameters:
    ----------
    - COM: srp_status = False.
    - SRP: srp_status = True.
    """
    status_condition = "IS NOT NULL" if srp_status else "IS NULL"
    return f'''
    SELECT TOP 1
        RecordDate,
        RecordTime
    FROM
        MSys_SomRecords
    WHERE
        RecordMac = '{modem_mac}'
        AND SrpStatus {status_condition}
    ORDER BY
        RecordDate DESC, RecordTime DESC
    '''


def update_srp_value(modem_mac: str, record_datetime: datetime) -> str:
    """SRP всегда идет 0 устройством. Далее логически идут COM."""
    return (f'''
    UPDATE
        Msys_COM
    SET
        COM_AlarmTimeStamp = '{record_datetime}',
        COM_Device = 0
    WHERE
        COM_ModemMac = '{modem_mac}'
        AND (
            COM_Device IS NULL OR COM_Device = 0
        )
    ''')


def select_com_value(modem_mac: str) -> str:
    return (f'''
    SELECT
        COUNT(*)
    FROM
        MSys_COM
    WHERE
        COM_ModemMac = '{modem_mac}'
        AND (
            COM_Device IS NULL OR COM_Device >= 1
        )
    ''')


def update_com_value(modem_mac: str, record_datetime: datetime) -> str:
    return (f'''
    UPDATE
        Msys_COM
    SET
        COM_AlarmTimeStamp = '{record_datetime}'
    WHERE
        -- COM на опоре может быть несколько уровней, поэтому COM_Device >= 1
        COM_ModemMac = '{modem_mac}'
        AND (
            COM_Device IS NULL OR COM_Device >= 1
        )
    ''')


def add_com_value(modem_mac: str, record_datetime: datetime) -> str:
    return (f'''
    INSERT INTO
        Msys_COM (
        COM_Device,
        COM_Type,
        COM_Pole,
        COM_Cabinet,
        COM_AlarmTimeStamp,
        COM_ModemMac
    )
    VALUES (
            1,
            NULL,
            (
                SELECT TOP 1 ModemPole
                FROM MSys_Modems
                WHERE ModemCounter = '{modem_mac}' AND ModemLevel IN (102, 2)
            ),
            NULL,
            '{record_datetime}',
            '{modem_mac}'
    )
    ''')
