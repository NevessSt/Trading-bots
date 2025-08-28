#!/usr/bin/env python3
"""
Buyer-Specific Build Script for TradingBot Pro
Handles different buyer tiers and deployment options.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from build_config import TradingBotBuilder

class BuyerDeploymentManager:
    """Manages buyer-specific deployments and configurations"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.builder = TradingBotBuilder(str(self.project_root))
        self.buyer_configs_dir = self.project_root / "buyer_configs"
        self.buyer_configs_dir.mkdir(exist_ok=True)
        
        # Buyer tier configurations
        self.buyer_tiers = {
            'starter': {
                'price': 299,
                'build_config': 'basic',
                'features': [
                    'Basic trading strategies',
                    'Risk management',
                    'Web dashboard',
                    'Email support'
                ],
                'limitations': {
                    'max_exchanges': 2,
                    'max_strategies': 3,
                    'support_level': 'email'
                },
                'delivery': 'executable_only'
            },
            'professional': {
                'price': 799,
                'build_config': 'standard',
                'features': [
                    'All starter features',
                    'Advanced strategies',
                    'Portfolio management',
                    'API access',
                    'Priority support'
                ],
                'limitations': {
                    'max_exchanges': 5,
                    'max_strategies': 10,
                    'support_level': 'priority'
                },
                'delivery': 'executable_plus_configs'
            },
            'enterprise': {
                'price': 2499,
                'build_config': 'premium',
                'features': [
                    'All professional features',
                    'Full source code',
                    'Custom integrations',
                    'White-label options',
                    'Dedicated support'
                ],
                'limitations': {
                    'max_exchanges': 'unlimited',
                    'max_strategies': 'unlimited',
                    'support_level': 'dedicated'
                },
                'delivery': 'full_source_code'
            },
            'institutional': {
                'price': 9999,
                'build_config': 'enterprise',
                'features': [
                    'All enterprise features',
                    'Multi-tenant support',
                    'Custom development',
                    'On-site training',
                    '24/7 support'
                ],
                'limitations': {
                    'max_exchanges': 'unlimited',
                    'max_strategies': 'unlimited',
                    'support_level': '24/7'
                },
                'delivery': 'full_source_plus_services'
            }
        }
    
    def create_buyer_license(self, buyer_info: Dict) -> str:
        """Create buyer-specific license configuration"""
        license_config = {
            'buyer_id': buyer_info['id'],
            'buyer_name': buyer_info['name'],
            'buyer_email': buyer_info['email'],
            'tier': buyer_info['tier'],
            'purchase_date': datetime.now().isoformat(),
            'license_key': self._generate_license_key(buyer_info),
            'features': self.buyer_tiers[buyer_info['tier']]['features'],
            'limitations': self.buyer_tiers[buyer_info['tier']]['limitations'],
            'support_level': self.buyer_tiers[buyer_info['tier']]['limitations']['support_level']
        }
        
        # Save license config
        license_file = self.buyer_configs_dir / f"license_{buyer_info['id']}.json"
        with open(license_file, 'w') as f:
            json.dump(license_config, f, indent=2)
        
        return str(license_file)
    
    def _generate_license_key(self, buyer_info: Dict) -> str:
        """Generate unique license key for buyer"""
        import hashlib
        import secrets
        
        # Create unique identifier
        unique_data = f"{buyer_info['id']}{buyer_info['email']}{datetime.now().isoformat()}"
        hash_obj = hashlib.sha256(unique_data.encode())
        
        # Add random component
        random_component = secrets.token_hex(8)
        
        # Format as license key
        license_key = f"TB-{hash_obj.hexdigest()[:8].upper()}-{random_component.upper()}"
        return license_key
    
    def create_buyer_env_file(self, buyer_info: Dict, output_dir: Path) -> str:
        """Create buyer-specific .env file"""
        tier_config = self.buyer_tiers[buyer_info['tier']]
        
        env_content = f'''# TradingBot Pro Configuration - {buyer_info['tier'].title()} Tier
# Generated for: {buyer_info['name']} ({buyer_info['email']})
# Purchase Date: {datetime.now().strftime('%Y-%m-%d')}

# License Configuration
LICENSE_KEY={buyer_info.get('license_key', 'REPLACE_WITH_YOUR_LICENSE_KEY')}
LICENSE_TIER={buyer_info['tier']}
BUYER_ID={buyer_info['id']}

# Server Configuration
FLASK_ENV=production
SECRET_KEY=REPLACE_WITH_SECURE_SECRET_KEY
HOST=127.0.0.1
PORT=5000
DEBUG=false

# Database Configuration
DATABASE_URL=sqlite:///tradingbot.db
REDIS_URL=redis://localhost:6379/0

# Exchange API Keys (REQUIRED)
# Binance
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=true

# Coinbase Pro
COINBASE_API_KEY=your_coinbase_api_key_here
COINBASE_SECRET_KEY=your_coinbase_secret_key_here
COINBASE_PASSPHRASE=your_coinbase_passphrase_here
COINBASE_SANDBOX=true

# Risk Management
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=500
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=5.0

# Trading Configuration
DEFAULT_STRATEGY=conservative
TRADING_ENABLED=false
PAPER_TRADING=true

# Tier-Specific Limitations
MAX_EXCHANGES={tier_config['limitations']['max_exchanges']}
MAX_STRATEGIES={tier_config['limitations']['max_strategies']}

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_ENABLED=false

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/tradingbot.log

# License Server (for revocation checks)
LICENSE_SERVER_URL=https://license.tradingbot-pro.com
ENABLE_REMOTE_LICENSE_CHECK=true
LICENSE_CACHE_TIMEOUT=3600
'''
        
        env_file = output_dir / '.env'
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        return str(env_file)
    
    def create_buyer_guide(self, buyer_info: Dict, output_dir: Path) -> str:
        """Create buyer-specific setup guide"""
        tier_config = self.buyer_tiers[buyer_info['tier']]
        
        guide_content = f'''# TradingBot Pro - {buyer_info['tier'].title()} Tier Setup Guide

**Buyer:** {buyer_info['name']}  
**Email:** {buyer_info['email']}  
**Purchase Date:** {datetime.now().strftime('%Y-%m-%d')}  
**License Key:** `{buyer_info.get('license_key', 'See license_info.json')}`

## What You Received

### Features Included:
{chr(10).join([f"- {feature}" for feature in tier_config['features']])}

### Tier Limitations:
- **Max Exchanges:** {tier_config['limitations']['max_exchanges']}
- **Max Strategies:** {tier_config['limitations']['max_strategies']}
- **Support Level:** {tier_config['limitations']['support_level']}

## Quick Start Guide

### 1. Initial Setup

1. **Extract the package** to your desired directory
2. **Copy `.env.example` to `.env`**
3. **Edit `.env`** with your configuration:
   - Add your exchange API keys
   - Set your risk management parameters
   - Configure email notifications

### 2. Exchange API Setup

#### Binance Setup:
1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create new API key with trading permissions
3. Add your IP address to whitelist
4. Copy API key and secret to `.env` file

#### Coinbase Pro Setup:
1. Go to [Coinbase Pro API](https://pro.coinbase.com/profile/api)
2. Create new API key with trading permissions
3. Copy API key, secret, and passphrase to `.env` file

### 3. Running the Bot

''')
        
        if tier_config['delivery'] == 'executable_only':
            guide_content += '''#### Executable Version:
```bash
# Windows
.\\TradingBot-{}.exe

# Linux/Mac
./TradingBot-{}
```

'''.format(buyer_info['tier'].title(), buyer_info['tier'].title())
        
        if 'source' in tier_config['delivery']:
            guide_content += '''#### Source Code Version:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python backend/app.py
```

'''
        
        guide_content += f'''### 4. Accessing the Dashboard

Once running, open your browser and go to:
- **Local:** http://localhost:5000
- **Network:** http://YOUR_IP:5000

Default login credentials will be displayed in the console on first run.

### 5. Safety First

⚠️ **IMPORTANT SAFETY NOTES:**

1. **Start with Paper Trading:** Set `PAPER_TRADING=true` in your `.env` file
2. **Use Testnet:** Set `BINANCE_TESTNET=true` and `COINBASE_SANDBOX=true`
3. **Set Conservative Limits:** Start with small `MAX_POSITION_SIZE` and `MAX_DAILY_LOSS`
4. **Monitor Closely:** Watch your first trades carefully
5. **Read Documentation:** Review all strategy documentation before use

## Support Information

### Your Support Level: {tier_config['limitations']['support_level'].title()}

- **Email Support:** support@tradingbot-pro.com
- **Response Time:** {'24 hours' if tier_config['limitations']['support_level'] == 'email' else '4 hours' if tier_config['limitations']['support_level'] == 'priority' else '1 hour'}
- **Documentation:** See SUPPORT.md for detailed support information

### Getting Help

1. **Check Documentation:** Review README.md and strategy guides
2. **Common Issues:** See SUPPORT.md for troubleshooting
3. **Contact Support:** Email with your license key and detailed description

## License Information

- **License Key:** `{buyer_info.get('license_key', 'See license_info.json')}`
- **Tier:** {buyer_info['tier'].title()}
- **Valid Until:** Lifetime (no expiration)
- **Revocation:** License can be revoked for terms violations

## Legal Compliance

⚠️ **Please read carefully:**

- **EULA.md** - End User License Agreement
- **DISCLAIMER.md** - Trading risk disclaimers
- **REFUND_POLICY.md** - Refund terms and conditions

By using this software, you agree to all terms and conditions.

## Upgrade Options

Interested in upgrading your tier? Contact sales@tradingbot-pro.com

---

**Need Help?** Contact support@tradingbot-pro.com with your license key: `{buyer_info.get('license_key', 'N/A')}`
'''
        
        guide_file = output_dir / 'BUYER_SETUP_GUIDE.md'
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        return str(guide_file)
    
    def create_deployment_package_for_buyer(self, buyer_info: Dict) -> Optional[str]:
        """Create complete deployment package for specific buyer"""
        tier_config = self.buyer_tiers[buyer_info['tier']]
        build_config = tier_config['build_config']
        
        print(f"Creating deployment package for {buyer_info['name']} ({buyer_info['tier']} tier)")
        
        # Create license
        license_file = self.create_buyer_license(buyer_info)
        with open(license_file, 'r') as f:
            license_data = json.load(f)
        buyer_info['license_key'] = license_data['license_key']
        
        # Build the executable
        success = self.builder.build_single_config(build_config)
        if not success:
            print(f"❌ Failed to build {build_config} configuration")
            return None
        
        # Create buyer-specific package
        package_name = f"TradingBot-Pro-{buyer_info['tier'].title()}-{buyer_info['id']}-{datetime.now().strftime('%Y%m%d')}"
        package_dir = self.builder.dist_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy built executable
        exe_name = self.builder.build_configs[build_config]['name']
        exe_path = self.builder.dist_dir / exe_name
        if exe_path.exists():
            if exe_path.is_dir():
                shutil.copytree(exe_path, package_dir / exe_name)
            else:
                shutil.copy2(exe_path, package_dir)
        
        # Create buyer-specific files
        self.create_buyer_env_file(buyer_info, package_dir)
        self.create_buyer_guide(buyer_info, package_dir)
        
        # Copy license info
        shutil.copy2(license_file, package_dir / 'license_info.json')
        
        # Copy standard documentation
        docs_to_copy = [
            'README.md',
            'SUPPORT.md',
            'EULA.md',
            'DISCLAIMER.md',
            'REFUND_POLICY.md'
        ]
        
        for doc in docs_to_copy:
            doc_path = self.project_root / doc
            if doc_path.exists():
                shutil.copy2(doc_path, package_dir)
        
        # Copy source code if included in tier
        if 'source' in tier_config['delivery']:
            source_dirs = ['backend', 'frontend', 'tools', 'strategies']
            source_package_dir = package_dir / 'source'
            source_package_dir.mkdir(exist_ok=True)
            
            for source_dir in source_dirs:
                src_path = self.project_root / source_dir
                if src_path.exists():
                    dst_path = source_package_dir / source_dir
                    shutil.copytree(src_path, dst_path, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            
            # Copy requirements.txt
            req_path = self.project_root / 'requirements.txt'
            if req_path.exists():
                shutil.copy2(req_path, source_package_dir)
        
        # Create ZIP package
        import zipfile
        zip_path = self.builder.dist_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(package_dir)
                    zipf.write(file_path, arc_path)
        
        print(f"✅ Buyer package created: {zip_path}")
        return str(zip_path)
    
    def list_buyer_tiers(self):
        """Display available buyer tiers"""
        print("\nAvailable Buyer Tiers:")
        print("=" * 50)
        
        for tier_name, config in self.buyer_tiers.items():
            print(f"\n{tier_name.upper()} - ${config['price']}")
            print("-" * 30)
            print("Features:")
            for feature in config['features']:
                print(f"  • {feature}")
            print(f"\nDelivery: {config['delivery'].replace('_', ' ').title()}")
            print(f"Max Exchanges: {config['limitations']['max_exchanges']}")
            print(f"Max Strategies: {config['limitations']['max_strategies']}")
            print(f"Support Level: {config['limitations']['support_level'].title()}")

def main():
    parser = argparse.ArgumentParser(description='TradingBot Pro Buyer Deployment Manager')
    parser.add_argument('--list-tiers', action='store_true', help='List available buyer tiers')
    parser.add_argument('--buyer-id', help='Buyer ID')
    parser.add_argument('--buyer-name', help='Buyer name')
    parser.add_argument('--buyer-email', help='Buyer email')
    parser.add_argument('--tier', choices=['starter', 'professional', 'enterprise', 'institutional'],
                       help='Buyer tier')
    parser.add_argument('--create-package', action='store_true', help='Create deployment package')
    
    args = parser.parse_args()
    
    manager = BuyerDeploymentManager()
    
    if args.list_tiers:
        manager.list_buyer_tiers()
        return
    
    if args.create_package:
        if not all([args.buyer_id, args.buyer_name, args.buyer_email, args.tier]):
            print("❌ Missing required buyer information for package creation")
            print("Required: --buyer-id, --buyer-name, --buyer-email, --tier")
            return
        
        buyer_info = {
            'id': args.buyer_id,
            'name': args.buyer_name,
            'email': args.buyer_email,
            'tier': args.tier
        }
        
        package_path = manager.create_deployment_package_for_buyer(buyer_info)
        if package_path:
            print(f"\n✅ Deployment package ready: {package_path}")
        else:
            print("\n❌ Failed to create deployment package")
    else:
        print("Use --list-tiers to see available tiers or --create-package to build for a buyer")

if __name__ == '__main__':
    main()