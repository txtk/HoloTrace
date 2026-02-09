from config.settings.DevelopSettings import DevelopSettings
from config.settings.ProductionSettings import ProductionSettings
from config.settings.TestSettings import TestSettings
from config.settings.AppSettings import AppSettings
from config.settings.base import ConfigEnum, BaseSetting

from functools import lru_cache

select_dict:dict[ConfigEnum: AppSettings] = {
    ConfigEnum.prod: ProductionSettings(),
    ConfigEnum.dev: DevelopSettings(),
    ConfigEnum.test: TestSettings(),
}

@lru_cache
def get_settings() -> AppSettings:
    """
    Get the application settings based on the current mode.
    Uses LRU cache to optimize performance.
    """
    mode = BaseSetting().mode
    return select_dict[mode]