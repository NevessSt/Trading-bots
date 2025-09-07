"""Configuration management utilities for trading bot.

This module provides secure configuration handling, environment variable management,
and settings validation for robust trading bot operations.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union, List, Type, get_type_hints
from pathlib import Path
from dataclasses import dataclass, field, fields
from enum import Enum
from datetime import datetime, timedelta
import logging
from cryptography.fernet import Fernet
import base64
import hashlib

class ConfigError(Exception):
    """Configuration-related errors"""
    pass

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None
    sandbox: bool = True
    rate_limit: int = 1200  # requests per minute
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    enabled: bool = True
    
    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise ConfigError(f"API credentials required for exchange {self.name}")

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "trading_bot"
    username: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    @property
    def connection_string(self) -> str:
        """Get database connection string"""
        return (f"postgresql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}")

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 30
    connection_pool_size: int = 10
    
    @property
    def connection_string(self) -> str:
        """Get Redis connection string"""
        auth = f":{self.password}@" if self.password else ""
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.database}"

@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size: float = 0.1  # 10% of portfolio
    max_daily_loss: float = 0.05  # 5% daily loss limit
    max_drawdown: float = 0.15  # 15% maximum drawdown
    stop_loss_percentage: float = 0.02  # 2% stop loss
    take_profit_percentage: float = 0.04  # 4% take profit
    max_open_positions: int = 5
    risk_free_rate: float = 0.02  # 2% annual risk-free rate
    volatility_lookback: int = 30  # days
    correlation_threshold: float = 0.7
    leverage_limit: float = 1.0  # No leverage by default

@dataclass
class TradingConfig:
    """Trading configuration"""
    default_strategy: str = "mean_reversion"
    trading_pairs: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    timeframes: List[str] = field(default_factory=lambda: ["1h", "4h", "1d"])
    min_trade_amount: float = 10.0  # USD
    max_trade_amount: float = 1000.0  # USD
    slippage_tolerance: float = 0.001  # 0.1%
    order_timeout: int = 300  # seconds
    dry_run: bool = True
    enable_shorting: bool = False
    enable_margin: bool = False

@dataclass
class NotificationConfig:
    """Notification configuration"""
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = field(default_factory=list)
    
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    
    notification_levels: List[str] = field(default_factory=lambda: ["ERROR", "CRITICAL"])

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: Optional[str] = None
    jwt_secret: str = ""
    jwt_expiry_hours: int = 24
    api_rate_limit: int = 100  # requests per minute
    max_login_attempts: int = 5
    lockout_duration: int = 300  # seconds
    require_2fa: bool = False
    allowed_ips: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
        if not self.jwt_secret:
            self.jwt_secret = base64.urlsafe_b64encode(os.urandom(32)).decode()

@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_level: str = "INFO"
    log_format: str = "json"
    log_rotation: str = "daily"
    log_retention_days: int = 30
    metrics_enabled: bool = True
    metrics_port: int = 8080
    health_check_port: int = 8081
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    prometheus_enabled: bool = False

@dataclass
class TradingBotConfig:
    """Main trading bot configuration"""
    # Environment and basic settings
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    app_name: str = "TradingBot"
    version: str = "1.0.0"
    
    # Component configurations
    exchanges: Dict[str, ExchangeConfig] = field(default_factory=dict)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # File paths
    data_dir: str = "data"
    logs_dir: str = "logs"
    models_dir: str = "models"
    
    def __post_init__(self):
        # Create directories if they don't exist
        for dir_path in [self.data_dir, self.logs_dir, self.models_dir]:
            Path(dir_path).mkdir(exist_ok=True)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate exchanges
        if not self.exchanges:
            errors.append("At least one exchange must be configured")
        
        for exchange_name, exchange_config in self.exchanges.items():
            if not exchange_config.api_key:
                errors.append(f"API key required for exchange {exchange_name}")
            if not exchange_config.api_secret:
                errors.append(f"API secret required for exchange {exchange_name}")
        
        # Validate trading pairs
        if not self.trading.trading_pairs:
            errors.append("At least one trading pair must be configured")
        
        # Validate risk parameters
        if self.risk.max_position_size <= 0 or self.risk.max_position_size > 1:
            errors.append("Max position size must be between 0 and 1")
        
        if self.risk.max_daily_loss <= 0 or self.risk.max_daily_loss > 1:
            errors.append("Max daily loss must be between 0 and 1")
        
        # Validate database connection
        if not self.database.password and self.environment == Environment.PRODUCTION:
            errors.append("Database password required in production")
        
        return errors
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT

class ConfigManager:
    """Configuration manager with encryption and validation"""
    
    def __init__(self, config_file: Optional[str] = None, 
                 env_file: Optional[str] = None):
        self.config_file = config_file or "config.yaml"
        self.env_file = env_file or ".env"
        self.logger = logging.getLogger(__name__)
        self._config: Optional[TradingBotConfig] = None
        self._encryption_key: Optional[bytes] = None
    
    def load_config(self) -> TradingBotConfig:
        """Load configuration from files and environment variables"""
        # Load environment variables first
        self._load_env_file()
        
        # Load base configuration from file
        config_data = self._load_config_file()
        
        # Override with environment variables
        config_data = self._apply_env_overrides(config_data)
        
        # Create configuration object
        self._config = self._create_config_object(config_data)
        
        # Validate configuration
        errors = self._config.validate()
        if errors:
            raise ConfigError(f"Configuration validation failed: {'; '.join(errors)}")
        
        self.logger.info(f"Configuration loaded successfully for {self._config.environment.value} environment")
        return self._config
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)
        if not env_path.exists():
            self.logger.warning(f"Environment file {self.env_file} not found")
            return
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            self.logger.error(f"Error loading environment file: {e}")
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            self.logger.warning(f"Configuration file {self.config_file} not found, using defaults")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ConfigError(f"Unsupported configuration file format: {config_path.suffix}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration file: {e}")
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        # Environment variable mappings
        env_mappings = {
            # General settings
            'ENVIRONMENT': 'environment',
            'DEBUG': 'debug',
            'APP_NAME': 'app_name',
            
            # Database settings
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.database',
            'DB_USER': 'database.username',
            'DB_PASSWORD': 'database.password',
            
            # Redis settings
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'REDIS_PASSWORD': 'redis.password',
            
            # Security settings
            'JWT_SECRET': 'security.jwt_secret',
            'ENCRYPTION_KEY': 'security.encryption_key',
            
            # Monitoring
            'LOG_LEVEL': 'monitoring.log_level',
            'SENTRY_DSN': 'monitoring.sentry_dsn',
        }
        
        # Apply environment overrides
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_data, config_path, env_value)
        
        # Handle exchange configurations
        self._load_exchange_configs(config_data)
        
        return config_data
    
    def _load_exchange_configs(self, config_data: Dict[str, Any]):
        """Load exchange configurations from environment variables"""
        exchanges = config_data.setdefault('exchanges', {})
        
        # Common exchange names
        exchange_names = ['BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'OKEX']
        
        for exchange in exchange_names:
            api_key = os.getenv(f'{exchange}_API_KEY')
            api_secret = os.getenv(f'{exchange}_API_SECRET')
            api_passphrase = os.getenv(f'{exchange}_API_PASSPHRASE')
            sandbox = os.getenv(f'{exchange}_SANDBOX', 'true').lower() == 'true'
            
            if api_key and api_secret:
                exchange_config = {
                    'name': exchange.lower(),
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'sandbox': sandbox
                }
                
                if api_passphrase:
                    exchange_config['api_passphrase'] = api_passphrase
                
                exchanges[exchange.lower()] = exchange_config
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: str):
        """Set nested dictionary value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value to appropriate type
        final_key = keys[-1]
        current[final_key] = self._convert_env_value(value)
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> TradingBotConfig:
        """Create TradingBotConfig object from dictionary"""
        try:
            # Handle environment enum
            if 'environment' in config_data:
                env_value = config_data['environment']
                if isinstance(env_value, str):
                    config_data['environment'] = Environment(env_value.lower())
            
            # Create exchange configs
            if 'exchanges' in config_data:
                exchanges = {}
                for name, exchange_data in config_data['exchanges'].items():
                    exchanges[name] = ExchangeConfig(**exchange_data)
                config_data['exchanges'] = exchanges
            
            # Create nested config objects
            nested_configs = {
                'database': DatabaseConfig,
                'redis': RedisConfig,
                'risk': RiskConfig,
                'trading': TradingConfig,
                'notifications': NotificationConfig,
                'security': SecurityConfig,
                'monitoring': MonitoringConfig
            }
            
            for key, config_class in nested_configs.items():
                if key in config_data and isinstance(config_data[key], dict):
                    config_data[key] = config_class(**config_data[key])
            
            return TradingBotConfig(**config_data)
            
        except Exception as e:
            raise ConfigError(f"Error creating configuration object: {e}")
    
    def save_config(self, config: TradingBotConfig, encrypt_secrets: bool = True):
        """Save configuration to file"""
        config_data = self._config_to_dict(config, encrypt_secrets)
        
        try:
            with open(self.config_file, 'w') as f:
                if self.config_file.endswith('.json'):
                    json.dump(config_data, f, indent=2, default=str)
                else:
                    yaml.dump(config_data, f, default_flow_style=False)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")
    
    def _config_to_dict(self, config: TradingBotConfig, encrypt_secrets: bool) -> Dict[str, Any]:
        """Convert configuration object to dictionary"""
        # This is a simplified implementation
        # In practice, you'd want to handle nested objects and encryption
        return {
            'environment': config.environment.value,
            'debug': config.debug,
            'app_name': config.app_name,
            # Add other fields as needed
        }
    
    def get_config(self) -> TradingBotConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> TradingBotConfig:
        """Reload configuration from files"""
        self._config = None
        return self.load_config()

# Global configuration manager
config_manager = ConfigManager()

# Convenience functions
def get_config() -> TradingBotConfig:
    """Get current configuration"""
    return config_manager.get_config()

def load_config(config_file: Optional[str] = None, 
                env_file: Optional[str] = None) -> TradingBotConfig:
    """Load configuration with custom files"""
    global config_manager
    config_manager = ConfigManager(config_file, env_file)
    return config_manager.load_config()

def get_exchange_config(exchange_name: str) -> Optional[ExchangeConfig]:
    """Get configuration for specific exchange"""
    config = get_config()
    return config.exchanges.get(exchange_name.lower())

def is_production() -> bool:
    """Check if running in production"""
    return get_config().is_production()

def is_development() -> bool:
    """Check if running in development"""
    return get_config().is_development()