def select_unwork_com(modem_version: str, com_types_id: list[int]) -> str:
    return (f'''
    SELECT DISTINCT
        RTRIM(m.ModemID)
    FROM
        MSys_COM as c LEFT OUTER JOIN MSys_Modems as m
        ON c.COM_ModemMac = m.ModemCounter
    WHERE
        m.ModemLevel IN (102, 2)
        AND m.ModemStatus IN (1000, 1004)
        AND ModemVersion LIKE '{modem_version}%'
        AND c.COM_AlarmTimeStamp IS NULL
        AND c.COM_Type IN ({', '.join(map(str, com_types_id))})
    ''')
