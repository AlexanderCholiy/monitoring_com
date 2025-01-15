import os
import asyncio
import asyncssh

import pandas as pd

from colorama import Fore, Style, init


init(autoreset=True)
CURRENT_DIR: str = os.path.dirname(__file__)


async def controllers_connect_com(
    devices_ip_type_id: list[tuple[str, int]],
    semaphore: asyncio.Semaphore,
    connected_counter: asyncio.Lock,
    connect_timeout: int,
    command_timeout: int
) -> pd.DataFrame:
    df = pd.DataFrame(
        columns=[
            'IP', 'Type',
            'Command COM (Gedel)', 'Command SRP (Gedel)',
            'Command COM (Olaisis)'
        ]
    )

    async def processing_results(
        device_ip: str, device_type_id: int, i: int,
        result: asyncssh.SSHCompletedProcess
    ):
        """Обработка результатов выполнения команд."""
        if isinstance(result, Exception):
            results = 'Command_ERROR: Network connection problem'
        else:
            results = (
                f'Command_OK: {
                    result.stdout.strip()
                }' if result.exit_status == 0
                else f'Command_ERROR: {
                    result.stderr.strip() or result.stdout.strip()
                }'
            )

        if device_ip in df['IP'].values:
            if device_type_id in [0, 1, 2, 3]:
                df.loc[
                    df['IP'] == device_ip,
                    'Command COM (Gedel)' if i == 0 else 'Command SRP (Gedel)'
                ] = results
            elif device_type_id == 21:
                df.loc[
                    df['IP'] == device_ip, 'Command COM (Olaisis)'
                ] = results
        else:
            new_row = [device_ip, device_type_id]
            if device_type_id in [0, 1, 2, 3]:
                new_row += [
                    results, None, None
                ] if i == 0 else [None, results, None]
            elif device_type_id == 21:
                new_row += [None, None, results]
            df.loc[len(df)] = new_row

    total = len(devices_ip_type_id)
    tasks = [
        run_commands_on_device(
            total, device_ip, device_name,
            semaphore, connected_counter, connect_timeout, command_timeout
        ) for device_ip, device_name in devices_ip_type_id
    ]

    results = await asyncio.gather(*tasks)
    for (device_ip, device_type_id), result in zip(
        devices_ip_type_id, results
    ):
        for i, output in enumerate(result):
            await processing_results(device_ip, device_type_id, i, output)
    print()
    return df


async def run_commands_on_device(
    total: int, device_ip: str, devices_type: int,
    semaphore: asyncio.Semaphore,
    connected_counter: asyncio.Lock, connect_timeout: int, command_timeout: int
) -> list:
    commands = {
        0: ['/home/verticali/run-som 1 somaction',
            '/home/verticali/run-som 0 srpaction',
            '/etc/init.d/cron restart'],
        1: ['/home/verticali/run-som 1 somaction',
            '/home/verticali/run-som 0 srpaction',
            '/etc/init.d/cron restart'],
        2: ['/home/verticali/run-som 1 somaction',
            '/home/verticali/run-som 0 srpaction',
            '/etc/init.d/cron restart'],
        3: ['/home/verticali/run-som 1 somaction',
            '/home/verticali/run-som 0 srpaction',
            '/etc/init.d/cron restart'],
        21: ['/home/verticali/run-som 2 somaction',
             '/etc/init.d/cron restart']
    }.get(devices_type, [])

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
                Fore.BLUE + Style.NORMAL + 'Обновление crontab: ' +
                Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
            ),
            end='\r', flush=True
        )

    return results


async def restart_crontab_main(
    devices_ip_type: list[tuple[str, str]],
    connect_timeout: int, command_timeout: int,
    semaphore_value: int = 100
):
    connected_counter = asyncio.Lock()
    connected_counter.value = 0

    semaphore = asyncio.Semaphore(semaphore_value)
    df = await controllers_connect_com(
        devices_ip_type,
        semaphore, connected_counter, connect_timeout, command_timeout
    )

    folder_path = os.path.join(CURRENT_DIR, '..', '..', 'data')
    os.makedirs(folder_path, exist_ok=True)

    df.to_json(os.path.join(folder_path, 'com_records.json'), orient='records')
