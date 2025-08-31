from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
import json
import uuid
from pathlib import Path

from .logging_service import get_logger, LogCategory
from .error_handler import handle_errors, ErrorCategory
from .encryption_service import get_encryption_service, EncryptedData, KeyType, EncryptionLevel


class LicenseType(Enum):
    """Types of licenses available"""
    DEMO = "demo"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    LIFETIME = "lifetime"
    DEVELOPER = "developer"


class LicenseStatus(Enum):
    """License status states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class Permission(Enum):
    """System permissions"""
    # Trading permissions
    TRADE_EXECUTE = "trade_execute"
    TRADE_VIEW = "trade_view"
    TRADE_HISTORY = "trade_history"
    
    # Strategy permissions
    STRATEGY_CREATE = "strategy_create"
    STRATEGY_EDIT = "strategy_edit"
    STRATEGY_DELETE = "strategy_delete"
    STRATEGY_BACKTEST = "strategy_backtest"
    STRATEGY_MARKETPLACE = "strategy_marketplace"
    
    # Bot management
    BOT_START = "bot_start"
    BOT_STOP = "bot_stop"
    BOT_CONFIG = "bot_config"
    BOT_MULTIPLE = "bot_multiple"
    
    # Data access
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_ANALYTICS = "data_analytics"
    
    # API access
    API_ACCESS = "api_access"
    API_RATE_LIMIT_HIGH = "api_rate_limit_high"
    
    # Exchange support
    EXCHANGE_BINANCE = "exchange_binance"
    EXCHANGE_COINBASE = "exchange_coinbase"
    EXCHANGE_KUCOIN = "exchange_kucoin"
    EXCHANGE_BYBIT = "exchange_bybit"
    
    # Admin permissions
    ADMIN_USERS = "admin_users"
    ADMIN_LICENSES = "admin_licenses"
    ADMIN_SYSTEM = "admin_system"
    
    # Support features
    SUPPORT_PRIORITY = "support_priority"
    SUPPORT_PHONE = "support_phone"


@dataclass
class LicenseFeatures:
    """Features available for each license type"""
    max_bots: int = 1
    max_strategies: int = 3
    max_exchanges: int = 1
    api_rate_limit: int = 100  # requests per minute
    support_level: str = "email"
    custom_strategies: bool = False
    advanced_analytics: bool = False
    white_label: bool = False
    permissions: Set[Permission] = field(default_factory=set)


@dataclass
class License:
    """License information"""
    license_key: str
    user_id: str
    license_type: LicenseType
    status: LicenseStatus
    created_at: datetime
    expires_at: Optional[datetime]
    features: LicenseFeatures
    machine_id: Optional[str] = None
    activation_count: int = 0
    max_activations: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_used: Optional[datetime] = None
    usage_stats: Dict[str, Any] = field(default_factory=dict)


class LicenseService:
    """Service for managing licenses and permissions"""
    
    def __init__(self, license_file_path: Optional[str] = None):
        self.logger = get_logger(LogCategory.SECURITY)
        self.encryption_service = get_encryption_service()
        self.license_file = license_file_path or self._get_default_license_file()
        self.licenses: Dict[str, License] = {}
        self.license_templates = self._initialize_license_templates()
        self._load_licenses()
    
    def _get_default_license_file(self) -> str:
        """Get default license file path"""
        return str(Path(__file__).parent.parent / "data" / "licenses.encrypted")
    
    def _initialize_license_templates(self) -> Dict[LicenseType, LicenseFeatures]:
        """Initialize license feature templates"""
        return {
            LicenseType.DEMO: LicenseFeatures(
                max_bots=1,
                max_strategies=2,
                max_exchanges=1,
                api_rate_limit=50,
                support_level="community",
                permissions={
                    Permission.TRADE_VIEW,
                    Permission.TRADE_HISTORY,
                    Permission.STRATEGY_BACKTEST,
                    Permission.BOT_START,
                    Permission.BOT_STOP,
                    Permission.EXCHANGE_BINANCE
                }
            ),
            LicenseType.BASIC: LicenseFeatures(
                max_bots=2,
                max_strategies=5,
                max_exchanges=2,
                api_rate_limit=200,
                support_level="email",
                permissions={
                    Permission.TRADE_EXECUTE,
                    Permission.TRADE_VIEW,
                    Permission.TRADE_HISTORY,
                    Permission.STRATEGY_CREATE,
                    Permission.STRATEGY_EDIT,
                    Permission.STRATEGY_BACKTEST,
                    Permission.BOT_START,
                    Permission.BOT_STOP,
                    Permission.BOT_CONFIG,
                    Permission.DATA_EXPORT,
                    Permission.API_ACCESS,
                    Permission.EXCHANGE_BINANCE,
                    Permission.EXCHANGE_COINBASE
                }
            ),
            LicenseType.PROFESSIONAL: LicenseFeatures(
                max_bots=5,
                max_strategies=20,
                max_exchanges=4,
                api_rate_limit=500,
                support_level="priority",
                custom_strategies=True,
                advanced_analytics=True,
                permissions={
                    Permission.TRADE_EXECUTE,
                    Permission.TRADE_VIEW,
                    Permission.TRADE_HISTORY,
                    Permission.STRATEGY_CREATE,
                    Permission.STRATEGY_EDIT,
                    Permission.STRATEGY_DELETE,
                    Permission.STRATEGY_BACKTEST,
                    Permission.STRATEGY_MARKETPLACE,
                    Permission.BOT_START,
                    Permission.BOT_STOP,
                    Permission.BOT_CONFIG,
                    Permission.BOT_MULTIPLE,
                    Permission.DATA_EXPORT,
                    Permission.DATA_IMPORT,
                    Permission.DATA_ANALYTICS,
                    Permission.API_ACCESS,
                    Permission.API_RATE_LIMIT_HIGH,
                    Permission.EXCHANGE_BINANCE,
                    Permission.EXCHANGE_COINBASE,
                    Permission.EXCHANGE_KUCOIN,
                    Permission.EXCHANGE_BYBIT,
                    Permission.SUPPORT_PRIORITY
                }
            ),
            LicenseType.ENTERPRISE: LicenseFeatures(
                max_bots=-1,  # Unlimited
                max_strategies=-1,  # Unlimited
                max_exchanges=-1,  # Unlimited
                api_rate_limit=2000,
                support_level="phone",
                custom_strategies=True,
                advanced_analytics=True,
                white_label=True,
                permissions=set(Permission)  # All permissions
            ),
            LicenseType.LIFETIME: LicenseFeatures(
                max_bots=10,
                max_strategies=50,
                max_exchanges=4,
                api_rate_limit=1000,
                support_level="priority",
                custom_strategies=True,
                advanced_analytics=True,
                permissions={
                    Permission.TRADE_EXECUTE,
                    Permission.TRADE_VIEW,
                    Permission.TRADE_HISTORY,
                    Permission.STRATEGY_CREATE,
                    Permission.STRATEGY_EDIT,
                    Permission.STRATEGY_DELETE,
                    Permission.STRATEGY_BACKTEST,
                    Permission.STRATEGY_MARKETPLACE,
                    Permission.BOT_START,
                    Permission.BOT_STOP,
                    Permission.BOT_CONFIG,
                    Permission.BOT_MULTIPLE,
                    Permission.DATA_EXPORT,
                    Permission.DATA_IMPORT,
                    Permission.DATA_ANALYTICS,
                    Permission.API_ACCESS,
                    Permission.API_RATE_LIMIT_HIGH,
                    Permission.EXCHANGE_BINANCE,
                    Permission.EXCHANGE_COINBASE,
                    Permission.EXCHANGE_KUCOIN,
                    Permission.EXCHANGE_BYBIT,
                    Permission.SUPPORT_PRIORITY,
                    Permission.SUPPORT_PHONE
                }
            ),
            LicenseType.DEVELOPER: LicenseFeatures(
                max_bots=3,
                max_strategies=10,
                max_exchanges=2,
                api_rate_limit=1000,
                support_level="priority",
                custom_strategies=True,
                permissions={
                    Permission.TRADE_VIEW,
                    Permission.TRADE_HISTORY,
                    Permission.STRATEGY_CREATE,
                    Permission.STRATEGY_EDIT,
                    Permission.STRATEGY_DELETE,
                    Permission.STRATEGY_BACKTEST,
                    Permission.BOT_CONFIG,
                    Permission.DATA_EXPORT,
                    Permission.DATA_IMPORT,
                    Permission.DATA_ANALYTICS,
                    Permission.API_ACCESS,
                    Permission.API_RATE_LIMIT_HIGH,
                    Permission.EXCHANGE_BINANCE,
                    Permission.EXCHANGE_COINBASE
                }
            )
        }
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def generate_license_key(self, 
                           user_id: str,
                           license_type: LicenseType,
                           duration_days: Optional[int] = None,
                           max_activations: int = 1,
                           machine_id: Optional[str] = None) -> License:
        """Generate a new license key"""
        try:
            license_key = f"{license_type.value.upper()}-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:8].upper()}"
            
            expires_at = None
            if duration_days:
                expires_at = datetime.utcnow() + timedelta(days=duration_days)
            
            features = self.license_templates[license_type]
            
            license_obj = License(
                license_key=license_key,
                user_id=user_id,
                license_type=license_type,
                status=LicenseStatus.PENDING,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                features=features,
                machine_id=machine_id,
                max_activations=max_activations,
                metadata={
                    "generated_by": "system",
                    "generation_time": datetime.utcnow().isoformat()
                }
            )
            
            self.licenses[license_key] = license_obj
            self._save_licenses()
            
            self.logger.info(f"Generated license key for user {user_id}", extra={
                "license_key": license_key,
                "license_type": license_type.value,
                "user_id": user_id,
                "expires_at": expires_at.isoformat() if expires_at else None
            })
            
            return license_obj
            
        except Exception as e:
            self.logger.error(f"Failed to generate license key: {e}")
            raise
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def activate_license(self, license_key: str, machine_id: str, user_id: str) -> bool:
        """Activate a license for a specific machine"""
        try:
            if license_key not in self.licenses:
                self.logger.warning(f"License key not found: {license_key}")
                return False
            
            license_obj = self.licenses[license_key]
            
            # Check if license belongs to user
            if license_obj.user_id != user_id:
                self.logger.warning(f"License key does not belong to user: {user_id}")
                return False
            
            # Check license status
            if license_obj.status != LicenseStatus.PENDING and license_obj.status != LicenseStatus.ACTIVE:
                self.logger.warning(f"License is not activatable: {license_obj.status.value}")
                return False
            
            # Check expiration
            if license_obj.expires_at and datetime.utcnow() > license_obj.expires_at:
                license_obj.status = LicenseStatus.EXPIRED
                self._save_licenses()
                self.logger.warning(f"License has expired: {license_key}")
                return False
            
            # Check activation limit
            if license_obj.activation_count >= license_obj.max_activations:
                if license_obj.machine_id != machine_id:
                    self.logger.warning(f"License activation limit reached: {license_key}")
                    return False
            
            # Activate license
            license_obj.status = LicenseStatus.ACTIVE
            license_obj.machine_id = machine_id
            license_obj.activation_count += 1
            license_obj.last_used = datetime.utcnow()
            
            self._save_licenses()
            
            self.logger.info(f"License activated successfully", extra={
                "license_key": license_key,
                "machine_id": machine_id,
                "user_id": user_id,
                "activation_count": license_obj.activation_count
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate license: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def validate_license(self, license_key: str, machine_id: str, user_id: str) -> bool:
        """Validate if a license is active and valid"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            
            # Check ownership
            if license_obj.user_id != user_id:
                return False
            
            # Check status
            if license_obj.status != LicenseStatus.ACTIVE:
                return False
            
            # Check machine binding
            if license_obj.machine_id and license_obj.machine_id != machine_id:
                return False
            
            # Check expiration
            if license_obj.expires_at and datetime.utcnow() > license_obj.expires_at:
                license_obj.status = LicenseStatus.EXPIRED
                self._save_licenses()
                return False
            
            # Update last used
            license_obj.last_used = datetime.utcnow()
            self._save_licenses()
            
            return True
            
        except Exception as e:
            self.logger.error(f"License validation error: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def check_permission(self, license_key: str, permission: Permission) -> bool:
        """Check if a license has a specific permission"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            
            if license_obj.status != LicenseStatus.ACTIVE:
                return False
            
            return permission in license_obj.features.permissions
            
        except Exception as e:
            self.logger.error(f"Permission check error: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def get_license_info(self, license_key: str) -> Optional[License]:
        """Get license information"""
        return self.licenses.get(license_key)
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def revoke_license(self, license_key: str, reason: str = "Manual revocation") -> bool:
        """Revoke a license"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            license_obj.status = LicenseStatus.REVOKED
            license_obj.metadata["revocation_reason"] = reason
            license_obj.metadata["revoked_at"] = datetime.utcnow().isoformat()
            
            self._save_licenses()
            
            self.logger.info(f"License revoked", extra={
                "license_key": license_key,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke license: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def suspend_license(self, license_key: str, reason: str = "Manual suspension") -> bool:
        """Suspend a license temporarily"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            license_obj.status = LicenseStatus.SUSPENDED
            license_obj.metadata["suspension_reason"] = reason
            license_obj.metadata["suspended_at"] = datetime.utcnow().isoformat()
            
            self._save_licenses()
            
            self.logger.info(f"License suspended", extra={
                "license_key": license_key,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to suspend license: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def reactivate_license(self, license_key: str) -> bool:
        """Reactivate a suspended license"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            
            if license_obj.status != LicenseStatus.SUSPENDED:
                return False
            
            # Check expiration
            if license_obj.expires_at and datetime.utcnow() > license_obj.expires_at:
                license_obj.status = LicenseStatus.EXPIRED
            else:
                license_obj.status = LicenseStatus.ACTIVE
            
            license_obj.metadata["reactivated_at"] = datetime.utcnow().isoformat()
            
            self._save_licenses()
            
            self.logger.info(f"License reactivated", extra={
                "license_key": license_key,
                "new_status": license_obj.status.value
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reactivate license: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def extend_license(self, license_key: str, additional_days: int) -> bool:
        """Extend license expiration"""
        try:
            if license_key not in self.licenses:
                return False
            
            license_obj = self.licenses[license_key]
            
            if license_obj.expires_at:
                license_obj.expires_at += timedelta(days=additional_days)
            else:
                license_obj.expires_at = datetime.utcnow() + timedelta(days=additional_days)
            
            # Reactivate if expired
            if license_obj.status == LicenseStatus.EXPIRED:
                license_obj.status = LicenseStatus.ACTIVE
            
            license_obj.metadata["extended_at"] = datetime.utcnow().isoformat()
            license_obj.metadata["extension_days"] = additional_days
            
            self._save_licenses()
            
            self.logger.info(f"License extended", extra={
                "license_key": license_key,
                "additional_days": additional_days,
                "new_expiry": license_obj.expires_at.isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to extend license: {e}")
            return False
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def get_user_licenses(self, user_id: str) -> List[License]:
        """Get all licenses for a user"""
        return [license_obj for license_obj in self.licenses.values() if license_obj.user_id == user_id]
    
    @handle_errors(ErrorCategory.SECURITY_ERROR)
    def cleanup_expired_licenses(self) -> int:
        """Clean up expired licenses"""
        try:
            expired_count = 0
            current_time = datetime.utcnow()
            
            for license_key, license_obj in self.licenses.items():
                if (license_obj.expires_at and 
                    current_time > license_obj.expires_at and 
                    license_obj.status == LicenseStatus.ACTIVE):
                    
                    license_obj.status = LicenseStatus.EXPIRED
                    expired_count += 1
            
            if expired_count > 0:
                self._save_licenses()
                self.logger.info(f"Marked {expired_count} licenses as expired")
            
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired licenses: {e}")
            return 0
    
    def _load_licenses(self):
        """Load licenses from encrypted file"""
        try:
            if Path(self.license_file).exists():
                license_data = self.encryption_service.load_encrypted_config(self.license_file)
                
                for key, data in license_data.items():
                    # Reconstruct License object
                    features_data = data['features']
                    features = LicenseFeatures(
                        max_bots=features_data['max_bots'],
                        max_strategies=features_data['max_strategies'],
                        max_exchanges=features_data['max_exchanges'],
                        api_rate_limit=features_data['api_rate_limit'],
                        support_level=features_data['support_level'],
                        custom_strategies=features_data.get('custom_strategies', False),
                        advanced_analytics=features_data.get('advanced_analytics', False),
                        white_label=features_data.get('white_label', False),
                        permissions={Permission(p) for p in features_data['permissions']}
                    )
                    
                    license_obj = License(
                        license_key=data['license_key'],
                        user_id=data['user_id'],
                        license_type=LicenseType(data['license_type']),
                        status=LicenseStatus(data['status']),
                        created_at=datetime.fromisoformat(data['created_at']),
                        expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
                        features=features,
                        machine_id=data.get('machine_id'),
                        activation_count=data.get('activation_count', 0),
                        max_activations=data.get('max_activations', 1),
                        metadata=data.get('metadata', {}),
                        last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
                        usage_stats=data.get('usage_stats', {})
                    )
                    
                    self.licenses[key] = license_obj
                
                self.logger.info(f"Loaded {len(self.licenses)} licenses from file")
            else:
                self.logger.info("No existing license file found, starting with empty license store")
                
        except Exception as e:
            self.logger.error(f"Failed to load licenses: {e}")
            self.licenses = {}
    
    def _save_licenses(self):
        """Save licenses to encrypted file"""
        try:
            # Ensure directory exists
            Path(self.license_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Convert licenses to serializable format
            license_data = {}
            for key, license_obj in self.licenses.items():
                license_data[key] = {
                    'license_key': license_obj.license_key,
                    'user_id': license_obj.user_id,
                    'license_type': license_obj.license_type.value,
                    'status': license_obj.status.value,
                    'created_at': license_obj.created_at.isoformat(),
                    'expires_at': license_obj.expires_at.isoformat() if license_obj.expires_at else None,
                    'features': {
                        'max_bots': license_obj.features.max_bots,
                        'max_strategies': license_obj.features.max_strategies,
                        'max_exchanges': license_obj.features.max_exchanges,
                        'api_rate_limit': license_obj.features.api_rate_limit,
                        'support_level': license_obj.features.support_level,
                        'custom_strategies': license_obj.features.custom_strategies,
                        'advanced_analytics': license_obj.features.advanced_analytics,
                        'white_label': license_obj.features.white_label,
                        'permissions': [p.value for p in license_obj.features.permissions]
                    },
                    'machine_id': license_obj.machine_id,
                    'activation_count': license_obj.activation_count,
                    'max_activations': license_obj.max_activations,
                    'metadata': license_obj.metadata,
                    'last_used': license_obj.last_used.isoformat() if license_obj.last_used else None,
                    'usage_stats': license_obj.usage_stats
                }
            
            # Save encrypted
            self.encryption_service.save_encrypted_config(license_data, self.license_file)
            self.logger.info(f"Saved {len(self.licenses)} licenses to encrypted file")
            
        except Exception as e:
            self.logger.error(f"Failed to save licenses: {e}")
            raise


# Global license service instance
_license_service = None


def get_license_service(license_file_path: Optional[str] = None) -> LicenseService:
    """Get global license service instance"""
    global _license_service
    if _license_service is None:
        _license_service = LicenseService(license_file_path)
    return _license_service


# Decorator for permission checking
def require_permission(permission: Permission):
    """Decorator to check if user has required permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be integrated with your authentication system
            # For now, it's a placeholder
            license_key = kwargs.get('license_key') or getattr(args[0], 'license_key', None)
            if not license_key:
                raise PermissionError("No license key provided")
            
            license_service = get_license_service()
            if not license_service.check_permission(license_key, permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Async version for async functions
def require_permission_async(permission: Permission):
    """Async decorator to check if user has required permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            license_key = kwargs.get('license_key') or getattr(args[0], 'license_key', None)
            if not license_key:
                raise PermissionError("No license key provided")
            
            license_service = get_license_service()
            if not license_service.check_permission(license_key, permission):
                raise PermissionError(f"Permission denied: {permission.value}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator