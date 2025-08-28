#!/usr/bin/env python3
"""
Multi-Tenant Management System for TradingBot Pro
Handles tenant isolation, configuration, and resource management.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool

# Database setup
Base = declarative_base()
logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    TRIAL = "trial"

class ResourceType(Enum):
    DATABASE = "database"
    REDIS = "redis"
    STORAGE = "storage"
    API_KEYS = "api_keys"
    WEBHOOKS = "webhooks"

@dataclass
class TenantConfig:
    """Configuration for a tenant"""
    tenant_id: str
    name: str
    domain: str
    database_url: str
    redis_url: str
    storage_path: str
    api_rate_limits: Dict[str, int]
    feature_flags: Dict[str, bool]
    custom_settings: Dict[str, Any]
    resource_limits: Dict[str, Any]

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True)
    status = Column(String, nullable=False, default=TenantStatus.ACTIVE.value)
    
    # Configuration
    database_url = Column(String, nullable=False)
    redis_url = Column(String)
    storage_path = Column(String, nullable=False)
    
    # Limits and settings
    api_rate_limits = Column(JSON, default={})
    feature_flags = Column(JSON, default={})
    custom_settings = Column(JSON, default={})
    resource_limits = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Billing integration
    subscription_id = Column(String)
    plan_type = Column(String)

class TenantUser(Base):
    __tablename__ = "tenant_users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, default="user")  # admin, user, viewer
    permissions = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class TenantResource(Base):
    __tablename__ = "tenant_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)
    resource_name = Column(String, nullable=False)
    resource_config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TenantUsage(Base):
    __tablename__ = "tenant_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    period = Column(String)  # hourly, daily, monthly

class TenantManager:
    """Manages multi-tenant operations"""
    
    def __init__(self, master_db_url: str = None):
        self.master_db_url = master_db_url or os.getenv('MASTER_DATABASE_URL', 'sqlite:///master_tenant.db')
        self.master_engine = create_engine(self.master_db_url)
        self.MasterSession = scoped_session(sessionmaker(bind=self.master_engine))
        
        # Create master tables
        Base.metadata.create_all(bind=self.master_engine)
        
        # Cache for tenant configurations
        self._tenant_cache = {}
        self._tenant_engines = {}
        
        logger.info("TenantManager initialized")
    
    def create_tenant(self, tenant_id: str, name: str, domain: str, 
                     plan_type: str = "starter", custom_config: Dict = None) -> Tenant:
        """Create a new tenant with isolated resources"""
        session = self.MasterSession()
        
        try:
            # Check if tenant already exists
            existing = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if existing:
                raise ValueError(f"Tenant {tenant_id} already exists")
            
            # Generate tenant-specific resource URLs
            database_url = self._generate_tenant_database_url(tenant_id)
            redis_url = self._generate_tenant_redis_url(tenant_id)
            storage_path = self._generate_tenant_storage_path(tenant_id)
            
            # Default configuration based on plan
            default_config = self._get_default_tenant_config(plan_type)
            if custom_config:
                default_config.update(custom_config)
            
            # Create tenant record
            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                domain=domain,
                database_url=database_url,
                redis_url=redis_url,
                storage_path=storage_path,
                plan_type=plan_type,
                api_rate_limits=default_config.get('api_rate_limits', {}),
                feature_flags=default_config.get('feature_flags', {}),
                custom_settings=default_config.get('custom_settings', {}),
                resource_limits=default_config.get('resource_limits', {})
            )
            
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
            
            # Initialize tenant resources
            self._initialize_tenant_resources(tenant)
            
            # Cache the tenant
            self._tenant_cache[tenant_id] = tenant
            
            logger.info(f"Created tenant: {tenant_id}")
            return tenant
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create tenant {tenant_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        # Check cache first
        if tenant_id in self._tenant_cache:
            return self._tenant_cache[tenant_id]
        
        session = self.MasterSession()
        try:
            tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if tenant:
                self._tenant_cache[tenant_id] = tenant
                # Update last accessed
                tenant.last_accessed = datetime.utcnow()
                session.commit()
            return tenant
        finally:
            session.close()
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        session = self.MasterSession()
        try:
            tenant = session.query(Tenant).filter(Tenant.domain == domain).first()
            if tenant:
                self._tenant_cache[tenant.tenant_id] = tenant
            return tenant
        finally:
            session.close()
    
    def update_tenant_status(self, tenant_id: str, status: TenantStatus) -> bool:
        """Update tenant status"""
        session = self.MasterSession()
        try:
            tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            tenant.status = status.value
            tenant.updated_at = datetime.utcnow()
            session.commit()
            
            # Update cache
            if tenant_id in self._tenant_cache:
                self._tenant_cache[tenant_id] = tenant
            
            logger.info(f"Updated tenant {tenant_id} status to {status.value}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update tenant status: {e}")
            return False
        finally:
            session.close()
    
    def add_tenant_user(self, tenant_id: str, user_id: str, role: str = "user", 
                       permissions: List[str] = None) -> bool:
        """Add user to tenant"""
        session = self.MasterSession()
        try:
            # Check if user already exists for this tenant
            existing = session.query(TenantUser).filter(
                TenantUser.tenant_id == tenant_id,
                TenantUser.user_id == user_id
            ).first()
            
            if existing:
                # Update existing user
                existing.role = role
                existing.permissions = permissions or []
                existing.is_active = True
            else:
                # Create new tenant user
                tenant_user = TenantUser(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    role=role,
                    permissions=permissions or []
                )
                session.add(tenant_user)
            
            session.commit()
            logger.info(f"Added user {user_id} to tenant {tenant_id} with role {role}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add user to tenant: {e}")
            return False
        finally:
            session.close()
    
    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """Get all users for a tenant"""
        session = self.MasterSession()
        try:
            users = session.query(TenantUser).filter(
                TenantUser.tenant_id == tenant_id,
                TenantUser.is_active == True
            ).all()
            return users
        finally:
            session.close()
    
    def check_user_access(self, tenant_id: str, user_id: str, required_permission: str = None) -> bool:
        """Check if user has access to tenant"""
        session = self.MasterSession()
        try:
            tenant_user = session.query(TenantUser).filter(
                TenantUser.tenant_id == tenant_id,
                TenantUser.user_id == user_id,
                TenantUser.is_active == True
            ).first()
            
            if not tenant_user:
                return False
            
            if required_permission:
                return (required_permission in tenant_user.permissions or 
                       tenant_user.role == "admin")
            
            return True
            
        finally:
            session.close()
    
    @contextmanager
    def get_tenant_db_session(self, tenant_id: str):
        """Get database session for specific tenant"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        if tenant.status != TenantStatus.ACTIVE.value:
            raise ValueError(f"Tenant {tenant_id} is not active")
        
        # Get or create tenant-specific engine
        if tenant_id not in self._tenant_engines:
            self._tenant_engines[tenant_id] = create_engine(
                tenant.database_url,
                poolclass=StaticPool if 'sqlite' in tenant.database_url else None
            )
        
        engine = self._tenant_engines[tenant_id]
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            yield session
        finally:
            session.close()
    
    def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get complete tenant configuration"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        return TenantConfig(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            domain=tenant.domain,
            database_url=tenant.database_url,
            redis_url=tenant.redis_url,
            storage_path=tenant.storage_path,
            api_rate_limits=tenant.api_rate_limits or {},
            feature_flags=tenant.feature_flags or {},
            custom_settings=tenant.custom_settings or {},
            resource_limits=tenant.resource_limits or {}
        )
    
    def update_tenant_config(self, tenant_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update tenant configuration"""
        session = self.MasterSession()
        try:
            tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if not tenant:
                return False
            
            # Update allowed fields
            if 'api_rate_limits' in config_updates:
                tenant.api_rate_limits = config_updates['api_rate_limits']
            if 'feature_flags' in config_updates:
                tenant.feature_flags = config_updates['feature_flags']
            if 'custom_settings' in config_updates:
                tenant.custom_settings = config_updates['custom_settings']
            if 'resource_limits' in config_updates:
                tenant.resource_limits = config_updates['resource_limits']
            
            tenant.updated_at = datetime.utcnow()
            session.commit()
            
            # Clear cache to force reload
            if tenant_id in self._tenant_cache:
                del self._tenant_cache[tenant_id]
            
            logger.info(f"Updated tenant {tenant_id} configuration")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update tenant config: {e}")
            return False
        finally:
            session.close()
    
    def record_tenant_usage(self, tenant_id: str, metric_name: str, value: int, period: str = "hourly"):
        """Record usage metrics for tenant"""
        session = self.MasterSession()
        try:
            usage = TenantUsage(
                tenant_id=tenant_id,
                metric_name=metric_name,
                metric_value=value,
                period=period
            )
            session.add(usage)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to record usage: {e}")
        finally:
            session.close()
    
    def get_tenant_usage(self, tenant_id: str, metric_name: str = None, 
                        period: str = None, limit: int = 100) -> List[TenantUsage]:
        """Get usage metrics for tenant"""
        session = self.MasterSession()
        try:
            query = session.query(TenantUsage).filter(TenantUsage.tenant_id == tenant_id)
            
            if metric_name:
                query = query.filter(TenantUsage.metric_name == metric_name)
            if period:
                query = query.filter(TenantUsage.period == period)
            
            return query.order_by(TenantUsage.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def list_tenants(self, status: TenantStatus = None, limit: int = 100) -> List[Tenant]:
        """List all tenants"""
        session = self.MasterSession()
        try:
            query = session.query(Tenant)
            if status:
                query = query.filter(Tenant.status == status.value)
            
            return query.order_by(Tenant.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def delete_tenant(self, tenant_id: str, force: bool = False) -> bool:
        """Delete tenant and all associated data"""
        if not force:
            # Safety check - require explicit force flag
            logger.warning(f"Attempted to delete tenant {tenant_id} without force flag")
            return False
        
        session = self.MasterSession()
        try:
            # Delete tenant users
            session.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).delete()
            
            # Delete tenant resources
            session.query(TenantResource).filter(TenantResource.tenant_id == tenant_id).delete()
            
            # Delete usage records
            session.query(TenantUsage).filter(TenantUsage.tenant_id == tenant_id).delete()
            
            # Delete tenant
            tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
            if tenant:
                session.delete(tenant)
            
            session.commit()
            
            # Clean up cache and engines
            if tenant_id in self._tenant_cache:
                del self._tenant_cache[tenant_id]
            if tenant_id in self._tenant_engines:
                self._tenant_engines[tenant_id].dispose()
                del self._tenant_engines[tenant_id]
            
            logger.info(f"Deleted tenant: {tenant_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete tenant: {e}")
            return False
        finally:
            session.close()
    
    def _generate_tenant_database_url(self, tenant_id: str) -> str:
        """Generate tenant-specific database URL"""
        base_url = os.getenv('TENANT_DATABASE_BASE_URL', 'sqlite:///data/tenants')
        
        if base_url.startswith('sqlite'):
            return f"sqlite:///data/tenants/{tenant_id}.db"
        elif base_url.startswith('postgresql'):
            return f"{base_url}/tenant_{tenant_id}"
        elif base_url.startswith('mysql'):
            return f"{base_url}/tenant_{tenant_id}"
        else:
            return f"{base_url}_{tenant_id}"
    
    def _generate_tenant_redis_url(self, tenant_id: str) -> str:
        """Generate tenant-specific Redis URL"""
        base_url = os.getenv('TENANT_REDIS_BASE_URL', 'redis://localhost:6379')
        return f"{base_url}/{hash(tenant_id) % 16}"  # Use different Redis DB
    
    def _generate_tenant_storage_path(self, tenant_id: str) -> str:
        """Generate tenant-specific storage path"""
        base_path = os.getenv('TENANT_STORAGE_BASE_PATH', 'data/tenant_storage')
        return os.path.join(base_path, tenant_id)
    
    def _get_default_tenant_config(self, plan_type: str) -> Dict[str, Any]:
        """Get default configuration for tenant based on plan"""
        configs = {
            "starter": {
                "api_rate_limits": {
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000
                },
                "feature_flags": {
                    "advanced_strategies": False,
                    "api_access": False,
                    "custom_indicators": False
                },
                "resource_limits": {
                    "max_strategies": 3,
                    "max_exchanges": 2,
                    "storage_mb": 100
                }
            },
            "professional": {
                "api_rate_limits": {
                    "requests_per_minute": 500,
                    "requests_per_hour": 10000
                },
                "feature_flags": {
                    "advanced_strategies": True,
                    "api_access": True,
                    "custom_indicators": True
                },
                "resource_limits": {
                    "max_strategies": 10,
                    "max_exchanges": 5,
                    "storage_mb": 1000
                }
            },
            "enterprise": {
                "api_rate_limits": {
                    "requests_per_minute": 2000,
                    "requests_per_hour": 50000
                },
                "feature_flags": {
                    "advanced_strategies": True,
                    "api_access": True,
                    "custom_indicators": True,
                    "white_label": True
                },
                "resource_limits": {
                    "max_strategies": -1,  # unlimited
                    "max_exchanges": -1,   # unlimited
                    "storage_mb": 10000
                }
            }
        }
        
        return configs.get(plan_type, configs["starter"])
    
    def _initialize_tenant_resources(self, tenant: Tenant):
        """Initialize resources for new tenant"""
        try:
            # Create storage directory
            os.makedirs(tenant.storage_path, exist_ok=True)
            
            # Initialize tenant database
            if tenant.database_url.startswith('sqlite'):
                # For SQLite, create the directory
                db_dir = os.path.dirname(tenant.database_url.replace('sqlite:///', ''))
                os.makedirs(db_dir, exist_ok=True)
            
            logger.info(f"Initialized resources for tenant: {tenant.tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize tenant resources: {e}")
            raise

# Tenant context middleware
class TenantContext:
    """Thread-local tenant context"""
    
    def __init__(self):
        self._tenant_id = None
        self._tenant_config = None
    
    def set_tenant(self, tenant_id: str, tenant_config: TenantConfig = None):
        self._tenant_id = tenant_id
        self._tenant_config = tenant_config
    
    def get_tenant_id(self) -> Optional[str]:
        return self._tenant_id
    
    def get_tenant_config(self) -> Optional[TenantConfig]:
        return self._tenant_config
    
    def clear(self):
        self._tenant_id = None
        self._tenant_config = None

# Global tenant context
tenant_context = TenantContext()

def get_current_tenant_id() -> Optional[str]:
    """Get current tenant ID from context"""
    return tenant_context.get_tenant_id()

def get_current_tenant_config() -> Optional[TenantConfig]:
    """Get current tenant configuration from context"""
    return tenant_context.get_tenant_config()

if __name__ == '__main__':
    # Test the tenant manager
    manager = TenantManager()
    
    # Create a test tenant
    tenant = manager.create_tenant(
        tenant_id="test_tenant_001",
        name="Test Company",
        domain="test.tradingbot.com",
        plan_type="professional"
    )
    
    print(f"Created tenant: {tenant.tenant_id}")
    print(f"Database URL: {tenant.database_url}")
    print(f"Storage path: {tenant.storage_path}")
    
    # Add a user
    manager.add_tenant_user(tenant.tenant_id, "user123", "admin")
    
    # Test access
    has_access = manager.check_user_access(tenant.tenant_id, "user123")
    print(f"User has access: {has_access}")