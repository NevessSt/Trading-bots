# 🚀 AWS Deployment Guide

This guide provides step-by-step instructions for deploying the Trading Bot application on Amazon Web Services (AWS) using various AWS services.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [ECS Deployment](#ecs-deployment)
- [EC2 Deployment](#ec2-deployment)
- [RDS & ElastiCache Setup](#rds--elasticache-setup)
- [Load Balancer Configuration](#load-balancer-configuration)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Auto Scaling](#auto-scaling)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### AWS Account Setup
- AWS Account with billing enabled
- AWS CLI installed and configured
- IAM user with appropriate permissions
- Domain name (optional, for custom domain)

### Required AWS Services
- **ECS/EC2**: Container/compute hosting
- **RDS**: PostgreSQL database
- **ElastiCache**: Redis caching
- **ALB**: Application Load Balancer
- **Route 53**: DNS management
- **ACM**: SSL certificates
- **CloudWatch**: Monitoring and logging
- **S3**: File storage and backups

### Local Setup
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure
# Enter your Access Key ID, Secret Access Key, Region, and Output format

# Install ECS CLI
sudo curl -Lo /usr/local/bin/ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest
sudo chmod +x /usr/local/bin/ecs-cli
```

## 🐳 ECS Deployment (Recommended)

### 1. Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name trading-bot-cluster

# Create task execution role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### 2. Build and Push Docker Images

```bash
# Create ECR repositories
aws ecr create-repository --repository-name trading-bot-backend
aws ecr create-repository --repository-name trading-bot-frontend

# Get login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Build and push backend
docker build -t trading-bot-backend ./backend
docker tag trading-bot-backend:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/trading-bot-backend:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/trading-bot-backend:latest

# Build and push frontend
docker build -t trading-bot-frontend ./frontend
docker tag trading-bot-frontend:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/trading-bot-frontend:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/trading-bot-frontend:latest
```

### 3. Create Task Definitions

Create `backend-task-definition.json`:
```json
{
  "family": "trading-bot-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-west-2.amazonaws.com/trading-bot-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "DATABASE_URL", "value": "postgresql://username:password@rds-endpoint:5432/trading_bot"},
        {"name": "REDIS_URL", "value": "redis://elasticache-endpoint:6379/0"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/trading-bot-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 4. Create ECS Services

```bash
# Register task definitions
aws ecs register-task-definition --cli-input-json file://backend-task-definition.json
aws ecs register-task-definition --cli-input-json file://frontend-task-definition.json

# Create services
aws ecs create-service \
  --cluster trading-bot-cluster \
  --service-name backend-service \
  --task-definition trading-bot-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}"
```

## 🖥️ EC2 Deployment

### 1. Launch EC2 Instance

```bash
# Create security group
aws ec2 create-security-group --group-name trading-bot-sg --description "Trading Bot Security Group"

# Add rules
aws ec2 authorize-security-group-ingress --group-name trading-bot-sg --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name trading-bot-sg --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name trading-bot-sg --protocol tcp --port 443 --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups trading-bot-sg \
  --user-data file://user-data.sh
```

### 2. User Data Script

Create `user-data.sh`:
```bash
#!/bin/bash
yum update -y
yum install -y docker git

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Clone and deploy
cd /home/ec2-user
git clone https://github.com/your-repo/trading-bot.git
cd trading-bot

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 🗄️ RDS & ElastiCache Setup

### 1. Create RDS PostgreSQL Instance

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name trading-bot-subnet-group \
  --db-subnet-group-description "Trading Bot DB Subnet Group" \
  --subnet-ids subnet-12345 subnet-67890

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier trading-bot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YourSecurePassword123 \
  --allocated-storage 20 \
  --storage-type gp2 \
  --db-subnet-group-name trading-bot-subnet-group \
  --vpc-security-group-ids sg-database \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted
```

### 2. Create ElastiCache Redis Cluster

```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name trading-bot-cache-subnet \
  --cache-subnet-group-description "Trading Bot Cache Subnet Group" \
  --subnet-ids subnet-12345 subnet-67890

# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id trading-bot-redis \
  --description "Trading Bot Redis Cluster" \
  --node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-clusters 2 \
  --cache-subnet-group-name trading-bot-cache-subnet \
  --security-group-ids sg-cache \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

## ⚖️ Load Balancer Configuration

### 1. Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name trading-bot-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-alb \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target groups
aws elbv2 create-target-group \
  --name trading-bot-backend-tg \
  --protocol HTTP \
  --port 5000 \
  --vpc-id vpc-12345 \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

aws elbv2 create-target-group \
  --name trading-bot-frontend-tg \
  --protocol HTTP \
  --port 3000 \
  --vpc-id vpc-12345 \
  --health-check-path / \
  --health-check-interval-seconds 30
```

### 2. Create Listeners

```bash
# HTTP listener (redirect to HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/trading-bot-alb/1234567890123456 \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'

# HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/trading-bot-alb/1234567890123456 \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/trading-bot-frontend-tg/1234567890123456
```

## 🔒 SSL Certificate Setup

### 1. Request Certificate via ACM

```bash
# Request certificate
aws acm request-certificate \
  --domain-name tradingbot.yourdomain.com \
  --subject-alternative-names '*.tradingbot.yourdomain.com' \
  --validation-method DNS \
  --region us-west-2

# Get certificate details
aws acm describe-certificate --certificate-arn arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012
```

### 2. DNS Validation

```bash
# Add CNAME records to Route 53 for validation
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://dns-validation.json
```

## 📊 Monitoring & Logging

### 1. CloudWatch Setup

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/trading-bot-backend
aws logs create-log-group --log-group-name /ecs/trading-bot-frontend

# Create custom metrics
aws cloudwatch put-metric-alarm \
  --alarm-name "TradingBot-HighCPU" \
  --alarm-description "Trading Bot High CPU Usage" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 2. CloudWatch Dashboard

Create `dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "backend-service"],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", "backend-service"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "ECS Service Metrics"
      }
    }
  ]
}
```

## 🔄 Auto Scaling

### 1. ECS Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/trading-bot-cluster/backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/trading-bot-cluster/backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name trading-bot-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### 2. Scaling Policy Configuration

Create `scaling-policy.json`:
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleOutCooldown": 300,
  "ScaleInCooldown": 300
}
```

## 💰 Cost Optimization

### 1. Reserved Instances

```bash
# Purchase RDS Reserved Instance
aws rds purchase-reserved-db-instances-offering \
  --reserved-db-instances-offering-id 12345678-1234-1234-1234-123456789012 \
  --reserved-db-instance-id trading-bot-reserved-db

# Purchase ElastiCache Reserved Nodes
aws elasticache purchase-reserved-cache-nodes-offering \
  --reserved-cache-nodes-offering-id 12345678-1234-1234-1234-123456789012 \
  --reserved-cache-node-id trading-bot-reserved-cache
```

### 2. Spot Instances (for non-critical workloads)

```bash
# Create Spot Fleet for batch processing
aws ec2 create-spot-fleet --spot-fleet-request-config file://spot-fleet-config.json
```

### 3. Cost Monitoring

```bash
# Create budget
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

## 🔧 Troubleshooting

### Common Issues

#### 1. ECS Task Fails to Start
```bash
# Check task definition
aws ecs describe-task-definition --task-definition trading-bot-backend

# Check service events
aws ecs describe-services --cluster trading-bot-cluster --services backend-service

# Check logs
aws logs get-log-events --log-group-name /ecs/trading-bot-backend --log-stream-name ecs/backend/task-id
```

#### 2. Database Connection Issues
```bash
# Test RDS connectivity
aws rds describe-db-instances --db-instance-identifier trading-bot-db

# Check security groups
aws ec2 describe-security-groups --group-ids sg-database
```

#### 3. Load Balancer Health Checks Failing
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/trading-bot-backend-tg/1234567890123456

# Check ALB logs
aws s3 cp s3://your-alb-logs-bucket/AWSLogs/123456789012/elasticloadbalancing/us-west-2/ . --recursive
```

### Performance Optimization

#### 1. Database Performance
```sql
-- Connect to RDS and run performance queries
SELECT * FROM pg_stat_activity WHERE state = 'active';
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

#### 2. Application Performance
```bash
# Enable X-Ray tracing
aws xray create-service-map --service-names trading-bot-backend

# Check CloudWatch Insights
aws logs start-query \
  --log-group-name /ecs/trading-bot-backend \
  --start-time 1609459200 \
  --end-time 1609545600 \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/'
```

## 📚 Additional Resources

### AWS Documentation
- [ECS Developer Guide](https://docs.aws.amazon.com/ecs/)
- [RDS User Guide](https://docs.aws.amazon.com/rds/)
- [ElastiCache User Guide](https://docs.aws.amazon.com/elasticache/)
- [Application Load Balancer Guide](https://docs.aws.amazon.com/elasticloadbalancing/)

### Cost Calculators
- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)

### Monitoring Tools
- [AWS CloudWatch](https://aws.amazon.com/cloudwatch/)
- [AWS X-Ray](https://aws.amazon.com/xray/)
- [AWS Config](https://aws.amazon.com/config/)

---

## 🎯 Quick Deployment Checklist

- [ ] AWS CLI configured
- [ ] Docker images built and pushed to ECR
- [ ] RDS PostgreSQL instance created
- [ ] ElastiCache Redis cluster created
- [ ] ECS cluster and services deployed
- [ ] Application Load Balancer configured
- [ ] SSL certificate obtained and configured
- [ ] DNS records configured
- [ ] Monitoring and logging set up
- [ ] Auto scaling configured
- [ ] Backup strategy implemented
- [ ] Security groups properly configured
- [ ] Cost monitoring enabled

---

*For additional support with AWS deployment, contact our team or refer to the main [DOCKER_DEPLOYMENT.md](../DOCKER_DEPLOYMENT.md) guide.*