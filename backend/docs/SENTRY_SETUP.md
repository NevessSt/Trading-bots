# Sentry Integration Setup

This document explains how to set up and configure Sentry error tracking and monitoring for the Trading Bot Platform.

## Overview

Sentry provides real-time error tracking, performance monitoring, and alerting for the trading bot application. It helps identify and debug issues in production environments.

## Features

- **Error Tracking**: Automatic capture of exceptions and errors
- **Performance Monitoring**: Track slow requests and database queries
- **User Context**: Associate errors with specific users and trading sessions
- **Trading Context**: Track bot IDs, exchanges, and trading symbols
- **Breadcrumbs**: Detailed execution trail for debugging
- **Filtering**: Smart filtering to reduce noise and focus on actionable errors
- **Integrations**: Flask, SQLAlchemy, Redis, and Celery integration

## Installation

Sentry SDK is already included in the requirements.txt:

```bash
pip install sentry-sdk[flask]==1.38.0
```

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Sentry Configuration
SENTRY_ENABLED=true
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production  # or development, staging
SENTRY_SAMPLE_RATE=1.0         # 1.0 = 100% of errors
SENTRY_TRACES_SAMPLE_RATE=0.1  # 0.1 = 10% of transactions
APP_VERSION=1.0.0              # Your app version
```

### Getting Your Sentry DSN

1. Create a Sentry account at [sentry.io](https://sentry.io)
2. Create a new project for your trading bot
3. Select "Flask" as the platform
4. Copy the DSN from the project settings
5. Add it to your environment variables

### Environment-Specific Configuration

#### Development
```bash
SENTRY_ENABLED=false           # Disable in development
SENTRY_ENVIRONMENT=development
SENTRY_SAMPLE_RATE=1.0
SENTRY_TRACES_SAMPLE_RATE=1.0  # Higher sampling for testing
```

#### Staging
```bash
SENTRY_ENABLED=true
SENTRY_ENVIRONMENT=staging
SENTRY_SAMPLE_RATE=1.0
SENTRY_TRACES_SAMPLE_RATE=0.5
```

#### Production
```bash
SENTRY_ENABLED=true
SENTRY_ENVIRONMENT=production
SENTRY_SAMPLE_RATE=1.0
SENTRY_TRACES_SAMPLE_RATE=0.1  # Lower sampling to reduce overhead
```

## Usage

### Automatic Error Tracking

Sentry automatically captures:
- Unhandled exceptions in Flask routes
- Database errors from SQLAlchemy
- Redis connection errors
- Celery task failures
- HTTP errors and timeouts

### Manual Error Tracking

```python
from utils.sentry_config import capture_exception, capture_message

try:
    # Your trading logic here
    execute_trade()
except Exception as e:
    capture_exception(e, 
        bot_id="bot_123",
        exchange="binance",
        symbol="BTCUSDT"
    )
    raise

# Capture informational messages
capture_message(
    "Trade executed successfully",
    level="info",
    bot_id="bot_123",
    profit=150.25
)
```

### Trading-Specific Decorators

```python
from middleware.sentry_middleware import track_trading_operation

@track_trading_operation("buy_order")
def place_buy_order(symbol, quantity, price):
    # Your trading logic
    pass
```

### Setting Context

```python
from utils.sentry_config import set_user_context, set_trading_context

# Set user context
set_user_context(
    user_id="user_123",
    email="trader@example.com",
    subscription_tier="pro"
)

# Set trading context
set_trading_context(
    bot_id="bot_456",
    exchange="binance",
    symbol="ETHUSDT",
    strategy="momentum"
)
```

### Adding Breadcrumbs

```python
from utils.sentry_config import add_breadcrumb

add_breadcrumb(
    message="Starting market analysis",
    category="trading",
    level="info",
    data={
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "indicators": ["RSI", "MACD"]
    }
)
```

## Error Filtering

The Sentry configuration includes smart filtering to reduce noise:

### Filtered Errors
- HTTP 4xx client errors (unless server errors)
- Validation errors (user input errors)
- Connection timeouts (unless persistent)
- Test environment errors

### Sensitive Data Protection
- API keys are automatically filtered
- Authorization headers are masked
- Personal information is excluded

## Performance Monitoring

Sentry tracks:
- Request response times
- Database query performance
- Celery task execution times
- Trading operation latency

### Slow Request Alerts
Requests taking longer than 5 seconds are automatically logged as warnings.

## Alerts and Notifications

### Setting Up Alerts

1. Go to your Sentry project dashboard
2. Navigate to **Alerts** → **Rules**
3. Create rules for:
   - New error types
   - Error frequency spikes
   - Performance degradation
   - Trading-specific errors

### Recommended Alert Rules

```yaml
# High-priority trading errors
Condition: Event type equals "error"
Filter: Event tags contain "component:trading_engine"
Action: Send email to trading team

# Performance degradation
Condition: Average response time > 2 seconds
Filter: Transaction name contains "/api/trading/"
Action: Send Slack notification

# API connection failures
Condition: Event message contains "API connection failed"
Filter: Event tags contain "exchange:binance"
Action: Send immediate alert
```

## Dashboard and Monitoring

### Key Metrics to Monitor

1. **Error Rate**: Percentage of requests resulting in errors
2. **Response Time**: Average API response times
3. **Trading Errors**: Bot-specific error rates
4. **Exchange Connectivity**: API connection success rates
5. **User Impact**: Errors affecting user experience

### Custom Dashboards

Create custom dashboards for:
- Trading performance metrics
- Exchange-specific error rates
- Bot health monitoring
- User activity tracking

## Troubleshooting

### Common Issues

#### Sentry Not Capturing Errors
```bash
# Check if Sentry is enabled
echo $SENTRY_ENABLED

# Verify DSN configuration
echo $SENTRY_DSN

# Check application logs
tail -f logs/trading_bot.log | grep -i sentry
```

#### High Error Volume
```python
# Adjust sample rates in production
SENTRY_SAMPLE_RATE=0.5        # Reduce to 50%
SENTRY_TRACES_SAMPLE_RATE=0.05 # Reduce to 5%
```

#### Missing Context
```python
# Ensure middleware is properly initialized
# Check app.py for SentryMiddleware initialization
```

### Testing Sentry Integration

```python
# Test error capture
from utils.sentry_config import capture_exception

try:
    raise ValueError("Test error for Sentry")
except Exception as e:
    capture_exception(e, test=True)
```

```bash
# Test via API endpoint
curl -X POST http://localhost:5000/api/test/sentry-error
```

## Security Considerations

- **API Keys**: Never log API keys or secrets
- **User Data**: Avoid sending PII to Sentry
- **Trading Data**: Be cautious with sensitive trading information
- **Access Control**: Limit Sentry project access to authorized personnel

## Best Practices

1. **Use Appropriate Log Levels**
   - `error`: For actual errors requiring attention
   - `warning`: For recoverable issues
   - `info`: For important events

2. **Add Meaningful Context**
   - Include relevant trading parameters
   - Add user and session information
   - Provide debugging breadcrumbs

3. **Monitor Performance Impact**
   - Keep sample rates reasonable in production
   - Monitor Sentry's impact on application performance

4. **Regular Maintenance**
   - Review and update alert rules
   - Clean up resolved issues
   - Update error filtering rules

## Integration with Other Tools

### Slack Integration
```yaml
# Add Slack webhook in Sentry project settings
Webhook URL: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
Channel: #trading-alerts
```

### Email Notifications
```yaml
# Configure email alerts
Recipients: trading-team@company.com
Conditions: High-priority errors only
```

### PagerDuty Integration
```yaml
# For critical production alerts
Service: Trading Bot Platform
Escalation: On-call engineer
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review error trends and patterns
2. **Monthly**: Update alert thresholds and rules
3. **Quarterly**: Analyze performance metrics and optimize

### Cleanup

```bash
# Archive old issues (Sentry does this automatically)
# Review and resolve stale alerts
# Update documentation with new error patterns
```

## Support

For issues with Sentry integration:

1. Check the [Sentry documentation](https://docs.sentry.io/)
2. Review application logs for Sentry-related errors
3. Contact the development team with specific error details
4. Use the test endpoints to verify configuration

---

**Note**: Remember to test Sentry integration in a staging environment before deploying to production.