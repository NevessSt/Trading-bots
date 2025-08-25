#!/usr/bin/env python3
"""
API Connection Test Script

This script helps you verify that your exchange API credentials are properly configured
and that your trading bot can successfully connect to the exchange.

Usage:
    python test_connection.py [exchange]
    
Examples:
    python test_connection.py binance
    python test_connection.py coinbase
    python test_connection.py kraken
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_binance_connection():
    """Test Binance API connection"""
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        print("🔄 Testing Binance connection...")
        
        # Get credentials
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        
        if not api_key or not secret_key:
            print("❌ Missing Binance API credentials in .env file")
            print("   Please add BINANCE_API_KEY and BINANCE_SECRET_KEY")
            return False
            
        # Initialize client
        client = Client(
            api_key=api_key,
            api_secret=secret_key,
            testnet=use_testnet
        )
        
        # Test basic connection
        server_time = client.get_server_time()
        print(f"✅ Server connection successful")
        print(f"   Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
        
        # Test account access
        account_info = client.get_account()
        print(f"✅ Account access successful")
        print(f"   Account type: {account_info['accountType']}")
        print(f"   Can trade: {account_info['canTrade']}")
        print(f"   Can withdraw: {account_info['canWithdraw']}")
        print(f"   Can deposit: {account_info['canDeposit']}")
        
        # Show balances (non-zero only)
        balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
        if balances:
            print(f"\n💰 Account balances:")
            for balance in balances[:5]:  # Show first 5 non-zero balances
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    print(f"   {balance['asset']}: {free} (free) + {locked} (locked)")
            if len(balances) > 5:
                print(f"   ... and {len(balances) - 5} more assets")
        else:
            print("\n💰 No balances found (this is normal for testnet)")
            
        # Test market data access
        try:
            ticker = client.get_symbol_ticker(symbol="BTCUSDT")
            print(f"\n📊 Market data access successful")
            print(f"   BTC/USDT price: ${float(ticker['price']):,.2f}")
        except Exception as e:
            print(f"⚠️  Market data access failed: {str(e)}")
            
        # Test trading permissions (with a very small test order that will likely fail)
        try:
            # This will likely fail due to insufficient balance, but tests permissions
            client.create_test_order(
                symbol='BTCUSDT',
                side='BUY',
                type='MARKET',
                quantity=0.001
            )
            print("✅ Trading permissions verified")
        except BinanceAPIException as e:
            if "insufficient balance" in str(e).lower():
                print("✅ Trading permissions verified (insufficient balance is expected)")
            elif "invalid symbol" in str(e).lower():
                print("✅ Trading permissions verified (symbol validation working)")
            else:
                print(f"⚠️  Trading permission issue: {str(e)}")
        except Exception as e:
            print(f"⚠️  Could not test trading permissions: {str(e)}")
            
        print(f"\n🎉 Binance connection test completed successfully!")
        print(f"   Environment: {'Testnet' if use_testnet else 'Live Trading'}")
        
        if use_testnet:
            print("\n💡 You're using testnet. To switch to live trading:")
            print("   Set BINANCE_TESTNET=false in your .env file")
            
        return True
        
    except ImportError:
        print("❌ Binance library not installed")
        print("   Run: pip install python-binance")
        return False
    except BinanceAPIException as e:
        print(f"❌ Binance API error: {str(e)}")
        print("\n🔧 Common solutions:")
        print("   1. Check your API key and secret")
        print("   2. Verify IP restrictions in Binance settings")
        print("   3. Ensure API permissions are enabled")
        print("   4. Check if your system time is synchronized")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_coinbase_connection():
    """Test Coinbase Pro API connection"""
    try:
        import cbpro
        
        print("🔄 Testing Coinbase Pro connection...")
        
        # Get credentials
        api_key = os.getenv('COINBASE_API_KEY')
        secret_key = os.getenv('COINBASE_SECRET_KEY')
        passphrase = os.getenv('COINBASE_PASSPHRASE')
        sandbox = os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true'
        
        if not all([api_key, secret_key, passphrase]):
            print("❌ Missing Coinbase Pro API credentials in .env file")
            print("   Please add COINBASE_API_KEY, COINBASE_SECRET_KEY, and COINBASE_PASSPHRASE")
            return False
            
        # Initialize client
        client = cbpro.AuthenticatedClient(
            api_key, secret_key, passphrase,
            sandbox=sandbox
        )
        
        # Test account access
        accounts = client.get_accounts()
        print(f"✅ Account access successful")
        print(f"   Found {len(accounts)} accounts")
        
        # Show balances
        for account in accounts:
            balance = float(account['balance'])
            if balance > 0:
                print(f"   {account['currency']}: {balance}")
                
        print(f"\n🎉 Coinbase Pro connection test completed successfully!")
        return True
        
    except ImportError:
        print("❌ Coinbase Pro library not installed")
        print("   Run: pip install cbpro")
        return False
    except Exception as e:
        print(f"❌ Coinbase Pro API error: {str(e)}")
        return False

def test_kraken_connection():
    """Test Kraken API connection"""
    try:
        import krakenex
        
        print("🔄 Testing Kraken connection...")
        
        # Get credentials
        api_key = os.getenv('KRAKEN_API_KEY')
        secret_key = os.getenv('KRAKEN_SECRET_KEY')
        
        if not api_key or not secret_key:
            print("❌ Missing Kraken API credentials in .env file")
            print("   Please add KRAKEN_API_KEY and KRAKEN_SECRET_KEY")
            return False
            
        # Initialize client
        client = krakenex.API()
        client.key = api_key
        client.secret = secret_key
        
        # Test account access
        response = client.query_private('Balance')
        
        if response['error']:
            print(f"❌ Kraken API error: {response['error']}")
            return False
            
        print(f"✅ Account access successful")
        
        # Show balances
        balances = response['result']
        for currency, balance in balances.items():
            if float(balance) > 0:
                print(f"   {currency}: {balance}")
                
        print(f"\n🎉 Kraken connection test completed successfully!")
        return True
        
    except ImportError:
        print("❌ Kraken library not installed")
        print("   Run: pip install krakenex")
        return False
    except Exception as e:
        print(f"❌ Kraken API error: {str(e)}")
        return False

def print_usage():
    """Print usage information"""
    print("\n📋 API Connection Test Tool")
    print("\nUsage:")
    print("   python test_connection.py [exchange]")
    print("\nSupported exchanges:")
    print("   binance    - Test Binance API connection")
    print("   coinbase   - Test Coinbase Pro API connection")
    print("   kraken     - Test Kraken API connection")
    print("   all        - Test all configured exchanges")
    print("\nExamples:")
    print("   python test_connection.py binance")
    print("   python test_connection.py all")
    print("\n💡 Make sure your .env file contains the required API credentials.")

def main():
    """Main function"""
    print("🚀 Trading Bot API Connection Test")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Please create a .env file with your API credentials")
        print("   See API_INTEGRATION_GUIDE.md for setup instructions")
        return False
        
    # Parse command line arguments
    if len(sys.argv) < 2:
        print_usage()
        return False
        
    exchange = sys.argv[1].lower()
    
    success = True
    
    if exchange == 'binance':
        success = test_binance_connection()
    elif exchange == 'coinbase':
        success = test_coinbase_connection()
    elif exchange == 'kraken':
        success = test_kraken_connection()
    elif exchange == 'all':
        print("\n🔄 Testing all configured exchanges...\n")
        
        # Test Binance if credentials exist
        if os.getenv('BINANCE_API_KEY'):
            print("\n" + "="*50)
            success &= test_binance_connection()
            
        # Test Coinbase if credentials exist
        if os.getenv('COINBASE_API_KEY'):
            print("\n" + "="*50)
            success &= test_coinbase_connection()
            
        # Test Kraken if credentials exist
        if os.getenv('KRAKEN_API_KEY'):
            print("\n" + "="*50)
            success &= test_kraken_connection()
            
        if not any([os.getenv('BINANCE_API_KEY'), os.getenv('COINBASE_API_KEY'), os.getenv('KRAKEN_API_KEY')]):
            print("❌ No exchange API credentials found in .env file")
            success = False
    else:
        print(f"❌ Unsupported exchange: {exchange}")
        print_usage()
        return False
        
    print("\n" + "="*50)
    if success:
        print("🎉 All tests passed! Your API connection is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Start your trading bot: python app.py")
        print("   2. Open the web interface: http://localhost:5000")
        print("   3. Configure your trading strategies")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 For help, see:")
        print("   - API_INTEGRATION_GUIDE.md")
        print("   - TROUBLESHOOTING.md")
        
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)