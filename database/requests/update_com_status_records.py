def update_com_status_records() -> str:
    return ('''
    SELECT *
    FROM (
        -- Рассмотрим только SRP
        SELECT DISTINCT
            c.COM_Device,
            c.COM_Type,
            c.COM_Status,
            c.COM_Pole,
            c.COM_AlarmTimeStamp,
            m.ModemStatus,
            m.ModemCounter
        FROM
            Msys_COM AS c LEFT JOIN MSys_Modems AS m
            ON c.COM_ModemMac = m.ModemCounter
        WHERE
            COM_Device = 0
            AND m.ModemLevel IN (102, 2)
    ) AS cm_1
    LEFT JOIN (
        -- Самые актуальые показания для каждого SRP
        SELECT
            SrpVin AS SrpVin,
            SrpVbat AS SrpVbat,
            SrpHeater AS SrpHeater,
            SrpStatus AS SrpStatus,
            VBat AS VBat,
            Out2c AS Out2c,
            Out1c AS Out1c,
            RecordMac AS RecordMac,
            Out1state AS Out1state,
            Out2state AS Out2state,
            Out1overc AS Out1overc,
            Out2overc AS Out2overc,
            Out1disc AS Out1disc,
            Out2disc AS Out2disc
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY RecordMac
                    ORDER BY RecordDate DESC, RecordTime DESC
                ) AS rn_1
            FROM
                MSys_SomRecords AS sr
            WHERE
                SrpStatus IS NOT NULL
                AND RecordDate BETWEEN CAST(
                    DATEADD(DAY, -1000, GETDATE()
                ) AS DATE)
                AND CAST(GETDATE() AS DATE)
        ) AS srp
        WHERE
            rn_1 = 1
    ) AS rd_1
    ON cm_1.ModemCounter = rd_1.RecordMac

    UNION ALL

    SELECT *
    FROM (
        -- Рассмотрим только COM
        SELECT DISTINCT
            c.COM_Device,
            c.COM_Type,
            c.COM_Status,
            c.COM_Pole,
            c.COM_AlarmTimeStamp,
            m.ModemStatus,
            m.ModemCounter
        FROM
            Msys_COM AS c LEFT JOIN MSys_Modems AS m
            ON c.COM_ModemMac = m.ModemCounter
        WHERE
            (COM_Device != 0 OR COM_Device IS NULL)
            AND m.ModemLevel IN (102, 2)
    ) AS cm_2
    LEFT JOIN (
        -- Самые актуальые показания для каждого COM
        SELECT
            SrpVin AS SrpVin,
            SrpVbat AS SrpVbat,
            SrpHeater AS SrpHeater,
            SrpStatus AS SrpStatus,
            VBat AS VBat,
            Out2c AS Out2c,
            Out1c AS Out1c,
            RecordMac AS RecordMac,
            Out1state AS Out1state,
            Out2state AS Out2state,
            Out1overc AS Out1overc,
            Out2overc AS Out2overc,
            Out1disc AS Out1disc,
            Out2disc AS Out2disc
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY RecordMac
                    ORDER BY RecordDate DESC, RecordTime DESC
                ) AS rn_2
            FROM
                MSys_SomRecords AS sr
            WHERE
                SrpStatus IS NULL
                AND RecordDate BETWEEN CAST(
                    DATEADD(DAY, -1000, GETDATE()) AS DATE
                ) AND CAST(GETDATE() AS DATE)
        ) AS som
        WHERE
            rn_2 = 1
    ) AS rd_2
    ON cm_2.ModemCounter = rd_2.RecordMac
    ''')
