def update_com_table_by_somrecords(n_days: int) -> str:
    return (f'''
    INSERT INTO
        Msys_COM (
            COM_Type,
            COM_Cabinet,
            COM_AlarmTimeStamp,
            COM_Pole,
            COM_ModemMac
        )
    SELECT DISTINCT
        NULL,
        NULL,
        NULL,
        ModemPole,
        ModemCounter
    FROM
        MSys_Modems
    WHERE
        ModemCounter IN (
            SELECT DISTINCT
                RecordMac
            FROM
                MSys_SomRecords
            WHERE
                RecordDate > DATEADD(
                    DAY, DATEDIFF(DAY, 0, GETDATE()) - {n_days}, 0
                )
                AND RecordMac IS NOT NULL
        )
        AND ModemLevel IN (102, 2)
    EXCEPT
    SELECT
        NULL,
        NULL,
        NULL,
        COM_Pole,
        COM_ModemMac
    FROM
        Msys_COM
    ''')
