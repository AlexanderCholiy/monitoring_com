from datetime import datetime

import pandas as pd


def write_conn_controllers_log(
    json_file_path: str,
    log_file_path: str = '/var/log/mon/find_new_com.log'
) -> None:
    """
    Записываем в общую папку логов результаты выполнения команд (хотя бы одна
    команда должна быть удачной)
    """

    df = pd.read_json(json_file_path)

    df = df[
        df['Command SRP_0 (Gedel)'].str.contains('Command_OK')
        | df['Command COM_1 (Gedel)'].str.contains('Command_OK')
        | df['Command COM_1 (Allics)'].str.contains('Command_OK')
        | df['Command COM_2 (Allics)'].str.contains('Command_OK')
    ]
    df = df.reset_index(drop=True)

    for col in df.columns:
        df[col] = df[col].map(
            lambda x: 'error' if 'Command_ERROR:' in str(x) else x
        )
        df[col] = df[col].map(
            lambda x: (
                x.split('\n')[2].replace('<', '').replace('\r', '').strip()
             ) if 'Command_OK: *** 485 bus gateway PA8 (c)' in str(x) else x
        )

    df.insert(0, 'Timestamp', datetime.now().strftime('%Y-%m-%d %H:%M'))

    df.iloc[:, 2] = df.iloc[:, 2].apply(lambda x: f'SRP_0 (Gedel): {x}')
    df.iloc[:, 3] = df.iloc[:, 3].apply(lambda x: f'COM_1 (Gedel): {x}')
    df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: f'COM_1 (Allics): {x}')
    df.iloc[:, 5] = df.iloc[:, 5].apply(lambda x: f'COM_2 (Allics): {x}')

    with open(log_file_path, 'a') as log_file:
        log_file.write(df.to_string(index=False, header=False))
        log_file.write('\n')
