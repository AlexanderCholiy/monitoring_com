import time
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from colorama import Fore, Style, init

from app.common.log_results import logger


init(autoreset=True)
print_lock = threading.Lock()


def execute_command_with_timeout(command: str, timeout: int):
    process = subprocess.Popen(
        command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    start_time = time.time()

    while True:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            return stdout, stderr, process.returncode

        if time.time() - start_time > timeout:
            process.kill()
            return None, None, None

        time.sleep(0.1)


def send_com_update(
    ip: str, firmware_folder_path: str, timeout: int, index: int, total: int,
    progress_callback
):
    command = f'cd {firmware_folder_path} && ./send_to_factory.sh {ip}'
    stdout, stderr, returncode = execute_command_with_timeout(command, timeout)
    if returncode is None:
        with print_lock:
            print(
                Fore.YELLOW + Style.DIM + 'Контроллер ' +
                Fore.WHITE + Style.BRIGHT + ip + Style.RESET_ALL +
                Fore.YELLOW + Style.DIM +
                ' - выполнение команды:\n' +
                Fore.WHITE + Style.BRIGHT + command + Style.RESET_ALL +
                Fore.YELLOW + Style.DIM +
                '\nпревысило таймаут ' +
                Fore.WHITE + Style.BRIGHT + str(timeout) + Style.RESET_ALL +
                Fore.YELLOW + Style.DIM + ' секунд.'
            )
            logger.error(
                f'Выполнение команды {command} превысило время ожидания ' +
                f'{timeout} секунд.'
            )
    elif returncode == 0:
        progress_callback()
    else:
        with print_lock:
            print(
                Fore.RED + Style.DIM + 'Контроллер ' +
                Fore.WHITE + Style.BRIGHT + ip + Style.RESET_ALL +
                Fore.RED + Style.DIM +
                ' - при выполнении команды:\n' +
                Fore.WHITE + Style.BRIGHT + command + Style.RESET_ALL +
                Fore.RED + Style.DIM +
                '\nвозникла ошибка:\n' +
                Fore.WHITE + Style.BRIGHT + str(stderr)
            )
            logger.error(
                f'При выполнии команды {command} возникла ошибка:\n' +
                str(stderr)
            )


def update_com(
    controllers_ip: list[str], firmware_folder_path: str, timeout: int
):
    total: int = len(controllers_ip)
    completed_count = 0

    def progress_callback():
        nonlocal completed_count
        completed_count += 1
        percent_complete = round((completed_count / total) * 100, 2)
        with print_lock:
            print(
                (
                    Fore.BLUE + Style.NORMAL + 'Обновление прошивки: ' +
                    f'{firmware_folder_path} ' +
                    Fore.WHITE + Style.BRIGHT + str(percent_complete) + '%'
                ),
                end='\r', flush=True
            )

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                send_com_update,
                ip, firmware_folder_path, timeout, index, total,
                progress_callback
            )
            for index, ip in enumerate(controllers_ip)
        ]

        for future in as_completed(futures):
            pass

    if total != 0:
        print()
