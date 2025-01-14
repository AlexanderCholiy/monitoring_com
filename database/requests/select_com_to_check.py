def select_com_to_check() -> str:
    return ('''
    SELECT DISTINCT
        RTRIM(ModemID),
        COM_Type
    FROM
        Msys_COM AS c LEFT OUTER JOIN MSys_Modems AS m
        ON c.COM_ModemMac = m.ModemCounter
    WHERE
        (
            COM_AlarmTimeStamp IS NULL
            OR COM_AlarmTimeStamp <= CAST(GETDATE() - 1 AS DATE)
            OR COM_AlarmTimeStamp > CAST(GETDATE() + 1 AS DATE)
        )
        AND COM_Type IN (0, 1, 2, 3, 21)
        AND ModemStatus IN (1000, 1004)
    ''')
