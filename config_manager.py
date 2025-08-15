#!/usr/bin/env python3
"""
Configuration Manager for TradingBot Pro
Handles configuration loading, validation, and environment-specific settings
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import base64
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "tradingbot"
    username: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    ssl: bool = False
    socket_timeout: int = 5
    connection_pool_max_connections: int = 50

@dataclass
class SecurityConfig:
    secret_key: str = ""
    jwt_secret: str = ""
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    encryption_key: str = ""
    rate_limit_per_minute: int = 60
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]

@dataclass
class TradingConfig:
    max_concurrent_trades: int = 10
    default_risk_percentage: float = 2.0
    max_risk_percentage: float = 10.0
    min_trade_amount: float = 10.0
    max_trade_amount: float = 10000.0
    stop_loss_percentage: float = 5.0
    take_profit_percentage: float = 10.0
    trading_enabled: bool = True
    paper_trading_mode: bool = True
    supported_exchanges: List[str] = None
    
    def __post_init__(self):
        if self.supported_exchanges is None:
            self.supported_exchanges = ["binance", "coinbase", "kraken"]

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    workers: int = 4
    timeout: int = 30
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    rate_limit_enabled: bool = True
    api_version: str = "v1"
    documentation_enabled: bool = True

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/tradingbot.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_enabled: bool = True
    structured_logging: bool = False

@dataclass
class MonitoringConfig:
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    alert_email_enabled: bool = False
    alert_email_recipients: List[str] = None
    prometheus_enabled: bool = False
    grafana_enabled: bool = False
    
    def __post_init__(self):
        if self.alert_email_recipients is None:
            self.alert_email_recipients = []

@dataclass
class BackupConfig:
    enabled: bool = True
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 30
    local_path: str = "backups"
    cloud_enabled: bool = False
    cloud_provider: str = "aws"  # aws, gcp, azure
    cloud_bucket: str = ""
    encryption_enabled: bool = True

@dataclass
class NotificationConfig:
    email_enabled: bool = False
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_use_tls: bool = True
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    discord_enabled: bool = False
    discord_webhook_url: str = ""

@dataclass
class AppConfig:
    environment: str = Environment.DEVELOPMENT.value
    debug: bool = False
    testing: bool = False
    database: DatabaseConfig = None
    redis: RedisConfig = None
    security: SecurityConfig = None
    trading: TradingConfig = None
    api: APIConfig = None
    logging: LoggingConfig = None
    monitoring: MonitoringConfig = None
    backup: BackupConfig = None
    notification: NotificationConfig = None
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.redis is None:
            self.redis = RedisConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.trading is None:
            self.trading = TradingConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.backup is None:
            self.backup = BackupConfig()
        if self.notification is None:
            self.notification = NotificationConfig()

class ConfigManager:
    def __init__(self, config_dir: str = "config", environment: str = None):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv("ENVIRONMENT", Environment.DEVELOPMENT.value)
        self.config: AppConfig = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from files and environment variables"""
        try:
            # Start with default configuration
            config_data = self._get_default_config()
            
            # Load base configuration
            base_config_file = self.config_dir / "config.yaml"
            if base_config_file.exists():
                with open(base_config_file, 'r') as f:
                    base_config = yaml.safe_load(f)
                    config_data = self._deep_merge(config_data, base_config)
            
            # Load environment-specific configuration
            env_config_file = self.config_dir / f"config.{self.environment}.yaml"
            if env_config_file.exists():
                with open(env_config_file, 'r') as f:
                    env_config = yaml.safe_load(f)
                    config_data = self._deep_merge(config_data, env_config)
            
            # Override with environment variables
            config_data = self._apply_env_overrides(config_data)
            
            # Create AppConfig instance
            self.config = self._create_config_object(config_data)
            
            # Validate configuration
            self._validate_config()
            
            # Generate missing secrets
            self._generate_missing_secrets()
            
            self.logger.info(f"Configuration loaded for environment: {self.environment}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        default_config = AppConfig()
        return asdict(default_config)
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config_data: Dict) -> Dict:
        """Apply environment variable overrides"""
        env_mappings = {
            'DATABASE_HOST': ['database', 'host'],
            'DATABASE_PORT': ['database', 'port'],
            'DATABASE_NAME': ['database', 'name'],
            'DATABASE_USERNAME': ['database', 'username'],
            'DATABASE_PASSWORD': ['database', 'password'],
            'REDIS_HOST': ['redis', 'host'],
            'REDIS_PORT': ['redis', 'port'],
            'REDIS_PASSWORD': ['redis', 'password'],
            'SECRET_KEY': ['security', 'secret_key'],
            'JWT_SECRET': ['security', 'jwt_secret'],
            'API_HOST': ['api', 'host'],
            'API_PORT': ['api', 'port'],
            'DEBUG': ['debug'],
            'TRADING_ENABLED': ['trading', 'trading_enabled'],
            'PAPER_TRADING': ['trading', 'paper_trading_mode'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if env_value.lower() in ('true', 'false'):
                    env_value = env_value.lower() == 'true'
                elif env_value.isdigit():
                    env_value = int(env_value)
                elif self._is_float(env_value):
                    env_value = float(env_value)
                
                # Set the value in config_data
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = env_value
        
        return config_data
    
    def _is_float(self, value: str) -> bool:
        """Check if string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _create_config_object(self, config_data: Dict) -> AppConfig:
        """Create AppConfig object from dictionary"""
        # Create nested config objects
        if 'database' in config_data:
            config_data['database'] = DatabaseConfig(**config_data['database'])
        if 'redis' in config_data:
            config_data['redis'] = RedisConfig(**config_data['redis'])
        if 'security' in config_data:
            config_data['security'] = SecurityConfig(**config_data['security'])
        if 'trading' in config_data:
            config_data['trading'] = TradingConfig(**config_data['trading'])
        if 'api' in config_data:
            config_data['api'] = APIConfig(**config_data['api'])
        if 'logging' in config_data:
            config_data['logging'] = LoggingConfig(**config_data['logging'])
        if 'monitoring' in config_data:
            config_data['monitoring'] = MonitoringConfig(**config_data['monitoring'])
        if 'backup' in config_data:
            config_data['backup'] = BackupConfig(**config_data['backup'])
        if 'notification' in config_data:
            config_data['notification'] = NotificationConfig(**config_data['notification'])
        
        return AppConfig(**config_data)
    
    def _validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate database configuration
        if not self.config.database.host:
            errors.append("Database host is required")
        if not self.config.database.name:
            errors.append("Database name is required")
        
        # Validate security configuration
        if not self.config.security.secret_key:
            errors.append("Secret key is required")
        if not self.config.security.jwt_secret:
            errors.append("JWT secret is required")
        
        # Validate trading configuration
        if self.config.trading.max_risk_percentage > 50:
            errors.append("Maximum risk percentage cannot exceed 50%")
        if self.config.trading.min_trade_amount <= 0:
            errors.append("Minimum trade amount must be positive")
        
        # Validate API configuration
        if self.config.api.port < 1 or self.config.api.port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _generate_missing_secrets(self):
        """Generate missing secret keys"""
        if not self.config.security.secret_key:
            self.config.security.secret_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
            self.logger.info("Generated new secret key")
        
        if not self.config.security.jwt_secret:
            self.config.security.jwt_secret = base64.urlsafe_b64encode(os.urandom(32)).decode()
            self.logger.info("Generated new JWT secret")
        
        if not self.config.security.encryption_key:
            self.config.security.encryption_key = Fernet.generate_key().decode()
            self.logger.info("Generated new encryption key")
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        db = self.config.database
        if db.password:
            return f"postgresql://{db.username}:{db.password}@{db.host}:{db.port}/{db.name}"
        else:
            return f"postgresql://{db.username}@{db.host}:{db.port}/{db.name}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        redis = self.config.redis
        if redis.password:
            return f"redis://:{redis.password}@{redis.host}:{redis.port}/{redis.db}"
        else:
            return f"redis://{redis.host}:{redis.port}/{redis.db}"
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION.value
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT.value
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment == Environment.TESTING.value
    
    def save_config(self, filename: str = None):
        """Save current configuration to file"""
        if not filename:
            filename = f"config.{self.environment}.yaml"
        
        config_file = self.config_dir / filename
        config_dict = asdict(self.config)
        
        # Remove sensitive data before saving
        sensitive_keys = ['password', 'secret', 'key', 'token']
        config_dict = self._remove_sensitive_data(config_dict, sensitive_keys)
        
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Configuration saved to {config_file}")
    
    def _remove_sensitive_data(self, data: Any, sensitive_keys: List[str]) -> Any:
        """Remove sensitive data from configuration before saving"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    result[key] = "[REDACTED]"
                else:
                    result[key] = self._remove_sensitive_data(value, sensitive_keys)
            return result
        elif isinstance(data, list):
            return [self._remove_sensitive_data(item, sensitive_keys) for item in data]
        else:
            return data
    
    def create_sample_config(self):
        """Create sample configuration files"""
        # Create base config
        base_config = {
            'environment': 'development',
            'debug': True,
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'tradingbot_dev',
                'username': 'postgres',
                'password': 'your_password_here'
            },
            'security': {
                'secret_key': 'your_secret_key_here',
                'jwt_secret': 'your_jwt_secret_here',
                'jwt_expiration_hours': 24
            },
            'trading': {
                'paper_trading_mode': True,
                'max_concurrent_trades': 5,
                'default_risk_percentage': 2.0
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': True
            }
        }
        
        base_config_file = self.config_dir / "config.yaml"
        with open(base_config_file, 'w') as f:
            yaml.dump(base_config, f, default_flow_style=False, indent=2)
        
        # Create production config template
        prod_config = {
            'environment': 'production',
            'debug': False,
            'database': {
                'host': 'your_production_db_host',
                'name': 'tradingbot_prod',
                'ssl_mode': 'require'
            },
            'security': {
                'rate_limit_per_minute': 30,
                'max_login_attempts': 3
            },
            'trading': {
                'paper_trading_mode': False,
                'trading_enabled': True
            },
            'monitoring': {
                'enabled': True,
                'alert_email_enabled': True,
                'prometheus_enabled': True
            },
            'backup': {
                'enabled': True,
                'cloud_enabled': True,
                'cloud_provider': 'aws',
                'cloud_bucket': 'your-backup-bucket'
            }
        }
        
        prod_config_file = self.config_dir / "config.production.yaml"
        with open(prod_config_file, 'w') as f:
            yaml.dump(prod_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Sample configuration files created in {self.config_dir}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            'environment': self.environment,
            'debug': self.config.debug,
            'database_host': self.config.database.host,
            'database_name': self.config.database.name,
            'api_host': self.config.api.host,
            'api_port': self.config.api.port,
            'trading_enabled': self.config.trading.trading_enabled,
            'paper_trading': self.config.trading.paper_trading_mode,
            'monitoring_enabled': self.config.monitoring.enabled,
            'backup_enabled': self.config.backup.enabled
        }
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration values dynamically"""
        def update_nested(obj, path, value):
            keys = path.split('.')
            current = obj
            for key in keys[:-1]:
                if hasattr(current, key):
                    current = getattr(current, key)
                else:
                    return False
            
            if hasattr(current, keys[-1]):
                setattr(current, keys[-1], value)
                return True
            return False
        
        updated_keys = []
        for key, value in updates.items():
            if update_nested(self.config, key, value):
                updated_keys.append(key)
                self.logger.info(f"Updated config: {key} = {value}")
            else:
                self.logger.warning(f"Failed to update config key: {key}")
        
        return updated_keys

# Global configuration instance
_config_manager = None

def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def init_config(config_dir: str = "config", environment: str = None) -> ConfigManager:
    """Initialize global configuration"""
    global _config_manager
    _config_manager = ConfigManager(config_dir, environment)
    return _config_manager

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Configuration Manager')
    parser.add_argument('action', choices=['create-sample', 'validate', 'summary'])
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--environment', help='Environment name')
    
    args = parser.parse_args()
    
    config_manager = ConfigManager(args.config_dir, args.environment)
    
    if args.action == 'create-sample':
        config_manager.create_sample_config()
        print("Sample configuration files created")
    
    elif args.action == 'validate':
        try:
            config_manager.load_config()
            print("Configuration is valid")
        except Exception as e:
            print(f"Configuration validation failed: {e}")
    
    elif args.action == 'summary':
        summary = config_manager.get_config_summary()
        print(json.dumps(summary, indent=2))