# Import configuration for easier access
from config.config import get_config, Config, DevelopmentConfig, TestingConfig, ProductionConfig

__all__ = ['get_config', 'Config', 'DevelopmentConfig', 'TestingConfig', 'ProductionConfig']