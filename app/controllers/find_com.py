import asyncio
import asyncssh
import pandas as pd
import os

from colorama import Style, Fore, init
init(autoreset=True)


class ControllersConnectCOM:
    """Подключение к контроллерам в РЩУ для ручного поиска COM и SRP."""

    def __init__(self, devices_ip: list, connect_timeout: int=30, command_timeout: int=60) -> None:
        """
        - devices_ip - список устройств к которым необходимо подключиться;
        - connect_timeout - время в течение которого мы должны успеть подключиться к контроллеру;
        - command_timeout - время за которое команда должна быть выполнена;
        """
        
        self.devices_ip = devices_ip
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout

    async def controllers_connect_com(self, semaphore: asyncio.Semaphore, connected_counter: asyncio.Lock) -> pd.DataFrame:
        """Подключение к контроллерам в асинхронном режиме с последующей передачей команд для поиска COM и SRP и записей результатов выполнения этих команд."""

        df = pd.DataFrame(columns=['IP', 'Command SRP_0 (Gedel)', 'Command COM_1 (Gedel)', 'Command SRP_0 (Gedel_Old)', 'Command COM_1 (Gedel_Old)', 'Command COM_1 (Allics)', 'Command COM_2 (Allics)'])
        # Список основных команд
        columns = df.columns[1:]

        async def processing_results(device_ip: str, i: int, result: asyncssh.SSHCompletedProcess):
            """Обработка результатов выполнения команд."""

            if isinstance(result, Exception):
                results = 'Command_ERROR: Network connection problem'
            else:
                results = (
                    f'Command_OK: {result.stdout.strip()}' if result.exit_status == 0 and result.stdout
                    else f'Command_ERROR: {result.stderr.strip()}' if result.stderr
                    else f'Command_ERROR: {result.stdout.strip() + result.stderr.strip()}'
                )

             # Если IP уже есть в DataFrame
            if device_ip in df['IP'].values: 
                df.loc[df['IP'] == device_ip, columns[i]] = results
            else:
                # Если IP еще нет в DataFrame, добавляем новую строку с результатами
                row = [None] * len(columns)
                row[i] = results
                # Если ошибка Network connection problem продублируем её на другие команды
                if results == 'Command_ERROR: Network connection problem':
                    row = [results] * len(columns)
                df.loc[len(df)] = [device_ip] + row

        tasks = [self.run_commands_on_device(device_ip, semaphore, connected_counter) for device_ip in self.devices_ip]
        results = await asyncio.gather(*tasks)

        for device_ip, result in zip(self.devices_ip, results):
            for i, output in enumerate(result):
                await processing_results(device_ip, i, output)

        return df

    async def run_commands_on_device(self, device_ip: str, semaphore: asyncio.Semaphore, connected_counter: asyncio.Lock) -> list:
        """
        Запуск команд для контроллера и получение результатов их выполнения.
        - Если SRP Gedel есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 15 03 00 00 00 01 будет содержать 08 (например 0f 03 02 0f 08 d5 b3).
        - Если COM Gedel есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 14 03 00 00 00 01 будет содержать 07 (например 0e 03 02 0e 07 a9 e7).
        - *Если SRP Gedel есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 15 04 01 будет содержать 04 (например 0f 04 01 00 00 20 f1).
        - *Если COM Gedel есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 14 04 01 будет содержать 04 (например 0e 04 02 01 2b ac be).
        - Если COM Олайсис первого уровня есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 02 04 00 0c 00 01 будет содержать 04 (например 02 04 02 00 02 7c f1). У Олайсис SRP нет.
        - Если COM Олайсис второго уровня есть, значит ответ на команду /home/verticali/send /dev/ttyAPP2 03 04 00 0c 00 01 будет содержать 04 (например 02 04 02 00 02 7c f1). У Олайсис SRP нет.

        0f - осначает SRP, а 0e - SOM.
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
                async with asyncssh.connect(device_ip, username='root', known_hosts=None, connect_timeout=self.connect_timeout) as conn:
                    for command in commands:
                        result = await conn.run(command, check=False, timeout=self.command_timeout)
                        results.append(result)
        except (asyncio.exceptions.TimeoutError, asyncssh.Error) as e:
            results.append(e)
        except Exception as e:
            results.append(e)

        # Вывод результата прогресса подключений.
        async with connected_counter:
            connected_counter.value += 1
            print(Fore.BLACK + Style.NORMAL + f'• устройство {connected_counter.value} из {len(self.devices_ip)} (ip: {device_ip});')

        return results


async def controllers_connect_com_main(devices_ip: list, connect_timeout: int=30, command_timeout: int=60, semaphore: int=100, folder_path: str='data'):
    """
    Подключение к контроллерам РЩУ в асинхронном режиме для ручного поиска SRP и COM (для Allics всех уровней COM).

    - devices_ip - список устройств к которым необходимо подключиться;
    - connect_timeout - время в течение которого мы должны успеть подключиться к контроллеру;
    - command_timeout - время за которое команда должна быть выполнена;  
    - semaphore - максимальное количество одновременных операций (не рекомендуется выставлять слишком большое кол-во, т.к. это может привести к ошибкам соединения);
    - folder_path - путь к папке для сохранения результатов команд (имя файла "com.json");
    """

    connected_counter = asyncio.Lock()
    connected_counter.value = 0

    semaphore = asyncio.Semaphore(semaphore)  
    controller = ControllersConnectCOM(devices_ip, connect_timeout, command_timeout)
    df = await controller.controllers_connect_com(semaphore, connected_counter)

    os.makedirs(folder_path, exist_ok=True)

    df.to_json(os.path.join(folder_path, 'com.json'), orient='records')



