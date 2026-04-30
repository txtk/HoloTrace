from config.settings.AppSettings import AppSettings


class TestSettings(AppSettings):
    debug: bool = True

    class Config:
        env_file = ["./envs/test.env", "./envs/base.env"]
        env_file_encoding = "utf-8"
