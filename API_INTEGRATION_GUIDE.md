# API Integration Guide

This guide will walk you through integrating your trading bot with popular cryptocurrency exchanges. We'll focus on Binance as the primary example, but the principles apply to other exchanges as well.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Binance API Setup](#binance-api-setup)
3. [API Key Security](#api-key-security)
4. [Configuration](#configuration)
5. [Testing Your Connection](#testing-your-connection)
6. [Common Issues & Troubleshooting](#common-issues--troubleshooting)
7. [Other Exchanges](#other-exchanges)
8. [Best Practices](#best-practices)

## Prerequisites

Before starting, ensure you have:

- ✅ A verified account on your chosen exchange
- ✅ Completed KYC (Know Your Customer) verification
- ✅ Two-factor authentication (2FA) enabled
- ✅ Some funds in your account for testing
- ✅ Basic understanding of API concepts

## Binance API Setup

### Step 1: Create API Keys

1. **Log into Binance**
   - Go to [binance.com](https://binance.com)
   - Sign in to your account

2. **Navigate to API Management**
   - Click on your profile icon (top right)
   - Select "API Management"
   - Or go directly to: Account → API Management

3. **Create New API Key**
   - Click "Create API"
   - Choose "System generated" (recommended)
   - Enter a label (e.g., "Trading Bot")
   - Complete 2FA verification

4. **Configure API Permissions**
   ```
   ✅ Enable Reading
   ✅ Enable Spot & Margin Trading (if needed)
   ❌ Enable Futures (only if you plan to trade futures)
   ❌ Enable Withdrawals (NOT recommended for bots)
   ```

5. **IP Restrictions (Highly Recommended)**
   - Add your server's IP address
   - For local development, add your home IP
   - Never use "Unrestricted" in production

### Step 2: Save Your Credentials

⚠️ **CRITICAL**: Save these immediately - you won't see the secret again!

```
API Key: your_api_key_here
Secret Key: your_secret_key_here
```

## API Key Security

### Environment Variables Setup

1. **Create `.env` file** (if not exists):
   ```bash
   # In your project root directory
   touch .env
   ```

2. **Add your credentials**:
   ```env
   # Binance API Configuration
   BINANCE_API_KEY=your_api_key_here
   BINANCE_SECRET_KEY=your_secret_key_here
   BINANCE_TESTNET=true  # Set to false for live trading
   
   # Security Settings
   ENCRYPTION_KEY=your_32_character_encryption_key_here
   ```

3. **Verify `.env` is in `.gitignore`**:
   ```gitignore
   # Environment files
   .env
   .env.local
   .env.*.local
   ```

### Encryption (Recommended)

For additional security, encrypt your API keys:

```python
from utils.encryption import encrypt_api_key, decrypt_api_key

# Encrypt your keys before storing
encrypted_key = encrypt_api_key("your_api_key")
encrypted_secret = encrypt_api_key("your_secret_key")
```

## Configuration

### Backend Configuration

1. **Update `config/config.py`**:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class Config:
       # Binance Configuration
       BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
       BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
       BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
       
       # Validate required settings
       if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
           raise ValueError("Binance API credentials not found in environment variables")
   ```

2. **Test Configuration Loading**:
   ```python
   # Run this to verify your config
   python -c "from config.config import Config; print('✅ Config loaded successfully')"
   ```

### Frontend Configuration

1. **Update API endpoints** in `frontend/src/services/api.js`:
   ```javascript
   const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
   
   export const tradingAPI = {
     // Test API connection
     testConnection: () => axios.get(`${API_BASE_URL}/api/test-connection`),
     
     // Get account info
     getAccountInfo: () => axios.get(`${API_BASE_URL}/api/account`),
   };
   ```

## Testing Your Connection

### Step 1: Basic Connection Test

```python
# Create test_connection.py
import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

def test_binance_connection():
    try:
        # Initialize client
        client = Client(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_SECRET_KEY'),
            testnet=True  # Use testnet for testing
        )
        
        # Test connection
        account_info = client.get_account()
        print("✅ Connection successful!")
        print(f"Account Type: {account_info['accountType']}")
        print(f"Can Trade: {account_info['canTrade']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_binance_connection()
```

### Step 2: Run the Test

```bash
# Navigate to backend directory
cd backend

# Run the connection test
python test_connection.py
```

### Step 3: Expected Output

```
✅ Connection successful!
Account Type: SPOT
Can Trade: True
```

### Step 4: Test Through Web Interface

1. **Start your backend**:
   ```bash
   python app.py
   ```

2. **Start your frontend**:
   ```bash
   cd ../frontend
   npm start
   ```

3. **Test in browser**:
   - Go to `http://localhost:3000`
   - Navigate to Settings → API Keys
   - Click "Test Connection"
   - Should show green checkmark if successful

## Common Issues & Troubleshooting

### Issue 1: "Invalid API Key"

**Symptoms**:
```
BinanceAPIException: Invalid API-key, IP, or permissions for action
```

**Solutions**:
1. ✅ Verify API key is correct (no extra spaces)
2. ✅ Check IP restrictions in Binance
3. ✅ Ensure API permissions are enabled
4. ✅ Try regenerating API keys

### Issue 2: "Timestamp Error"

**Symptoms**:
```
BinanceAPIException: Timestamp for this request is outside of the recvWindow
```

**Solutions**:
1. ✅ Sync your system clock
2. ✅ Add timestamp offset in client:
   ```python
   client = Client(
       api_key=api_key,
       api_secret=secret_key,
       timestamp_offset=1000  # Add 1 second offset
   )
   ```

### Issue 3: "Rate Limit Exceeded"

**Symptoms**:
```
BinanceAPIException: Too many requests
```

**Solutions**:
1. ✅ Implement rate limiting in your bot
2. ✅ Add delays between requests
3. ✅ Use WebSocket for real-time data instead of REST API

### Issue 4: "Insufficient Balance"

**Symptoms**:
```
BinanceAPIException: Account has insufficient balance
```

**Solutions**:
1. ✅ Check account balance
2. ✅ Verify you're using the correct trading pair
3. ✅ Ensure you have enough funds for fees

## Other Exchanges

### Coinbase Pro

```python
# Environment variables
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret
COINBASE_PASSPHRASE=your_coinbase_passphrase
```

### Kraken

```python
# Environment variables
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_SECRET_KEY=your_kraken_secret
```

### Bitfinex

```python
# Environment variables
BITFINEX_API_KEY=your_bitfinex_api_key
BITFINEX_SECRET_KEY=your_bitfinex_secret
```

## Best Practices

### Security

1. **Never hardcode API keys** in your source code
2. **Use environment variables** for all sensitive data
3. **Enable IP restrictions** on your API keys
4. **Disable withdrawal permissions** for trading bots
5. **Regularly rotate your API keys** (monthly recommended)
6. **Monitor API usage** for unusual activity

### Performance

1. **Use WebSocket connections** for real-time data
2. **Implement proper rate limiting** to avoid bans
3. **Cache frequently accessed data** when possible
4. **Use connection pooling** for multiple requests

### Monitoring

1. **Log all API calls** for debugging
2. **Set up alerts** for API failures
3. **Monitor rate limit usage**
4. **Track API response times**

### Testing

1. **Always test on testnet first**
2. **Start with small amounts** in production
3. **Implement comprehensive error handling**
4. **Test all failure scenarios**

## Quick Start Checklist

- [ ] Created exchange account and completed KYC
- [ ] Generated API keys with appropriate permissions
- [ ] Set up IP restrictions
- [ ] Created `.env` file with credentials
- [ ] Tested connection with test script
- [ ] Verified web interface connectivity
- [ ] Implemented proper error handling
- [ ] Set up monitoring and logging
- [ ] Tested with small amounts first

## Support

If you encounter issues:

1. **Check the logs** in `backend/logs/`
2. **Review this troubleshooting guide**
3. **Test your API keys** with the exchange's official tools
4. **Check exchange status** pages for outages
5. **Consult exchange documentation** for API changes

---

⚠️ **Risk Disclaimer**: Trading cryptocurrencies involves substantial risk of loss. Never trade with funds you cannot afford to lose. Always test thoroughly before deploying to production.

📧 **Need Help?** Check our [Troubleshooting Guide](TROUBLESHOOTING.md) or create an issue in the repository.