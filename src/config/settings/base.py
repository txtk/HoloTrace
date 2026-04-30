from enum import Enum

from pydantic_settings import BaseSettings


class ConfigEnum(Enum):
    prod = "prod"
    dev = "dev"
    test = "test"


class BaseSetting(BaseSettings):
    """
    Base settings class for the application.
    Inherits from BaseSettings to utilize Pydantic's settings management.
    """

    mode: ConfigEnum = ConfigEnum.prod

    class Config:
        env_file = "./envs/.env"
        env_file_encoding = "utf-8"
