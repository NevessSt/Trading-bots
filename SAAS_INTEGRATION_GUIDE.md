# SaaS Integration Guide - TradingBot Pro

This guide covers the multi-tenant SaaS capabilities of TradingBot Pro, including billing integration, tenant management, and deployment strategies.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Billing Integration](#billing-integration)
4. [Multi-Tenant System](#multi-tenant-system)
5. [Setup & Configuration](#setup--configuration)
6. [API Documentation](#api-documentation)
7. [Deployment](#deployment)
8. [Monitoring & Analytics](#monitoring--analytics)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

## Overview

TradingBot Pro includes comprehensive SaaS capabilities that enable you to:

- **Multi-Tenant Architecture**: Isolate customers with dedicated resources
- **Stripe Billing Integration**: Handle subscriptions, payments, and invoicing
- **Flexible Pricing Plans**: Support multiple subscription tiers
- **Usage Tracking**: Monitor and limit resource consumption
- **Enterprise Features**: White-labeling, SSO, and custom integrations

### Subscription Plans

| Plan | Monthly Price | Features | Limitations |
|------|---------------|----------|-------------|
| **Starter** | $29.99 | Basic strategies, Web dashboard, Email support | 2 exchanges, 3 strategies, 10K API calls/month |
| **Professional** | $79.99 | Advanced strategies, API access, Priority support | 5 exchanges, 10 strategies, 50K API calls/month |
| **Enterprise** | $249.99 | Full source code, Custom integrations, Dedicated support | Unlimited resources, White-label options |
| **Institutional** | $999.99 | Multi-tenant, Custom development, 24/7 support | All features + custom development |

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Tenant Router │    │  Billing System │
│                 │────│                 │────│                 │
│  (nginx/ALB)    │    │  (Middleware)   │    │   (Stripe API)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  API Gateway    │    │ Master Database │
│                 │    │                 │    │                 │
│  (React/Vue)    │    │   (Flask API)   │    │  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                 ┌─────────────────────────────────┐
                 │        Tenant Isolation         │
                 │                                 │
                 │  ┌─────────┐  ┌─────────┐      │
                 │  │Tenant A │  │Tenant B │ ...  │
                 │  │  DB     │  │  DB     │      │
                 │  │  Redis  │  │  Redis  │      │
                 │  │  Files  │  │  Files  │      │
                 │  └─────────┘  └─────────┘      │
                 └─────────────────────────────────┘
```

### Data Flow

1. **Request Routing**: Load balancer routes requests to application
2. **Tenant Identification**: Middleware identifies tenant from subdomain/domain/header
3. **Authentication**: Verify user belongs to tenant with proper permissions
4. **Resource Isolation**: Route to tenant-specific database and storage
5. **Usage Tracking**: Record API calls, trades, and resource usage
6. **Billing Integration**: Sync usage with Stripe for metered billing

## Billing Integration

### Stripe Setup

1. **Create Stripe Account**
   ```bash
   # Install Stripe CLI for testing
   stripe login
   stripe listen --forward-to localhost:5000/api/billing/webhook
   ```

2. **Configure Products and Prices**
   ```python
   # Create products in Stripe Dashboard or via API
   import stripe
   
   # Create Starter plan
   starter_product = stripe.Product.create(
       name="TradingBot Pro - Starter",
       description="Basic trading bot with essential features"
   )
   
   starter_monthly = stripe.Price.create(
       product=starter_product.id,
       unit_amount=2999,  # $29.99
       currency="usd",
       recurring={"interval": "month"}
   )
   ```

3. **Environment Configuration**
   ```bash
   # Add to .env
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   
   # Add price IDs
   STRIPE_STARTER_MONTHLY_PRICE_ID=price_...
   STRIPE_STARTER_YEARLY_PRICE_ID=price_...
   ```

### Subscription Management

```python
from backend.billing import BillingManager

# Initialize billing manager
billing = BillingManager()

# Create customer and subscription
customer = billing.create_customer(
    user_id="user_123",
    email="customer@example.com",
    name="John Doe",
    company="Acme Corp"
)

subscription = billing.create_subscription(
    customer_id=customer.id,
    plan_type=PlanType.PROFESSIONAL,
    billing_cycle="monthly",
    trial_days=7
)

# Check usage limits
result = billing.check_usage_limits(
    user_id="user_123",
    metric="api_calls_per_month",
    current_usage=5000
)

if not result["allowed"]:
    print(f"Usage limit exceeded: {result['reason']}")
```

### Webhook Handling

```python
# Flask route for Stripe webhooks
@app.route('/api/billing/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    billing_manager = BillingManager()
    result = billing_manager.handle_webhook(
        payload.decode('utf-8'), 
        sig_header
    )
    
    return jsonify(result)
```

## Multi-Tenant System

### Tenant Creation

```python
from backend.tenant_manager import TenantManager

# Initialize tenant manager
tenant_manager = TenantManager()

# Create new tenant
tenant = tenant_manager.create_tenant(
    tenant_id="acme_corp",
    name="Acme Corporation",
    domain="acme.tradingbot.pro",
    plan_type="enterprise",
    custom_config={
        "feature_flags": {
            "white_label": True,
            "custom_branding": True
        },
        "resource_limits": {
            "max_strategies": 50,
            "storage_mb": 5000
        }
    }
)

# Add users to tenant
tenant_manager.add_tenant_user(
    tenant_id="acme_corp",
    user_id="admin_user",
    role="admin",
    permissions=["manage_users", "view_billing", "configure_settings"]
)
```

### Tenant Routing

The system supports multiple routing methods:

1. **Subdomain Routing** (Recommended)
   - `acme.tradingbot.pro` → tenant_id: "acme"
   - `startup.tradingbot.pro` → tenant_id: "startup"

2. **Custom Domain Routing**
   - `trading.acme.com` → tenant_id: "acme_corp"
   - `bot.startup.io` → tenant_id: "startup_inc"

3. **Header-Based Routing**
   - `X-Tenant-ID: acme_corp`

4. **Path-Based Routing**
   - `/tenant/acme_corp/api/strategies`

### Database Isolation

```python
# Use tenant-specific database session
with tenant_manager.get_tenant_db_session("acme_corp") as session:
    # All database operations are isolated to this tenant
    strategies = session.query(Strategy).all()
    
    new_strategy = Strategy(
        name="Custom MACD Strategy",
        config={"fast_period": 12, "slow_period": 26}
    )
    session.add(new_strategy)
    session.commit()
```

## Setup & Configuration

### 1. Database Setup

```bash
# Create master database for tenant management
python -c "from backend.tenant_manager import Base, engine; Base.metadata.create_all(engine)"

# Create billing database
python -c "from backend.billing import Base, engine; Base.metadata.create_all(engine)"
```

### 2. Flask Application Integration

```python
from flask import Flask
from backend.tenant_middleware import TenantMiddleware, create_tenant_routes
from backend.billing import create_billing_routes

app = Flask(__name__)

# Initialize tenant middleware
tenant_middleware = TenantMiddleware(app)

# Add routes
create_tenant_routes(app)
create_billing_routes(app)

# Your existing routes with tenant awareness
@app.route('/api/strategies')
@require_tenant
@require_tenant_user()
def get_strategies():
    # This route is automatically tenant-aware
    with get_tenant_database_session() as session:
        strategies = session.query(Strategy).all()
        return jsonify([s.to_dict() for s in strategies])
```

### 3. Frontend Integration

```javascript
// Tenant-aware API client
class TenantAPIClient {
    constructor(tenantId, apiKey) {
        this.tenantId = tenantId;
        this.apiKey = apiKey;
        this.baseURL = `https://${tenantId}.tradingbot.pro/api`;
    }
    
    async request(endpoint, options = {}) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'X-Tenant-ID': this.tenantId,
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        return response.json();
    }
    
    async getStrategies() {
        return this.request('/strategies');
    }
    
    async createSubscription(planType, billingCycle = 'monthly') {
        return this.request('/billing/subscribe', {
            method: 'POST',
            body: JSON.stringify({
                plan_type: planType,
                billing_cycle: billingCycle
            })
        });
    }
}
```

## API Documentation

### Tenant Management APIs

#### Create Tenant
```http
POST /api/admin/tenants
Content-Type: application/json
Authorization: Bearer admin_token

{
    "tenant_id": "new_company",
    "name": "New Company Inc",
    "domain": "new.tradingbot.pro",
    "plan_type": "professional",
    "custom_config": {
        "feature_flags": {
            "api_access": true
        }
    }
}
```

#### Get Tenant Info
```http
GET /api/tenant/info
X-Tenant-ID: acme_corp
Authorization: Bearer user_token

Response:
{
    "tenant_id": "acme_corp",
    "name": "Acme Corporation",
    "plan_type": "enterprise",
    "feature_flags": {
        "white_label": true,
        "api_access": true
    },
    "resource_limits": {
        "max_strategies": 50,
        "storage_mb": 5000
    }
}
```

### Billing APIs

#### Get Available Plans
```http
GET /api/billing/plans

Response:
{
    "starter": {
        "name": "Starter",
        "price_monthly": 2999,
        "price_yearly": 29999,
        "features": ["Basic strategies", "Web dashboard"],
        "limitations": {
            "max_exchanges": 2,
            "max_strategies": 3
        }
    }
}
```

#### Create Subscription
```http
POST /api/billing/subscribe
Content-Type: application/json

{
    "user_id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "plan_type": "professional",
    "billing_cycle": "monthly",
    "trial_days": 7
}
```

#### Check Usage Limits
```http
GET /api/billing/limits/user_123/api_calls_per_month?current_usage=5000

Response:
{
    "allowed": true,
    "limit": 50000,
    "usage": 5000,
    "remaining": 45000
}
```

## Deployment

### Docker Deployment

```yaml
# docker-compose.saas.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - ENVIRONMENT=production
      - MASTER_DATABASE_URL=postgresql://user:pass@postgres:5432/master
      - TENANT_DATABASE_BASE_URL=postgresql://user:pass@postgres:5432
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    ports:
      - "5000:5000"
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=master
      - POSTGRES_USER=tradingbot
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name *.tradingbot.pro tradingbot.pro;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name *.tradingbot.pro tradingbot.pro;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://app:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradingbot-saas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tradingbot-saas
  template:
    metadata:
      labels:
        app: tradingbot-saas
    spec:
      containers:
      - name: app
        image: tradingbot-pro:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: MASTER_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: master-url
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: stripe-secret
              key: secret-key
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: tradingbot-service
spec:
  selector:
    app: tradingbot-saas
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

## Monitoring & Analytics

### Usage Tracking

```python
# Track various metrics
from backend.tenant_middleware import record_tenant_usage

# In your API endpoints
@app.route('/api/strategies/<strategy_id>/backtest')
@require_tenant
def run_backtest(strategy_id):
    # Record usage
    record_tenant_usage('backtests_run', 1)
    record_tenant_usage('compute_minutes', 5)
    
    # Your backtest logic here
    result = run_strategy_backtest(strategy_id)
    return jsonify(result)
```

### Prometheus Metrics

```python
# Add to your Flask app
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
api_requests = Counter('api_requests_total', 'Total API requests', ['tenant_id', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration', ['tenant_id'])

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'tenant_id'):
        api_requests.labels(tenant_id=g.tenant_id, endpoint=request.endpoint).inc()
        request_duration.labels(tenant_id=g.tenant_id).observe(time.time() - g.start_time)
    return response

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### Dashboard Queries

```sql
-- Top tenants by API usage
SELECT 
    tenant_id,
    SUM(metric_value) as total_api_calls,
    COUNT(*) as request_count
FROM tenant_usage 
WHERE metric_name = 'api_requests' 
    AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id 
ORDER BY total_api_calls DESC;

-- Revenue by plan type
SELECT 
    t.plan_type,
    COUNT(*) as tenant_count,
    SUM(CASE 
        WHEN t.plan_type = 'starter' THEN 29.99
        WHEN t.plan_type = 'professional' THEN 79.99
        WHEN t.plan_type = 'enterprise' THEN 249.99
        WHEN t.plan_type = 'institutional' THEN 999.99
    END) as monthly_revenue
FROM tenants t
WHERE t.status = 'active'
GROUP BY t.plan_type;
```

## Security Considerations

### Data Isolation

1. **Database Isolation**: Each tenant has separate database/schema
2. **File System Isolation**: Tenant-specific storage directories
3. **Redis Isolation**: Different Redis databases per tenant
4. **API Key Isolation**: Tenant-scoped API keys

### Access Control

```python
# Role-based access control
@app.route('/api/admin/tenant-settings')
@require_tenant
@require_tenant_user('admin')
def update_tenant_settings():
    # Only tenant admins can access
    pass

@app.route('/api/strategies')
@require_tenant
@require_tenant_user()
@check_feature_flag('api_access')
def get_strategies():
    # Requires API access feature
    pass
```

### Encryption

```python
# Encrypt sensitive tenant data
from cryptography.fernet import Fernet

class TenantDataEncryption:
    def __init__(self, tenant_id):
        # Generate tenant-specific encryption key
        self.key = self._get_tenant_key(tenant_id)
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### Rate Limiting

```python
# Tenant-specific rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_tenant_id():
    return getattr(g, 'tenant_id', 'anonymous')

limiter = Limiter(
    app,
    key_func=get_tenant_id,
    default_limits=["1000 per hour"]
)

@app.route('/api/expensive-operation')
@limiter.limit("10 per minute")
@require_tenant
def expensive_operation():
    pass
```

## Troubleshooting

### Common Issues

1. **Tenant Not Found**
   ```python
   # Debug tenant identification
   @app.before_request
   def debug_tenant():
       if app.debug:
           print(f"Host: {request.headers.get('Host')}")
           print(f"X-Tenant-ID: {request.headers.get('X-Tenant-ID')}")
           print(f"Path: {request.path}")
   ```

2. **Database Connection Issues**
   ```python
   # Test tenant database connectivity
   def test_tenant_db(tenant_id):
       try:
           with tenant_manager.get_tenant_db_session(tenant_id) as session:
               session.execute('SELECT 1')
           print(f"✓ Tenant {tenant_id} database OK")
       except Exception as e:
           print(f"✗ Tenant {tenant_id} database error: {e}")
   ```

3. **Stripe Webhook Issues**
   ```bash
   # Test webhook locally
   stripe listen --forward-to localhost:5000/api/billing/webhook
   
   # Verify webhook signature
   curl -X POST localhost:5000/api/billing/webhook \
     -H "Stripe-Signature: t=timestamp,v1=signature" \
     -d '{"type": "customer.subscription.created"}'
   ```

### Monitoring Commands

```bash
# Check tenant health
make tenant-health-check

# View tenant usage
make tenant-usage TENANT_ID=acme_corp

# Test billing integration
make test-billing

# Monitor webhook events
make monitor-webhooks
```

### Performance Optimization

1. **Connection Pooling**
   ```python
   # Use connection pooling for tenant databases
   from sqlalchemy.pool import QueuePool
   
   engine = create_engine(
       tenant.database_url,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20
   )
   ```

2. **Caching**
   ```python
   # Cache tenant configurations
   from flask_caching import Cache
   
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   
   @cache.memoize(timeout=300)
   def get_tenant_config(tenant_id):
       return tenant_manager.get_tenant_config(tenant_id)
   ```

3. **Database Optimization**
   ```sql
   -- Add indexes for tenant queries
   CREATE INDEX idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
   CREATE INDEX idx_tenant_users_tenant_id ON tenant_users(tenant_id);
   ```

## Next Steps

1. **Set up Stripe account** and configure webhook endpoints
2. **Deploy master database** for tenant management
3. **Configure DNS** for subdomain routing
4. **Set up monitoring** with Prometheus and Grafana
5. **Implement backup strategy** for tenant data
6. **Create admin dashboard** for tenant management
7. **Add compliance features** (GDPR, SOC2, etc.)
8. **Implement SSO integration** for enterprise customers

For additional support, contact our team at support@tradingbot.pro or refer to the API documentation at https://docs.tradingbot.pro.