import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import configparser
from cryptography.fernet import Fernet
import base64

@dataclass
class ExchangeConfig:
    """Configuration for exchange connections"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""  # For some exchanges like Coinbase Pro
    sandbox: bool = False
    rate_limit: int = 10  # requests per second
    timeout: int = 30
    retry_attempts: int = 3
    enabled: bool = True

@dataclass
class TradingStrategyConfig:
    """Configuration for trading strategies"""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_management: Dict[str, Any] = field(default_factory=dict)
    timeframes: list = field(default_factory=list)
    symbols: list = field(default_factory=list)
    max_positions: int = 5
    position_size: float = 0.1  # Percentage of portfolio
    stop_loss: float = 0.02  # 2%
    take_profit: float = 0.04  # 4%

@dataclass
class RiskManagementConfig:
    """Risk management configuration"""
    max_daily_loss: float = 0.05  # 5% of portfolio
    max_drawdown: float = 0.15  # 15% maximum drawdown
    position_sizing_method: str = "fixed_percentage"  # fixed_percentage, kelly, volatility_adjusted
    max_correlation: float = 0.7  # Maximum correlation between positions
    emergency_stop_loss: float = 0.10  # 10% emergency stop
    cool_down_period: int = 3600  # seconds after stop loss

@dataclass
class NotificationConfig:
    """Notification system configuration"""
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list = field(default_factory=list)
    
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    
    notification_levels: list = field(default_factory=lambda: ["error", "trade", "warning"])

@dataclass
class DatabaseConfig:
    """Database configuration"""
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "trading_bot"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/trading_bot.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    console_output: bool = True

class ConfigurationManager:
    """Advanced configuration manager with multiple sources and encryption"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._encryption_key = self._get_or_create_encryption_key()
        self._config_cache = {}
        
        # Default configuration
        self.exchanges: Dict[str, ExchangeConfig] = {}
        self.strategies: Dict[str, TradingStrategyConfig] = {}
        self.risk_management = RiskManagementConfig()
        self.notifications = NotificationConfig()
        self.database = DatabaseConfig()
        self.logging_config = LoggingConfig()
        
        # Load configuration from all sources
        self._load_configuration()
    
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get or create encryption key for sensitive data"""
        key_file = self.config_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
        
        return Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive configuration data"""
        return base64.urlsafe_b64encode(
            self._encryption_key.encrypt(data.encode())
        ).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive configuration data"""
        try:
            return self._encryption_key.decrypt(
                base64.urlsafe_b64decode(encrypted_data.encode())
            ).decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            return ""
    
    def _load_configuration(self):
        """Load configuration from multiple sources in priority order"""
        # 1. Load from YAML files
        self._load_yaml_config()
        
        # 2. Load from JSON files
        self._load_json_config()
        
        # 3. Load from INI files
        self._load_ini_config()
        
        # 4. Override with environment variables
        self._load_env_config()
        
        # 5. Validate configuration
        self._validate_configuration()
    
    def _load_yaml_config(self):
        """Load configuration from YAML files"""
        config_files = [
            'main.yaml',
            'exchanges.yaml',
            'strategies.yaml',
            'risk_management.yaml',
            'notifications.yaml'
        ]
        
        for config_file in config_files:
            file_path = self.config_dir / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                        self._merge_config(config_data, source=config_file)
                except Exception as e:
                    self.logger.error(f"Error loading {config_file}: {e}")
    
    def _load_json_config(self):
        """Load configuration from JSON files"""
        json_files = ['config.json', 'local_config.json']
        
        for json_file in json_files:
            file_path = self.config_dir / json_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        config_data = json.load(f)
                        self._merge_config(config_data, source=json_file)
                except Exception as e:
                    self.logger.error(f"Error loading {json_file}: {e}")
    
    def _load_ini_config(self):
        """Load configuration from INI files"""
        ini_file = self.config_dir / 'config.ini'
        if ini_file.exists():
            try:
                config = configparser.ConfigParser()
                config.read(ini_file)
                
                # Convert INI to dict format
                config_data = {}
                for section in config.sections():
                    config_data[section] = dict(config[section])
                
                self._merge_config(config_data, source='config.ini')
            except Exception as e:
                self.logger.error(f"Error loading config.ini: {e}")
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Database
            'DB_TYPE': ('database', 'type'),
            'DB_HOST': ('database', 'host'),
            'DB_PORT': ('database', 'port'),
            'DB_NAME': ('database', 'database'),
            'DB_USER': ('database', 'username'),
            'DB_PASSWORD': ('database', 'password'),
            
            # Logging
            'LOG_LEVEL': ('logging', 'level'),
            'LOG_FILE': ('logging', 'file_path'),
            
            # Risk Management
            'MAX_DAILY_LOSS': ('risk_management', 'max_daily_loss'),
            'MAX_DRAWDOWN': ('risk_management', 'max_drawdown'),
            
            # Notifications
            'EMAIL_ENABLED': ('notifications', 'email_enabled'),
            'EMAIL_SMTP_SERVER': ('notifications', 'email_smtp_server'),
            'EMAIL_USERNAME': ('notifications', 'email_username'),
            'EMAIL_PASSWORD': ('notifications', 'email_password'),
            'TELEGRAM_BOT_TOKEN': ('notifications', 'telegram_bot_token'),
            'TELEGRAM_CHAT_ID': ('notifications', 'telegram_chat_id'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(section, key, self._convert_env_value(value))
    
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
    
    def _merge_config(self, config_data: Dict[str, Any], source: str):
        """Merge configuration data from various sources"""
        self.logger.info(f"Loading configuration from {source}")
        
        for section, data in config_data.items():
            if section == 'exchanges':
                self._load_exchanges_config(data)
            elif section == 'strategies':
                self._load_strategies_config(data)
            elif section == 'risk_management':
                self._update_dataclass(self.risk_management, data)
            elif section == 'notifications':
                self._update_dataclass(self.notifications, data)
            elif section == 'database':
                self._update_dataclass(self.database, data)
            elif section == 'logging':
                self._update_dataclass(self.logging_config, data)
    
    def _load_exchanges_config(self, exchanges_data: Dict[str, Any]):
        """Load exchange configurations"""
        for exchange_name, config in exchanges_data.items():
            # Decrypt sensitive data if encrypted
            if 'api_key' in config and config['api_key'].startswith('enc_'):
                config['api_key'] = self.decrypt_sensitive_data(config['api_key'][4:])
            if 'api_secret' in config and config['api_secret'].startswith('enc_'):
                config['api_secret'] = self.decrypt_sensitive_data(config['api_secret'][4:])
            
            self.exchanges[exchange_name] = ExchangeConfig(name=exchange_name, **config)
    
    def _load_strategies_config(self, strategies_data: Dict[str, Any]):
        """Load strategy configurations"""
        for strategy_name, config in strategies_data.items():
            self.strategies[strategy_name] = TradingStrategyConfig(name=strategy_name, **config)
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """Update dataclass object with new data"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def _set_nested_config(self, section: str, key: str, value: Any):
        """Set nested configuration value"""
        if section == 'database':
            setattr(self.database, key, value)
        elif section == 'logging':
            setattr(self.logging_config, key, value)
        elif section == 'risk_management':
            setattr(self.risk_management, key, value)
        elif section == 'notifications':
            setattr(self.notifications, key, value)
    
    def _validate_configuration(self):
        """Validate configuration for required fields and consistency"""
        # Validate exchanges have required credentials
        for name, exchange in self.exchanges.items():
            if exchange.enabled and not exchange.api_key:
                self.logger.warning(f"Exchange {name} is enabled but missing API key")
        
        # Validate strategies have required parameters
        for name, strategy in self.strategies.items():
            if strategy.enabled and not strategy.symbols:
                self.logger.warning(f"Strategy {name} is enabled but has no symbols configured")
        
        # Validate risk management parameters
        if self.risk_management.max_daily_loss <= 0 or self.risk_management.max_daily_loss > 1:
            self.logger.error("max_daily_loss must be between 0 and 1")
    
    def get_exchange_config(self, exchange_name: str) -> Optional[ExchangeConfig]:
        """Get configuration for specific exchange"""
        return self.exchanges.get(exchange_name)
    
    def get_strategy_config(self, strategy_name: str) -> Optional[TradingStrategyConfig]:
        """Get configuration for specific strategy"""
        return self.strategies.get(strategy_name)
    
    def save_config_template(self):
        """Save configuration templates for easy setup"""
        templates = {
            'exchanges.yaml': {
                'binance': {
                    'api_key': 'your_api_key_here',
                    'api_secret': 'your_api_secret_here',
                    'sandbox': True,
                    'rate_limit': 10,
                    'enabled': True
                },
                'coinbase': {
                    'api_key': 'your_api_key_here',
                    'api_secret': 'your_api_secret_here',
                    'api_passphrase': 'your_passphrase_here',
                    'sandbox': True,
                    'enabled': False
                }
            },
            'strategies.yaml': {
                'moving_average_crossover': {
                    'enabled': True,
                    'parameters': {
                        'fast_period': 10,
                        'slow_period': 20
                    },
                    'symbols': ['BTC/USDT', 'ETH/USDT'],
                    'timeframes': ['1h', '4h'],
                    'position_size': 0.1,
                    'stop_loss': 0.02,
                    'take_profit': 0.04
                }
            },
            'risk_management.yaml': {
                'risk_management': {
                    'max_daily_loss': 0.05,
                    'max_drawdown': 0.15,
                    'position_sizing_method': 'fixed_percentage',
                    'emergency_stop_loss': 0.10
                }
            },
            'notifications.yaml': {
                'notifications': {
                    'email_enabled': False,
                    'telegram_enabled': False,
                    'notification_levels': ['error', 'trade', 'warning']
                }
            }
        }
        
        for filename, content in templates.items():
            template_path = self.config_dir / f"{filename}.template"
            with open(template_path, 'w') as f:
                yaml.dump(content, f, default_flow_style=False, indent=2)
        
        self.logger.info("Configuration templates saved")
    
    def export_config(self, format: str = 'yaml') -> str:
        """Export current configuration to string"""
        config_dict = {
            'exchanges': {name: vars(config) for name, config in self.exchanges.items()},
            'strategies': {name: vars(config) for name, config in self.strategies.items()},
            'risk_management': vars(self.risk_management),
            'notifications': vars(self.notifications),
            'database': vars(self.database),
            'logging': vars(self.logging_config)
        }
        
        if format.lower() == 'yaml':
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        elif format.lower() == 'json':
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError("Format must be 'yaml' or 'json'")

# Global configuration manager instance
config_manager = ConfigurationManager()

if __name__ == "__main__":
    # Example usage and testing
    config = ConfigurationManager()
    
    # Save templates for easy setup
    config.save_config_template()
    
    # Export current configuration
    print("Current configuration:")
    print(config.export_config('yaml'))