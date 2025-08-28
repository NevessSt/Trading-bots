# License Revocation System

The TradingBot Pro includes a comprehensive license revocation system that allows remote license management and control. This system provides both local and remote validation capabilities to ensure license compliance.

## Overview

The license revocation system consists of:
- **License Server**: Remote server for license validation and revocation management
- **Local Cache**: Client-side caching of revocation lists for offline operation
- **Admin Tools**: Command-line interface for license management
- **Automatic Fallback**: Graceful degradation when remote services are unavailable

## Components

### 1. License Server (`license_server.py`)

A Flask-based server that provides:
- License validation endpoints
- Revocation management
- License generation
- Statistics and monitoring
- Health checks

**Key Features:**
- SQLite database for license storage
- HMAC signature verification
- Revocation list management
- Audit logging
- RESTful API

### 2. Enhanced License Validation (`license_check.py`)

Updated license validation with:
- Remote revocation checking
- Local cache management
- Fallback mechanisms
- Configurable timeouts

### 3. Admin CLI Tool (`scripts/license_admin.py`)

Command-line interface for:
- Generating licenses
- Revoking licenses
- Validating licenses
- Viewing statistics
- Managing the license server

## Configuration

### Environment Variables

```bash
# License Server Configuration
LICENSE_SERVER_URL=https://license.tradingbot.pro
LICENSE_SERVER_PORT=8080
LICENSE_SERVER_SECRET=your-secret-key-here
LICENSE_ADMIN_KEY=your-admin-api-key

# Client Configuration
ENABLE_REMOTE_LICENSE_CHECK=true
LICENSE_CACHE_TIMEOUT=3600  # 1 hour in seconds

# Flask Configuration
FLASK_DEBUG=false
```

### Database Setup

The license server automatically creates its SQLite database on first run:
- `licenses` table: Active license records
- `revocation_list` table: Revoked license tracking
- `license_checks` table: Validation audit log

## Usage

### Starting the License Server

```bash
# Start server on default port (8080)
python scripts/license_admin.py start-server

# Start on custom port with debug mode
python scripts/license_admin.py start-server --port 9000 --debug

# Or run directly
python backend/license_server.py
```

### Generating Licenses

```bash
# Generate standard license
python scripts/license_admin.py generate MACHINE_ID_HERE

# Generate premium license with custom features
python scripts/license_admin.py generate MACHINE_ID_HERE \
  --type premium \
  --days 730 \
  --features advanced_trading portfolio_management api_access
```

### Revoking Licenses

```bash
# Revoke a license
python scripts/license_admin.py revoke LICENSE_KEY_HERE "License violation"

# Revoke with specific admin attribution
python scripts/license_admin.py revoke LICENSE_KEY_HERE \
  "Chargeback received" \
  --revoked-by "admin@company.com"
```

### Validating Licenses

```bash
# Validate a license
python scripts/license_admin.py validate LICENSE_KEY_HERE MACHINE_ID_HERE
```

### Monitoring and Statistics

```bash
# Check server health
python scripts/license_admin.py health

# View license statistics
python scripts/license_admin.py stats

# List revoked licenses
python scripts/license_admin.py list-revoked
```

## API Endpoints

### Public Endpoints

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0"
}
```

#### `POST /validate`
Validate a license

**Request:**
```json
{
  "license_key": "license_key_here",
  "machine_id": "machine_id_here"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "License is valid",
  "timestamp": "2024-01-15T10:30:00Z",
  "license_data": {
    "license_type": "premium",
    "expires_at": "2025-01-15T10:30:00Z",
    "features": ["advanced_trading", "portfolio_management"]
  }
}
```

#### `GET /revocation-list`
Get list of revoked licenses

**Response:**
```json
{
  "revoked_licenses": [
    {
      "license_key": "abc123...",
      "revoked_at": "2024-01-15T10:30:00Z",
      "reason": "License violation",
      "revoked_by": "admin"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Admin Endpoints (Require API Key)

#### `POST /generate`
Generate a new license

**Headers:**
```
X-API-Key: your-admin-api-key
```

**Request:**
```json
{
  "machine_id": "machine_id_here",
  "license_type": "premium",
  "days_valid": 365,
  "features": ["advanced_trading", "portfolio_management"]
}
```

#### `POST /revoke`
Revoke a license

**Headers:**
```
X-API-Key: your-admin-api-key
```

**Request:**
```json
{
  "license_key": "license_key_here",
  "reason": "License violation",
  "revoked_by": "admin@company.com"
}
```

#### `GET /stats`
Get license statistics

**Response:**
```json
{
  "total_licenses": 150,
  "active_licenses": 142,
  "revoked_licenses": 5,
  "expired_licenses": 3,
  "recent_checks": 45,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Client Integration

### Automatic Revocation Checking

The client automatically checks for revoked licenses:

1. **Local Cache Check**: First checks local revocation cache
2. **Remote Validation**: If cache is expired, contacts license server
3. **Cache Update**: Updates local cache with latest revocation list
4. **Graceful Fallback**: Falls back to local validation if remote fails

### Configuration Options

```python
from backend.license_check import LicenseValidator

# Initialize with custom settings
validator = LicenseValidator()
validator.license_server_url = "https://your-license-server.com"
validator.enable_remote_check = True
validator.cache_timeout = 7200  # 2 hours

# Validate license
is_valid, message, license_data = validator.validate_license()

# Force remote validation
is_valid, message, license_data = validator.force_remote_validation()

# Check cache status
cache_info = validator.get_revocation_cache_info()
```

## Security Considerations

### License Server Security

1. **API Key Authentication**: Admin endpoints require API key
2. **HMAC Signatures**: License keys use HMAC for integrity
3. **Rate Limiting**: Implement rate limiting in production
4. **HTTPS Only**: Always use HTTPS in production
5. **Database Security**: Secure SQLite database file permissions

### Client Security

1. **Cache Protection**: Revocation cache stored securely
2. **Fallback Behavior**: Graceful degradation prevents bypass
3. **Timeout Handling**: Reasonable timeouts prevent hanging
4. **Error Logging**: Comprehensive logging for audit trails

## Deployment

### Production Deployment

1. **Use HTTPS**: Deploy behind reverse proxy with SSL
2. **Database Backup**: Regular backups of license database
3. **Monitoring**: Set up health checks and alerting
4. **Load Balancing**: Use multiple server instances if needed
5. **API Key Rotation**: Regular rotation of admin API keys

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/license_server.py .
COPY backend/license_check.py .

EXPOSE 8080
CMD ["python", "license_server.py"]
```

### Environment Setup

```bash
# Production environment
export LICENSE_SERVER_URL=https://license.tradingbot.pro
export LICENSE_SERVER_SECRET=your-production-secret
export LICENSE_ADMIN_KEY=your-production-admin-key
export FLASK_DEBUG=false

# Start server
python backend/license_server.py
```

## Monitoring and Maintenance

### Health Monitoring

- Monitor `/health` endpoint
- Track license validation response times
- Alert on high error rates
- Monitor database size and performance

### Regular Maintenance

- Clean up old license check logs
- Backup license database
- Rotate API keys
- Update revocation lists
- Monitor for suspicious activity

### Troubleshooting

#### Common Issues

1. **Remote Validation Timeout**
   - Check network connectivity
   - Verify server URL configuration
   - Review server logs

2. **Cache Issues**
   - Clear revocation cache: `rm backend/config/revocation_cache.json`
   - Check cache permissions
   - Verify cache timeout settings

3. **Database Errors**
   - Check SQLite file permissions
   - Verify disk space
   - Review database integrity

#### Debug Commands

```bash
# Test server connectivity
curl -X GET https://license.tradingbot.pro/health

# Validate license manually
curl -X POST https://license.tradingbot.pro/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"...","machine_id":"..."}'

# Check revocation list
curl -X GET https://license.tradingbot.pro/revocation-list
```

## Best Practices

1. **Regular Updates**: Keep revocation cache updated
2. **Graceful Degradation**: Always allow local fallback
3. **Audit Logging**: Log all license operations
4. **Secure Storage**: Protect license server credentials
5. **Monitoring**: Monitor license server health
6. **Backup Strategy**: Regular database backups
7. **Testing**: Test revocation scenarios regularly

## Support

For license revocation system support:
- Email: license-support@tradingbot.pro
- Documentation: Check this file and API documentation
- Logs: Review application logs for detailed error information
- Health Check: Use `/health` endpoint to verify server status

---

*This license revocation system provides enterprise-grade license management capabilities while maintaining reliability through local fallback mechanisms.*