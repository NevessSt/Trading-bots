# Async Task Queue System (Celery)

This document describes the asynchronous task queue system implemented using Celery and Redis for the Trading Bot application.

## Overview

The async task system enables:
- **Non-blocking trade execution** - Trades are queued and processed asynchronously
- **Scheduled tasks** - Periodic market data updates, system maintenance, analytics
- **Background processing** - Notifications, report generation, data cleanup
- **Scalability** - Multiple workers can process tasks concurrently
- **Reliability** - Task retry logic and failure handling

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │───▶│   Redis Broker  │───▶│  Celery Workers │
│                 │    │                 │    │                 │
│ - API Endpoints │    │ - Task Queue    │    │ - Task Execution│
│ - Task Queuing  │    │ - Result Store  │    │ - Error Handling│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       │
                                │                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Beat    │    │   Task Results  │
                       │                 │    │                 │
                       │ - Periodic Tasks│    │ - Success/Failure│
                       │ - Scheduling    │    │ - Return Values │
                       └─────────────────┘    └─────────────────┘
```

## Task Categories

### 1. Trading Tasks (`tasks/trading.py`)
- `execute_trade_async` - Asynchronous trade execution
- `update_market_data` - Fetch latest market prices
- `sync_portfolios` - Synchronize user portfolio data
- `process_order_book` - Analyze order book data
- `calculate_indicators` - Compute technical indicators

### 2. Notification Tasks (`tasks/notifications.py`)
- `send_trade_notification` - Trade execution alerts
- `send_alert_notification` - System alerts
- `send_email_notification` - Email notifications
- `send_telegram_notification` - Telegram messages
- `send_bulk_notifications` - Batch notifications

### 3. Analytics Tasks (`tasks/analytics.py`)
- `calculate_portfolio_performance` - Portfolio metrics
- `generate_trading_report` - Trading reports
- `calculate_risk_metrics` - Risk analysis
- `generate_system_analytics` - System statistics
- `cleanup_old_analytics` - Data retention

### 4. Maintenance Tasks (`tasks/maintenance.py`)
- `system_health_check` - System diagnostics
- `cleanup_old_trades` - Data cleanup
- `cleanup_log_files` - Log rotation
- `database_maintenance` - DB optimization

## Queue Configuration

Tasks are routed to specific queues based on priority and type:

- **`high_priority`** - Critical tasks (trade execution, alerts)
- **`trading`** - Trading-related tasks
- **`notifications`** - Notification tasks
- **`analytics`** - Analytics and reporting
- **`maintenance`** - System maintenance
- **`default`** - General tasks

## Installation & Setup

### 1. Install Dependencies

```bash
# Install Celery dependencies
pip install -r requirements-celery.txt

# Or install individually
pip install celery redis flower
```

### 2. Install Redis

**Windows:**
```bash
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use WSL/Docker
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### 3. Environment Variables

Add to your `.env` file:
```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Optional: Flower monitoring
FLOWER_BASIC_AUTH=admin:admin123
```

## Running the System

### Development Mode

**Option 1: Use the startup script (Recommended)**
```bash
# Start all services
python start_celery.py

# Start with Flower monitoring
python start_celery.py --flower
```

**Option 2: Manual startup**
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
python worker.py

# Terminal 3: Start Celery Beat (for scheduled tasks)
python beat.py

# Terminal 4: Start Flower (optional monitoring)
celery -A celery_app flower --port=5555
```

### Production Mode (Docker)

```bash
# Start all Celery services
docker-compose -f docker-compose.celery.yml up -d

# Scale workers
docker-compose -f docker-compose.celery.yml up -d --scale celery_worker=4

# View logs
docker-compose -f docker-compose.celery.yml logs -f celery_worker
```

## API Usage

### Execute Async Trade
```python
# POST /api/tasks/execute-trade
{
    "user_id": 1,
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.001,
    "order_type": "market"
}

# Response
{
    "task_id": "abc123-def456-ghi789",
    "status": "pending",
    "message": "Trade execution queued"
}
```

### Check Task Status
```python
# GET /api/tasks/status/{task_id}
{
    "task_id": "abc123-def456-ghi789",
    "status": "success",
    "result": {
        "trade_id": 12345,
        "executed_price": 45000.50,
        "executed_quantity": 0.001
    },
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:02Z"
}
```

### Send Notification
```python
# POST /api/tasks/send-notification
{
    "user_id": 1,
    "type": "trade_executed",
    "message": "Your BTC buy order has been executed",
    "channels": ["email", "telegram"]
}
```

## Monitoring

### Flower Web UI
Access the Flower monitoring interface at:
- **URL:** http://localhost:5555
- **Auth:** admin / admin123 (configurable)

**Features:**
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Queue lengths and throughput
- Worker management

### API Endpoints
```python
# Get active tasks
GET /api/tasks/active

# Get worker statistics
GET /api/tasks/workers

# Get queue status
GET /api/tasks/queues

# Health check
GET /api/tasks/health
```

### Logs
Celery logs are written to:
- **Worker logs:** `logs/celery_worker.log`
- **Beat logs:** `logs/celery_beat.log`
- **Task logs:** `logs/celery_tasks.log`

## Scheduled Tasks

The following tasks run automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| `system-health-check` | Every 5 minutes | System diagnostics |
| `update-market-data` | Every 30 seconds | Market price updates |
| `portfolio-sync` | Every 2 minutes | Portfolio synchronization |
| `generate-daily-analytics` | Daily at 00:00 | Daily analytics |
| `generate-weekly-report` | Weekly (Sunday) | Weekly reports |
| `cleanup-old-trades` | Daily at 02:00 | Remove old trade data |
| `cleanup-log-files` | Daily at 03:00 | Log file rotation |
| `database-maintenance` | Weekly at 04:00 | Database optimization |

## Error Handling

### Retry Logic
- **Max retries:** 3 attempts
- **Retry delay:** Exponential backoff (2^retry_count seconds)
- **Retry conditions:** Network errors, temporary API failures

### Dead Letter Queue
Failed tasks after max retries are moved to a dead letter queue for manual inspection.

### Monitoring Alerts
- High error rates trigger notifications
- Worker failures are logged and reported
- Queue backlog alerts when tasks pile up

## Performance Tuning

### Worker Configuration
```python
# worker.py settings
WORKER_CONCURRENCY = 4  # Adjust based on CPU cores
WORKER_PREFETCH_MULTIPLIER = 1  # Tasks per worker
WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker after N tasks
```

### Queue Priorities
```python
# High priority tasks
route_task('execute_trade_async', queue='high_priority')
route_task('send_alert_notification', queue='high_priority')

# Normal priority
route_task('update_market_data', queue='trading')
route_task('send_email_notification', queue='notifications')
```

### Redis Optimization
```redis
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Troubleshooting

### Common Issues

**1. Redis Connection Failed**
```bash
# Check Redis status
redis-cli ping

# Start Redis
redis-server
```

**2. Worker Not Processing Tasks**
```bash
# Check worker status
celery -A celery_app inspect active

# Restart worker
python worker.py
```

**3. Tasks Stuck in Pending**
```bash
# Check queue lengths
celery -A celery_app inspect reserved

# Purge queue (development only)
celery -A celery_app purge
```

**4. High Memory Usage**
```bash
# Monitor worker memory
celery -A celery_app inspect stats

# Restart workers periodically
# Set WORKER_MAX_TASKS_PER_CHILD in worker.py
```

### Debug Mode
```bash
# Run worker with debug logging
celery -A celery_app worker --loglevel=debug

# Run single-threaded for debugging
celery -A celery_app worker --concurrency=1
```

## Security Considerations

1. **Redis Security**
   - Use password authentication in production
   - Bind Redis to localhost only
   - Use Redis ACLs for fine-grained access control

2. **Task Serialization**
   - Avoid pickle serialization (security risk)
   - Use JSON serialization (current default)
   - Validate task parameters

3. **Monitoring Access**
   - Secure Flower with authentication
   - Use HTTPS in production
   - Restrict network access to monitoring ports

## Best Practices

1. **Task Design**
   - Keep tasks idempotent (safe to retry)
   - Use small, focused tasks
   - Avoid long-running tasks (>5 minutes)
   - Handle exceptions gracefully

2. **Resource Management**
   - Monitor memory usage
   - Set appropriate timeouts
   - Use connection pooling
   - Clean up resources in tasks

3. **Monitoring**
   - Set up alerts for failures
   - Monitor queue lengths
   - Track task execution times
   - Log important events

4. **Deployment**
   - Use separate queues for different task types
   - Scale workers based on load
   - Use health checks
   - Implement graceful shutdowns

## Integration with Trading Engine

The async system is integrated with the existing trading engine:

```python
# In trading_engine.py
class TradingEngine:
    def execute_trade_async(self, trade_data):
        """Queue trade for async execution"""
        task = self.task_service.execute_trade_async(trade_data)
        return task.id
    
    def get_task_status(self, task_id):
        """Get status of async task"""
        return self.task_service.get_task_status(task_id)
```

This allows the trading engine to:
- Queue trades without blocking the API
- Track trade execution progress
- Handle multiple concurrent trades
- Provide real-time status updates to users

---

**For more information, see:**
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)