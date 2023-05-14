import os

import dotenv
from pydantic.dataclasses import dataclass

dotenv.load_dotenv()


@dataclass
class Config:
    DB_ECHO: bool = os.environ.get("DB_ECHO", True)
    DB_USER: str = os.environ.get("DB_USER")
    DB_PASSWD: str = os.environ.get("DB_PASSWD")
    DB_HOST: str = os.environ.get("DB_HOST")
    DB_PORT: str = os.environ.get("DB_PORT")
    DB_NAME: str = os.environ.get("DB_NAME")
    DB_URL: str = (
        f"postgresql://{DB_USER}:{DB_PASSWD}" f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    MLFLOW_URI: str = os.environ.get("MLFLOW_URI")
