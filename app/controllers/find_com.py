import os
import asyncio
import asyncssh

import pandas as pd

from colorama import Style, Fore, init


init(autoreset=True)
CURRENT_DIR: str = os.path.dirname(__file__)


async def controllers_connect_com(
    devices_ip: list[str],
    semaphore: asyncio.Semaphore, connected_counter: asyncio.Lock,
    connect_timeout, command_timeout
) -> pd.DataFrame:
    df = pd.DataFrame(
        columns=[
            'IP', 'Command SRP_0 (Gedel)', 'Command COM_1 (Gedel)',
            'Command SRP_0 (Gedel_Old)', 'Command COM_1 (Gedel_Old)',
            'Command COM_1 (Allics)', 'Command COM_2 (Allics)'
        ]
    )

    columns = df.columns[1:]

    async def processing_results(
        device_ip: str, i: int, result: asyncssh.SSHCompletedProcess
    ):
        """Обработка результатов выполнения команд."""

        if isinstance(result, Exception):
            results = 'Command_ERROR: Network connection problem'
        else:
            results = (
                f'Command_OK: {result.stdout.strip()}' if (
                    result.exit_status == 0 and result.stdout
                )
                else f'Command_ERROR: {result.stderr.strip()}' if result.stderr
                else f'Command_ERROR: {
                    result.stdout.strip() + result.stderr.strip()
                }'
            )

        if device_ip in df['IP'].values:
            df.loc[df['IP'] == device_ip, columns[i]] = results
        else:
            row = [None] * len(columns)
            row[i] = results
            if results == 'Command_ERROR: Network connection problem':
                row = [results] * len(columns)
            df.loc[len(df)] = [device_ip] + row

    total = len(devices_ip)
    tasks = [
        run_commands_on_device(
            total, device_ip,
            semaphore, connected_counter, connect_timeout, command_timeout
        ) for device_ip in devices_ip
    ]
    results = await asyncio.gather(*tasks)

    for device_ip, result in zip(devices_ip, results):
        for i, output in enumerate(result):
            await processing_results(device_ip, i, output)
    print()
    return df


async def run_commands_on_device(
    total, device_ip: str,
    semaphore: asyncio.Semaphore, connected_counter: asyncio.Lock,
    connect_timeout, command_timeout
) -> list[str]:
    """
    Commands:
    --------
    - SRP Gedel ответ на команду:
        /home/verticali/send /dev/ttyAPP2 15 03 00 00 00 01
        будет содержать 08 (например 0f 03 02 0f 08 d5 b3).
    - COM Gedel ответ на команду:
        /home/verticali/send /dev/ttyAPP2 14 03 00 00 00 01
        будет содержать 07 (например 0e 03 02 0e 07 a9 e7).
    - COM Allics первого уровня ответ на команду:
        /home/verticali/send /dev/ttyAPP2 02 04 00 0c 00 01
        будет содержать 04 (например 02 04 02 00 02 7c f1).
    - COM Allics второго уровня ответ на команду:
        /home/verticali/send /dev/ttyAPP2 03 04 00 0c 00 01
        будет содержать 04 (например 02 04 02 00 02 7c f1).
    - Old COM Gedel ответ на команду:
        /home/verticali/send /dev/ttyAPP2 14 04 01
        будет содержать 04 (например 0e 04 02 01 2b ac be).
    - Old SRP Gedel ответ на команду:
        /home/verticali/send /dev/ttyAPP2 15 04 01
        будет содержать 04 (например 0f 04 01 00 00 20 f1).
    """
    commands = [
        '/home/verticali/send /dev/ttyAPP2 15 03 00 00 00 01',
        '/home/verticali/send /dev/ttyAPP2 14 03 00 00 00 01',
        '/home/verticali/send /dev/ttyAPP2 15 04 01',
        '/home/verticali/send /dev/ttyAPP2 14 04 01',
        '/home/verticali/send /dev/ttyAPP2 02 04 00 0c 00 01',
        '/home/verticali/send /dev/ttyAPP2 03 04 00 0c 00 01',
    ]

    results = []

    try:
        async with semaphore:
            async with asyncssh.connect(
                device_ip, username='root',
                known_hosts=None, connect_timeout=connect_timeout
            ) as conn:
                for command in commands:
                    result = await conn.run(
                        command, check=False, timeout=command_timeout
                    )
                    results.append(result)
    except (asyncio.exceptions.TimeoutError, asyncssh.Error) as e:
        results.append(e)
    except Exception as e:
        results.append(e)

    async with connected_counter:
        connected_counter.value += 1
        percent_complete = round((connected_counter.value / total) * 100, 2)
        print(
            (
                Fore.BLUE + Style.NORMAL + 'Поиск новых COM: ' +
                Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
            ),
            end='\r', flush=True
        )

    return results


async def controllers_connect_com_main(
    devices_ip: list[str],
    connect_timeout: int, command_timeout: int,
    semaphore: int = 100
):
    connected_counter = asyncio.Lock()
    connected_counter.value = 0

    semaphore = asyncio.Semaphore(semaphore)
    df = await controllers_connect_com(
        devices_ip, semaphore, connected_counter,
        connect_timeout, command_timeout
    )

    folder_path = os.path.join(CURRENT_DIR, '..', '..', 'data')
    os.makedirs(folder_path, exist_ok=True)

    df.to_json(os.path.join(folder_path, 'find_com.json'), orient='records')
