from config.settings.AppSettings import AppSettings


class ProductionSettings(AppSettings):
    """
    Production settings class that extends AppSettings.
    This class is used to manage production-specific settings.
    """

    debug: bool = False

    class Config:
        env_file = ["./envs/prod.env", "./envs/base.env"]
        env_file_encoding = "utf-8"
        validate_assignment = True
