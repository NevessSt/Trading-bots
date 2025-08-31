# ☁️ Azure Deployment Guide

This guide provides comprehensive instructions for deploying the Trading Bot application on Microsoft Azure using various Azure services.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Container Instances Deployment](#container-instances-deployment)
- [App Service Deployment](#app-service-deployment)
- [AKS Deployment](#aks-deployment)
- [Database Setup](#database-setup)
- [Load Balancer & Traffic Manager](#load-balancer--traffic-manager)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Auto Scaling](#auto-scaling)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Azure Account Setup
- Azure subscription with billing enabled
- Azure CLI installed and configured
- Service Principal with appropriate permissions
- Domain name (optional, for custom domain)

### Required Azure Services
- **Container Instances/App Service/AKS**: Application hosting
- **Azure Database for PostgreSQL**: Database service
- **Azure Cache for Redis**: Caching service
- **Application Gateway**: Load balancing and SSL termination
- **Azure DNS**: DNS management
- **Key Vault**: SSL certificates and secrets
- **Monitor**: Monitoring and logging
- **Storage Account**: File storage and backups

### Local Setup
```bash
# Install Azure CLI (Linux/macOS)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure CLI (Windows)
# Download from: https://aka.ms/installazurecliwindows

# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"

# Install kubectl for AKS
az aks install-cli
```

## 🐳 Container Instances Deployment (Quickest)

### 1. Create Resource Group

```bash
# Create resource group
az group create --name trading-bot-rg --location eastus

# Create container registry
az acr create --resource-group trading-bot-rg --name tradingbotacr --sku Basic --admin-enabled true
```

### 2. Build and Push Images

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name tradingbotacr --resource-group trading-bot-rg --query loginServer --output tsv)

# Login to ACR
az acr login --name tradingbotacr

# Build and push backend
docker build -t $ACR_LOGIN_SERVER/trading-bot-backend:latest ./backend
docker push $ACR_LOGIN_SERVER/trading-bot-backend:latest

# Build and push frontend
docker build -t $ACR_LOGIN_SERVER/trading-bot-frontend:latest ./frontend
docker push $ACR_LOGIN_SERVER/trading-bot-frontend:latest
```

### 3. Deploy Container Instances

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name tradingbotacr --resource-group trading-bot-rg --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name tradingbotacr --resource-group trading-bot-rg --query passwords[0].value --output tsv)

# Deploy backend container
az container create \
  --resource-group trading-bot-rg \
  --name trading-bot-backend \
  --image $ACR_LOGIN_SERVER/trading-bot-backend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label trading-bot-backend-$(date +%s) \
  --ports 5000 \
  --environment-variables \
    FLASK_ENV=production \
    DATABASE_URL="postgresql://username:password@postgres-server.postgres.database.azure.com:5432/trading_bot" \
    REDIS_URL="redis://redis-cache.redis.cache.windows.net:6380/0?ssl=true&password=your-redis-key"

# Deploy frontend container
az container create \
  --resource-group trading-bot-rg \
  --name trading-bot-frontend \
  --image $ACR_LOGIN_SERVER/trading-bot-frontend:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label trading-bot-frontend-$(date +%s) \
  --ports 3000 \
  --environment-variables \
    REACT_APP_API_URL="https://trading-bot-backend-123456.eastus.azurecontainer.io:5000" \
    REACT_APP_WS_URL="wss://trading-bot-backend-123456.eastus.azurecontainer.io:5000"
```

## 🌐 App Service Deployment (Recommended)

### 1. Create App Service Plan

```bash
# Create App Service Plan
az appservice plan create \
  --name trading-bot-plan \
  --resource-group trading-bot-rg \
  --sku P1V2 \
  --is-linux

# Create backend web app
az webapp create \
  --resource-group trading-bot-rg \
  --plan trading-bot-plan \
  --name trading-bot-backend-app \
  --deployment-container-image-name $ACR_LOGIN_SERVER/trading-bot-backend:latest

# Create frontend web app
az webapp create \
  --resource-group trading-bot-rg \
  --plan trading-bot-plan \
  --name trading-bot-frontend-app \
  --deployment-container-image-name $ACR_LOGIN_SERVER/trading-bot-frontend:latest
```

### 2. Configure App Settings

```bash
# Configure backend app settings
az webapp config appsettings set \
  --resource-group trading-bot-rg \
  --name trading-bot-backend-app \
  --settings \
    FLASK_ENV=production \
    DATABASE_URL="postgresql://username:password@postgres-server.postgres.database.azure.com:5432/trading_bot" \
    REDIS_URL="redis://redis-cache.redis.cache.windows.net:6380/0?ssl=true&password=your-redis-key" \
    SECRET_KEY="your-secret-key" \
    JWT_SECRET_KEY="your-jwt-secret"

# Configure frontend app settings
az webapp config appsettings set \
  --resource-group trading-bot-rg \
  --name trading-bot-frontend-app \
  --settings \
    REACT_APP_API_URL="https://trading-bot-backend-app.azurewebsites.net" \
    REACT_APP_WS_URL="wss://trading-bot-backend-app.azurewebsites.net"
```

### 3. Configure Container Registry

```bash
# Configure ACR for backend
az webapp config container set \
  --name trading-bot-backend-app \
  --resource-group trading-bot-rg \
  --docker-custom-image-name $ACR_LOGIN_SERVER/trading-bot-backend:latest \
  --docker-registry-server-url https://$ACR_LOGIN_SERVER \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configure ACR for frontend
az webapp config container set \
  --name trading-bot-frontend-app \
  --resource-group trading-bot-rg \
  --docker-custom-image-name $ACR_LOGIN_SERVER/trading-bot-frontend:latest \
  --docker-registry-server-url https://$ACR_LOGIN_SERVER \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD
```

## ☸️ AKS Deployment (Enterprise)

### 1. Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group trading-bot-rg \
  --name trading-bot-aks \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --attach-acr tradingbotacr

# Get AKS credentials
az aks get-credentials --resource-group trading-bot-rg --name trading-bot-aks
```

### 2. Create Kubernetes Manifests

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trading-bot
```

Create `k8s/backend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: trading-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: tradingbotacr.azurecr.io/trading-bot-backend:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: trading-bot
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP
```

Create `k8s/frontend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: trading-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: tradingbotacr.azurecr.io/trading-bot-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://your-domain.com/api"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: trading-bot
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
```

Create `k8s/ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: trading-bot-ingress
  namespace: trading-bot
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: tls-secret
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### 3. Deploy to AKS

```bash
# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgresql://username:password@postgres-server.postgres.database.azure.com:5432/trading_bot" \
  --from-literal=redis-url="redis://redis-cache.redis.cache.windows.net:6380/0?ssl=true&password=your-redis-key" \
  --namespace=trading-bot

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n trading-bot
kubectl get services -n trading-bot
kubectl get ingress -n trading-bot
```

## 🗄️ Database Setup

### 1. Create Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group trading-bot-rg \
  --name trading-bot-postgres \
  --location eastus \
  --admin-user postgres \
  --admin-password "YourSecurePassword123!" \
  --sku-name GP_Gen5_2 \
  --version 13 \
  --storage-size 51200 \
  --backup-retention 7 \
  --geo-redundant-backup Enabled \
  --ssl-enforcement Enabled

# Create database
az postgres db create \
  --resource-group trading-bot-rg \
  --server-name trading-bot-postgres \
  --name trading_bot

# Configure firewall rules
az postgres server firewall-rule create \
  --resource-group trading-bot-rg \
  --server trading-bot-postgres \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 2. Create Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --resource-group trading-bot-rg \
  --name trading-bot-redis \
  --location eastus \
  --sku Standard \
  --vm-size c1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2

# Get Redis connection string
az redis show-access-keys \
  --resource-group trading-bot-rg \
  --name trading-bot-redis
```

## ⚖️ Load Balancer & Traffic Manager

### 1. Create Application Gateway

```bash
# Create public IP
az network public-ip create \
  --resource-group trading-bot-rg \
  --name trading-bot-pip \
  --allocation-method Static \
  --sku Standard

# Create virtual network
az network vnet create \
  --resource-group trading-bot-rg \
  --name trading-bot-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name appgw-subnet \
  --subnet-prefix 10.0.1.0/24

# Create Application Gateway
az network application-gateway create \
  --name trading-bot-appgw \
  --location eastus \
  --resource-group trading-bot-rg \
  --vnet-name trading-bot-vnet \
  --subnet appgw-subnet \
  --capacity 2 \
  --sku Standard_v2 \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http \
  --public-ip-address trading-bot-pip
```

### 2. Configure Backend Pools

```bash
# Add backend pool for frontend
az network application-gateway address-pool create \
  --gateway-name trading-bot-appgw \
  --resource-group trading-bot-rg \
  --name frontend-pool \
  --servers trading-bot-frontend-app.azurewebsites.net

# Add backend pool for backend API
az network application-gateway address-pool create \
  --gateway-name trading-bot-appgw \
  --resource-group trading-bot-rg \
  --name backend-pool \
  --servers trading-bot-backend-app.azurewebsites.net
```

## 🔒 SSL Certificate Setup

### 1. Create Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name trading-bot-kv \
  --resource-group trading-bot-rg \
  --location eastus \
  --enabled-for-template-deployment true

# Import SSL certificate
az keyvault certificate import \
  --vault-name trading-bot-kv \
  --name ssl-cert \
  --file certificate.pfx \
  --password "certificate-password"
```

### 2. Configure Application Gateway SSL

```bash
# Add HTTPS listener
az network application-gateway frontend-port create \
  --gateway-name trading-bot-appgw \
  --resource-group trading-bot-rg \
  --name httpsPort \
  --port 443

# Add SSL certificate to Application Gateway
az network application-gateway ssl-cert create \
  --gateway-name trading-bot-appgw \
  --resource-group trading-bot-rg \
  --name ssl-cert \
  --key-vault-secret-id "https://trading-bot-kv.vault.azure.net/secrets/ssl-cert"
```

## 📊 Monitoring & Logging

### 1. Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app trading-bot-insights \
  --location eastus \
  --resource-group trading-bot-rg \
  --application-type web

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app trading-bot-insights \
  --resource-group trading-bot-rg \
  --query instrumentationKey \
  --output tsv)

# Configure App Service to use Application Insights
az webapp config appsettings set \
  --resource-group trading-bot-rg \
  --name trading-bot-backend-app \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### 2. Create Log Analytics Workspace

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group trading-bot-rg \
  --workspace-name trading-bot-logs \
  --location eastus

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group trading-bot-rg \
  --workspace-name trading-bot-logs \
  --query customerId \
  --output tsv)
```

### 3. Configure Alerts

```bash
# Create action group
az monitor action-group create \
  --resource-group trading-bot-rg \
  --name trading-bot-alerts \
  --short-name tb-alerts \
  --email-receivers name=admin email=admin@yourdomain.com

# Create metric alert
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group trading-bot-rg \
  --scopes "/subscriptions/your-subscription-id/resourceGroups/trading-bot-rg/providers/Microsoft.Web/sites/trading-bot-backend-app" \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU usage is high" \
  --evaluation-frequency 5m \
  --window-size 15m \
  --action trading-bot-alerts
```

## 🔄 Auto Scaling

### 1. App Service Auto Scaling

```bash
# Create autoscale setting
az monitor autoscale create \
  --resource-group trading-bot-rg \
  --resource "/subscriptions/your-subscription-id/resourceGroups/trading-bot-rg/providers/Microsoft.Web/serverfarms/trading-bot-plan" \
  --name trading-bot-autoscale \
  --min-count 2 \
  --max-count 10 \
  --count 2

# Add scale-out rule
az monitor autoscale rule create \
  --resource-group trading-bot-rg \
  --autoscale-name trading-bot-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1

# Add scale-in rule
az monitor autoscale rule create \
  --resource-group trading-bot-rg \
  --autoscale-name trading-bot-autoscale \
  --condition "Percentage CPU < 30 avg 5m" \
  --scale in 1
```

### 2. AKS Auto Scaling

```bash
# Enable cluster autoscaler
az aks update \
  --resource-group trading-bot-rg \
  --name trading-bot-aks \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10

# Create HPA for backend deployment
kubectl autoscale deployment backend-deployment \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  --namespace=trading-bot
```

## 💰 Cost Optimization

### 1. Reserved Instances

```bash
# Purchase App Service Reserved Instance
az reservations reservation-order purchase \
  --reservation-order-id "your-order-id" \
  --sku "Standard_P1V2" \
  --location "East US" \
  --quantity 1 \
  --term P1Y
```

### 2. Cost Analysis

```bash
# Get cost analysis
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --resource-group trading-bot-rg

# Create budget
az consumption budget create \
  --budget-name trading-bot-budget \
  --amount 500 \
  --time-grain Monthly \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --resource-group trading-bot-rg
```

### 3. Optimization Recommendations

```bash
# Get advisor recommendations
az advisor recommendation list \
  --resource-group trading-bot-rg \
  --category Cost
```

## 🔧 Troubleshooting

### Common Issues

#### 1. App Service Deployment Issues
```bash
# Check deployment logs
az webapp log tail --name trading-bot-backend-app --resource-group trading-bot-rg

# Check app service logs
az webapp log download --name trading-bot-backend-app --resource-group trading-bot-rg

# Restart app service
az webapp restart --name trading-bot-backend-app --resource-group trading-bot-rg
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
az postgres server show --name trading-bot-postgres --resource-group trading-bot-rg

# Check firewall rules
az postgres server firewall-rule list --server-name trading-bot-postgres --resource-group trading-bot-rg

# Update connection string
az webapp config connection-string set \
  --resource-group trading-bot-rg \
  --name trading-bot-backend-app \
  --settings DefaultConnection="postgresql://username:password@server.postgres.database.azure.com:5432/database" \
  --connection-string-type PostgreSQL
```

#### 3. AKS Issues
```bash
# Check cluster status
az aks show --resource-group trading-bot-rg --name trading-bot-aks

# Get cluster credentials
az aks get-credentials --resource-group trading-bot-rg --name trading-bot-aks --overwrite-existing

# Check pod logs
kubectl logs -f deployment/backend-deployment -n trading-bot

# Describe problematic pods
kubectl describe pod <pod-name> -n trading-bot
```

### Performance Optimization

#### 1. Database Performance
```bash
# Enable Query Performance Insight
az postgres server configuration set \
  --resource-group trading-bot-rg \
  --server-name trading-bot-postgres \
  --name pg_qs.query_capture_mode \
  --value TOP

# Check slow queries
az postgres server-logs list \
  --resource-group trading-bot-rg \
  --server-name trading-bot-postgres
```

#### 2. Application Performance
```bash
# Enable Application Insights profiler
az webapp config appsettings set \
  --resource-group trading-bot-rg \
  --name trading-bot-backend-app \
  --settings APPINSIGHTS_PROFILERFEATURE_VERSION=1.0.0

# Check Application Insights metrics
az monitor app-insights metrics show \
  --app trading-bot-insights \
  --resource-group trading-bot-rg \
  --metric requests/rate
```

## 📚 Additional Resources

### Azure Documentation
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Azure Database for PostgreSQL Documentation](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure Cache for Redis Documentation](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/)

### Cost Management
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- [Azure Cost Management](https://docs.microsoft.com/en-us/azure/cost-management-billing/)

### Monitoring Tools
- [Azure Monitor](https://docs.microsoft.com/en-us/azure/azure-monitor/)
- [Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

---

## 🎯 Quick Deployment Checklist

- [ ] Azure CLI configured and logged in
- [ ] Resource group created
- [ ] Container registry created and images pushed
- [ ] Database (PostgreSQL) and cache (Redis) created
- [ ] App Service or AKS deployed
- [ ] Application Gateway configured
- [ ] SSL certificate configured
- [ ] DNS records configured
- [ ] Monitoring and logging enabled
- [ ] Auto scaling configured
- [ ] Backup strategy implemented
- [ ] Security groups and firewall rules configured
- [ ] Cost monitoring and budgets set up

---

*For additional support with Azure deployment, contact our team or refer to the main [DOCKER_DEPLOYMENT.md](../DOCKER_DEPLOYMENT.md) guide.*