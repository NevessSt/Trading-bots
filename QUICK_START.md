# 🚀 Quick Start Guide

> **Get your trading bot running in under 10 minutes!**

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Docker Desktop** installed and running
- [ ] **Git** for cloning the repository
- [ ] **Valid License Key** (provided after purchase)
- [ ] **Exchange Account** (Binance, Coinbase Pro, etc.)
- [ ] **API Keys** from your exchange (testnet recommended for first setup)

---

## ⚡ 5-Minute Setup

### Step 1: Clone & Configure

```bash
# Clone the repository
git clone <your-repository-url>
cd trading-bot

# Copy environment template
cp .env.example .env
```

### Step 2: Edit Configuration

Open `.env` file and update these essential settings:

```env
# 🔐 Security (CHANGE THESE!)
JWT_SECRET_KEY=your-unique-secret-key-min-32-characters
ENCRYPTION_KEY=your-32-byte-base64-encryption-key

# 📈 Trading (Safe defaults)
DEFAULT_TESTNET=true
MAX_POSITION_SIZE=100
RISK_LIMIT=0.01

# 🗄️ Database (Default works for Docker)
DATABASE_URL=postgresql://trading_user:trading_pass@db:5432/trading_bot
REDIS_URL=redis://redis:6379/0
```

### Step 3: Launch Everything

```bash
# Start all services with Docker
docker-compose up -d

# Wait 30 seconds for services to initialize
# Check status
docker-compose ps
```

### Step 4: Access Your Bot

Open your browser and navigate to:

- **🎯 Trading Dashboard**: http://localhost:3000
- **📊 Monitoring**: http://localhost:3001 (Grafana)
- **🔧 API Docs**: http://localhost:5000/docs

---

## 🎯 First-Time Setup

### 1. Create Your Account

1. Go to http://localhost:3000
2. Click **"Sign Up"**
3. Fill in your details:
   - Email address
   - Strong password
   - Confirm password
4. Click **"Create Account"**
5. You'll be automatically logged in

### 2. Activate Your License

1. Navigate to **Settings → License**
2. Enter your license key
3. Click **"Activate License"**
4. Verify activation status shows **"ACTIVE"**

> 💡 **Don't have a license?** The system will run in demo mode with limited features.

### 3. Add Your First API Key

1. Go to **Settings → API Keys**
2. Click **"Add API Key"**
3. Configure your exchange:

   **For Binance (Recommended for beginners):**
   ```
   Key Name: "My Binance Testnet"
   Exchange: "Binance"
   API Key: [Your Binance testnet API key]
   API Secret: [Your Binance testnet secret]
   Testnet: ✅ Enabled
   Permissions: ✅ Read, ✅ Trade
   ```

4. Click **"Test Connection"** to verify
5. Click **"Save API Key"**

### 4. Create Your First Strategy

1. Navigate to **Strategies → Create New**
2. Choose **"DCA (Dollar Cost Averaging)"**
3. Configure basic settings:
   ```
   Strategy Name: "My First DCA"
   Trading Pair: "BTCUSDT"
   Investment Amount: $10
   Frequency: "Every 1 hour"
   Conditions: "When RSI < 40"
   ```
4. Click **"Backtest Strategy"** to see historical performance
5. If satisfied, click **"Deploy to Testnet"**

---

## 🛡️ Security Best Practices

### Essential Security Steps

1. **🔐 Change Default Secrets**
   ```bash
   # Generate secure JWT secret (32+ characters)
   openssl rand -base64 32
   
   # Generate encryption key
   openssl rand -base64 32
   ```

2. **🔑 API Key Security**
   - ✅ Use testnet keys initially
   - ✅ Restrict API keys to your IP
   - ✅ Enable only required permissions
   - ❌ Never enable withdrawal permissions
   - ❌ Never share your API keys

3. **🌐 Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Regular security updates

---

## 📊 Getting Exchange API Keys

### Binance (Easiest Setup)

1. **Testnet** (Recommended first):
   - Visit: https://testnet.binance.vision/
   - Register with email
   - Go to API Management
   - Create API key with "Spot Trading" enabled

2. **Live Trading** (After testing):
   - Visit: https://www.binance.com/en/my/settings/api-management
   - Create API key
   - Enable: "Enable Reading" + "Enable Spot & Margin Trading"
   - Restrict to your server IP

### Coinbase Pro

1. Visit: https://pro.coinbase.com/profile/api
2. Create new API key
3. Permissions: "View" + "Trade" (NOT "Transfer")
4. **Important**: Save the passphrase!

### Other Exchanges

- **Kraken**: https://www.kraken.com/u/security/api
- **Bitfinex**: https://setting.bitfinex.com/api
- **OKX**: https://www.okx.com/account/my-api

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### "Docker containers won't start"
```bash
# Check Docker is running
docker --version

# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

#### "Can't access the dashboard"
```bash
# Check if services are running
docker-compose ps

# Check port conflicts
netstat -tulpn | grep :3000

# Try different port
# Edit docker-compose.yml: "3001:3000"
```

#### "API key test fails"
- ✅ Verify API key and secret are correct
- ✅ Check if testnet is enabled for testnet keys
- ✅ Ensure API key has trading permissions
- ✅ Check if IP restriction is set correctly

#### "License activation fails"
- ✅ Verify license key is entered correctly
- ✅ Check internet connection
- ✅ Contact support if key is valid but fails

### Getting Help

1. **📖 Check logs**: `docker-compose logs [service-name]`
2. **🔍 Search issues**: Check GitHub issues
3. **💬 Community**: Join Discord for help
4. **📧 Support**: Email support for license issues

---

## 🎯 Next Steps

Once your bot is running:

### Immediate Actions
1. **📊 Monitor Performance**: Check dashboard regularly
2. **🔔 Set Alerts**: Configure notifications
3. **📈 Analyze Results**: Review strategy performance
4. **🔄 Optimize**: Adjust parameters based on results

### Advanced Features
1. **📊 Custom Strategies**: Build advanced trading logic
2. **🤖 Multiple Bots**: Run different strategies simultaneously
3. **📈 Portfolio Management**: Advanced risk management
4. **🔗 API Integration**: Connect external tools

### Production Deployment
1. **🌐 Domain Setup**: Configure custom domain
2. **🔒 SSL Certificate**: Enable HTTPS
3. **📊 Monitoring**: Set up advanced monitoring
4. **💾 Backups**: Configure automated backups

---

## 📞 Support Contacts

- **🐛 Bug Reports**: GitHub Issues
- **💬 Community**: Discord Server
- **📧 License Support**: support@tradingbot.com
- **📖 Documentation**: Full docs in README.md

---

## ⚠️ Important Reminders

> **🚨 Always start with testnet trading!**
> 
> **💰 Never invest more than you can afford to lose**
> 
> **🔐 Keep your API keys secure and never share them**
> 
> **📊 Monitor your bot's performance regularly**
> 
> **🔄 Start with small amounts and scale gradually**

---

*Happy Trading! 🚀*

*Need help? We're here to support you every step of the way.*