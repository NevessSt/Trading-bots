# 🌊 DigitalOcean Deployment Guide

This guide provides comprehensive instructions for deploying the Trading Bot application on DigitalOcean using Droplets, App Platform, and managed databases.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [App Platform Deployment](#app-platform-deployment)
- [Droplet Deployment](#droplet-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Database Setup](#database-setup)
- [Load Balancer Setup](#load-balancer-setup)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Auto Scaling](#auto-scaling)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### DigitalOcean Account Setup
- DigitalOcean account with billing enabled
- DigitalOcean CLI (doctl) installed and configured
- API token with read/write permissions
- Domain name (optional, for custom domain)

### Required DigitalOcean Services
- **App Platform/Droplets**: Application hosting
- **Managed PostgreSQL**: Database service
- **Managed Redis**: Caching service
- **Load Balancer**: Traffic distribution
- **Spaces**: Object storage
- **Container Registry**: Docker image storage
- **Monitoring**: Application monitoring

### Local Setup
```bash
# Install doctl (Linux/macOS)
wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
tar xf doctl-1.94.0-linux-amd64.tar.gz
sudo mv doctl /usr/local/bin

# Install doctl (Windows)
# Download from: https://github.com/digitalocean/doctl/releases

# Authenticate with DigitalOcean
doctl auth init

# Verify authentication
doctl account get
```

## 🚀 App Platform Deployment (Recommended)

### 1. Create Container Registry

```bash
# Create container registry
doctl registry create trading-bot-registry

# Login to registry
doctl registry login

# Get registry URL
REGISTRY_URL=$(doctl registry get trading-bot-registry --format URL --no-header)
echo "Registry URL: $REGISTRY_URL"
```

### 2. Build and Push Images

```bash
# Tag and push backend image
docker build -t $REGISTRY_URL/trading-bot-backend:latest ./backend
docker push $REGISTRY_URL/trading-bot-backend:latest

# Tag and push frontend image
docker build -t $REGISTRY_URL/trading-bot-frontend:latest ./frontend
docker push $REGISTRY_URL/trading-bot-frontend:latest
```

### 3. Create App Platform Spec

Create `app-platform-spec.yaml`:
```yaml
name: trading-bot-app
services:
- name: backend
  source_dir: /
  github:
    repo: your-username/trading-bot
    branch: main
  dockerfile_path: backend/Dockerfile
  http_port: 5000
  instance_count: 2
  instance_size_slug: basic-xxs
  routes:
  - path: /api
  envs:
  - key: FLASK_ENV
    value: production
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
  - key: REDIS_URL
    value: ${redis.DATABASE_URL}
  - key: SECRET_KEY
    value: your-secret-key
    type: SECRET
  - key: JWT_SECRET_KEY
    value: your-jwt-secret
    type: SECRET

- name: frontend
  source_dir: /
  github:
    repo: your-username/trading-bot
    branch: main
  dockerfile_path: frontend/Dockerfile
  http_port: 3000
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
  envs:
  - key: REACT_APP_API_URL
    value: ${_self.URL}/api
  - key: REACT_APP_WS_URL
    value: wss://${_self.DOMAIN}/api

databases:
- name: db
  engine: PG
  version: "13"
  size: db-s-1vcpu-1gb
  num_nodes: 1

- name: redis
  engine: REDIS
  version: "6"
  size: db-s-1vcpu-1gb
  num_nodes: 1

static_sites:
- name: docs
  source_dir: docs
  github:
    repo: your-username/trading-bot
    branch: main
  routes:
  - path: /docs
```

### 4. Deploy to App Platform

```bash
# Create app from spec
doctl apps create --spec app-platform-spec.yaml

# Get app ID
APP_ID=$(doctl apps list --format ID --no-header)

# Monitor deployment
doctl apps get $APP_ID

# Get app URL
doctl apps get $APP_ID --format LiveURL --no-header
```

### 5. Configure Custom Domain

```bash
# Add custom domain
doctl apps update $APP_ID --spec app-platform-spec.yaml

# Get domain configuration
doctl apps get $APP_ID --format Domains
```

## 🖥️ Droplet Deployment (Manual)

### 1. Create Droplets

```bash
# Create droplet for backend
doctl compute droplet create trading-bot-backend \
  --region nyc3 \
  --image docker-20-04 \
  --size s-2vcpu-2gb \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
  --enable-monitoring \
  --enable-private-networking

# Create droplet for frontend
doctl compute droplet create trading-bot-frontend \
  --region nyc3 \
  --image docker-20-04 \
  --size s-1vcpu-1gb \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
  --enable-monitoring \
  --enable-private-networking

# Get droplet IPs
BACKEND_IP=$(doctl compute droplet get trading-bot-backend --format PublicIPv4 --no-header)
FRONTEND_IP=$(doctl compute droplet get trading-bot-frontend --format PublicIPv4 --no-header)

echo "Backend IP: $BACKEND_IP"
echo "Frontend IP: $FRONTEND_IP"
```

### 2. Setup Docker on Droplets

```bash
# SSH to backend droplet
ssh root@$BACKEND_IP

# Update system
apt update && apt upgrade -y

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/your-username/trading-bot.git
cd trading-bot

# Create environment file
cp .env.example .env
nano .env  # Edit with your configuration
```

### 3. Deploy with Docker Compose

Create `docker-compose.droplet.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: trading-bot-backend
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - trading-bot-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: 
      context: ./frontend
      args:
        - REACT_APP_API_URL=https://api.yourdomain.com
        - REACT_APP_WS_URL=wss://api.yourdomain.com
    container_name: trading-bot-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    networks:
      - trading-bot-network
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    container_name: trading-bot-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - trading-bot-network
    depends_on:
      - backend
      - frontend

networks:
  trading-bot-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

```bash
# Deploy application
docker-compose -f docker-compose.droplet.yml up -d

# Check status
docker-compose -f docker-compose.droplet.yml ps

# View logs
docker-compose -f docker-compose.droplet.yml logs -f
```

## ☸️ Kubernetes Deployment (DOKS)

### 1. Create DOKS Cluster

```bash
# Create Kubernetes cluster
doctl kubernetes cluster create trading-bot-k8s \
  --region nyc3 \
  --version 1.28.2-do.0 \
  --count 3 \
  --size s-2vcpu-2gb \
  --auto-upgrade=true \
  --maintenance-window="saturday=02:00" \
  --surge-upgrade=true

# Get cluster credentials
doctl kubernetes cluster kubeconfig save trading-bot-k8s

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### 2. Install Ingress Controller

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/do/deploy.yaml

# Wait for load balancer
kubectl get svc -n ingress-nginx
```

### 3. Deploy Application

Create `k8s/trading-bot-deployment.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trading-bot
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: trading-bot
type: Opaque
stringData:
  database-url: "postgresql://username:password@db-postgresql-nyc3-12345-do-user-123456-0.b.db.ondigitalocean.com:25060/trading_bot?sslmode=require"
  redis-url: "redis://default:password@db-redis-nyc3-12345-do-user-123456-0.b.db.ondigitalocean.com:25061/0?ssl_cert_reqs=required"
  secret-key: "your-secret-key"
  jwt-secret: "your-jwt-secret"
---
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
        image: registry.digitalocean.com/trading-bot-registry/trading-bot-backend:latest
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
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
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
---
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
        image: registry.digitalocean.com/trading-bot-registry/trading-bot-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://yourdomain.com/api"
        - name: REACT_APP_WS_URL
          value: "wss://yourdomain.com/api"
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
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: trading-bot-ingress
  namespace: trading-bot
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: trading-bot-tls
  rules:
  - host: yourdomain.com
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

```bash
# Deploy application
kubectl apply -f k8s/trading-bot-deployment.yaml

# Check deployment status
kubectl get pods -n trading-bot
kubectl get services -n trading-bot
kubectl get ingress -n trading-bot
```

## 🗄️ Database Setup

### 1. Create Managed PostgreSQL

```bash
# Create PostgreSQL cluster
doctl databases create trading-bot-postgres \
  --engine postgres \
  --version 13 \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Get database ID
DB_ID=$(doctl databases list --format ID --no-header | head -1)

# Create database
doctl databases db create $DB_ID trading_bot

# Create user
doctl databases user create $DB_ID trading_bot_user

# Get connection details
doctl databases connection $DB_ID
```

### 2. Create Managed Redis

```bash
# Create Redis cluster
doctl databases create trading-bot-redis \
  --engine redis \
  --version 6 \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Get Redis connection details
REDIS_ID=$(doctl databases list --format ID --no-header | tail -1)
doctl databases connection $REDIS_ID
```

### 3. Configure Database Security

```bash
# Add trusted sources (your droplets/app platform)
doctl databases firewalls append $DB_ID --rule type:droplet,value:$BACKEND_DROPLET_ID
doctl databases firewalls append $DB_ID --rule type:app,value:$APP_ID

# List firewall rules
doctl databases firewalls list $DB_ID
```

## ⚖️ Load Balancer Setup

### 1. Create Load Balancer

```bash
# Create load balancer
doctl compute load-balancer create \
  --name trading-bot-lb \
  --region nyc3 \
  --forwarding-rules entry_protocol:https,entry_port:443,target_protocol:http,target_port:5000,certificate_id:$CERT_ID \
  --forwarding-rules entry_protocol:http,entry_port:80,target_protocol:http,target_port:5000 \
  --health-check protocol:http,port:5000,path:/health,check_interval_seconds:10,response_timeout_seconds:5,unhealthy_threshold:3,healthy_threshold:2 \
  --droplet-ids $BACKEND_DROPLET_ID

# Get load balancer IP
LB_IP=$(doctl compute load-balancer list --format IP --no-header)
echo "Load Balancer IP: $LB_IP"
```

### 2. Configure Health Checks

```bash
# Update health check settings
doctl compute load-balancer update trading-bot-lb \
  --health-check protocol:http,port:5000,path:/health,check_interval_seconds:10,response_timeout_seconds:5,unhealthy_threshold:3,healthy_threshold:2
```

## 🔒 SSL Certificate Setup

### 1. Create SSL Certificate

```bash
# Create Let's Encrypt certificate
doctl compute certificate create \
  --name trading-bot-cert \
  --dns-names yourdomain.com,www.yourdomain.com \
  --type lets_encrypt

# Get certificate ID
CERT_ID=$(doctl compute certificate list --format ID --no-header)

# Add certificate to load balancer
doctl compute load-balancer add-forwarding-rules trading-bot-lb \
  --forwarding-rules entry_protocol:https,entry_port:443,target_protocol:http,target_port:5000,certificate_id:$CERT_ID
```

### 2. Install Cert-Manager (for Kubernetes)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## 📊 Monitoring & Logging

### 1. Enable DigitalOcean Monitoring

```bash
# Install monitoring agent on droplets
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash

# Configure monitoring
sudo systemctl enable do-agent
sudo systemctl start do-agent
```

### 2. Setup Application Monitoring

Create `monitoring/docker-compose.monitoring.yml`:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus_data:
  grafana_data:
```

### 3. Configure Alerts

Create `monitoring/alertmanager.yml`:
```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourdomain.com'
    subject: 'Trading Bot Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
```

## 🔄 Auto Scaling

### 1. App Platform Auto Scaling

```yaml
# Update app-platform-spec.yaml
services:
- name: backend
  # ... other config
  autoscaling:
    min_instance_count: 2
    max_instance_count: 10
    metrics:
    - type: cpu
      target: 70
```

### 2. Kubernetes HPA

```bash
# Create HPA for backend
kubectl autoscale deployment backend-deployment \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  --namespace=trading-bot

# Create HPA for frontend
kubectl autoscale deployment frontend-deployment \
  --cpu-percent=70 \
  --min=1 \
  --max=5 \
  --namespace=trading-bot

# Check HPA status
kubectl get hpa -n trading-bot
```

### 3. Cluster Auto Scaling

```bash
# Enable cluster autoscaler
doctl kubernetes cluster update trading-bot-k8s \
  --auto-upgrade=true \
  --surge-upgrade=true

# Create node pool with autoscaling
doctl kubernetes cluster node-pool create trading-bot-k8s \
  --name autoscale-pool \
  --size s-2vcpu-2gb \
  --count 1 \
  --min-nodes 1 \
  --max-nodes 10 \
  --auto-scale=true
```

## 💰 Cost Optimization

### 1. Resource Optimization

```bash
# List all resources and costs
doctl compute droplet list --format Name,Size,PriceMonthly
doctl databases list --format Name,Engine,Size,PriceMonthly
doctl kubernetes cluster list --format Name,NodePools,PriceMonthly

# Resize droplets if needed
doctl compute droplet-action resize $DROPLET_ID --size s-1vcpu-1gb --resize-disk
```

### 2. Reserved Instances

```bash
# Check available reserved instances
doctl compute reserved-ip list

# Create reserved IP
doctl compute reserved-ip create --region nyc3 --type assign --resource $DROPLET_ID
```

### 3. Monitoring Costs

```bash
# Get billing information
doctl account get

# Monitor usage
doctl compute droplet list --format Name,Status,CreatedAt
doctl databases list --format Name,Status,CreatedAt
```

## 🔧 Troubleshooting

### Common Issues

#### 1. App Platform Deployment Issues
```bash
# Check app logs
doctl apps logs $APP_ID --type build
doctl apps logs $APP_ID --type deploy
doctl apps logs $APP_ID --type run

# Check app status
doctl apps get $APP_ID

# Redeploy app
doctl apps create-deployment $APP_ID
```

#### 2. Droplet Connection Issues
```bash
# Check droplet status
doctl compute droplet get $DROPLET_ID

# Access droplet console
doctl compute droplet-action enable-ipv6 $DROPLET_ID

# Reset droplet
doctl compute droplet-action reboot $DROPLET_ID
```

#### 3. Database Connection Issues
```bash
# Check database status
doctl databases get $DB_ID

# Test connection
psql "postgresql://username:password@host:port/database?sslmode=require"

# Check firewall rules
doctl databases firewalls list $DB_ID
```

#### 4. Kubernetes Issues
```bash
# Check cluster status
doctl kubernetes cluster get trading-bot-k8s

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check pod logs
kubectl logs -f deployment/backend-deployment -n trading-bot

# Debug pod issues
kubectl describe pod <pod-name> -n trading-bot
```

### Performance Optimization

#### 1. Database Performance
```bash
# Check database metrics
doctl databases get $DB_ID --format Name,Status,Engine,Version,Size,NumNodes

# Resize database if needed
doctl databases resize $DB_ID --size db-s-2vcpu-2gb --num-nodes 1

# Create read replica
doctl databases replica create $DB_ID trading-bot-replica --region nyc3 --size db-s-1vcpu-1gb
```

#### 2. Application Performance
```bash
# Monitor droplet resources
doctl monitoring metrics droplet cpu $DROPLET_ID --start 2024-01-01T00:00:00Z --end 2024-01-02T00:00:00Z
doctl monitoring metrics droplet memory $DROPLET_ID --start 2024-01-01T00:00:00Z --end 2024-01-02T00:00:00Z

# Check load balancer metrics
doctl compute load-balancer get trading-bot-lb
```

## 📚 Additional Resources

### DigitalOcean Documentation
- [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Kubernetes Documentation](https://docs.digitalocean.com/products/kubernetes/)
- [Managed Databases Documentation](https://docs.digitalocean.com/products/databases/)
- [Load Balancers Documentation](https://docs.digitalocean.com/products/networking/load-balancers/)

### Cost Management
- [DigitalOcean Pricing](https://www.digitalocean.com/pricing/)
- [Cost Optimization Guide](https://docs.digitalocean.com/products/billing/)

### Monitoring Tools
- [DigitalOcean Monitoring](https://docs.digitalocean.com/products/monitoring/)
- [Uptime Monitoring](https://docs.digitalocean.com/products/monitoring/uptime/)

---

## 🎯 Quick Deployment Checklist

- [ ] DigitalOcean CLI configured and authenticated
- [ ] Container registry created and images pushed
- [ ] Database (PostgreSQL) and cache (Redis) created
- [ ] App Platform/Droplets/DOKS deployed
- [ ] Load balancer configured
- [ ] SSL certificate configured
- [ ] DNS records configured
- [ ] Monitoring and logging enabled
- [ ] Auto scaling configured
- [ ] Backup strategy implemented
- [ ] Firewall rules configured
- [ ] Cost monitoring set up

---

*For additional support with DigitalOcean deployment, contact our team or refer to the main [DOCKER_DEPLOYMENT.md](../DOCKER_DEPLOYMENT.md) guide.*