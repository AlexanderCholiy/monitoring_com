import os

from dotenv import load_dotenv


CURRENT_DIR: str = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(CURRENT_DIR, '.env')
load_dotenv(env_path)


class SettingsDB:
    """Параметры подключения к БД."""
    DB_HOST: str = os.getenv("DB_HOST")
    DB_USER: str = os.getenv("DB_USER")
    DB_PSWD: str = os.getenv("DB_PSWD")
    DB_NAME: str = os.getenv("DB_NAME")


settings_db = SettingsDB()
