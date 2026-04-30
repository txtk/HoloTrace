from config.settings.AppSettings import AppSettings


class DevelopSettings(AppSettings):
    """
    Development settings class that extends AppSettings.
    This class is used to manage development-specific settings.
    """

    debug: bool = True

    class Config:
        env_file = ["./envs/dev.env", "./envs/base.env"]
        env_file_encoding = "utf-8"
