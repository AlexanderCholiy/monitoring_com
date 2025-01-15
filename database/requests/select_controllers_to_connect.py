def select_controllers_to_connect() -> str:
    return ('''
    SELECT DISTINCT
        RTRIM(ModemID)
    FROM
        MSys_Modems
    WHERE
        ModemCounter NOT IN (
            SELECT DISTINCT
                COM_ModemMac
            FROM
                MSys_COM
            WHERE
                COM_ModemMac IS NOT NULL
                AND (
                    COM_Type IS NOT NULL
                )
        )
        AND ModemLevel IN (102, 2)
        AND ModemStatus IN (1000, 1004)
        -- Убираем устройства ВДНХ
        AND ModemID NOT LIKE '192.168.%' AND ModemPole != '10978-4-MS2496'
    ''')
