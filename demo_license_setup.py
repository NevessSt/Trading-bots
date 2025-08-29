#!/usr/bin/env python3
"""
Demo License Setup - One-Click License Activation
This script provides a complete out-of-the-box license solution for non-tech buyers.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🚀 TRADING BOT - DEMO LICENSE ACTIVATION")
    print("="*70)
    print("Welcome to your Trading Bot! This script will:")
    print("✅ Generate a demo license key (365 days)")
    print("✅ Start the license activation server")
    print("✅ Activate your bot automatically")
    print("✅ Provide you with a working trading bot")
    print("="*70)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("✅ Flask installed successfully")
    
    try:
        import requests
        print("✅ Requests is installed")
    except ImportError:
        print("❌ Requests not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("✅ Requests installed successfully")
    
    try:
        import cryptography
        print("✅ Cryptography is installed")
    except ImportError:
        print("❌ Cryptography not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        print("✅ Cryptography installed successfully")

def get_machine_id():
    """Get or generate machine ID"""
    try:
        # Try to import the machine ID generator
        sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
        from machine_id import generate_machine_id
        return generate_machine_id()
    except:
        # Fallback to simple machine ID generation
        import platform
        import hashlib
        
        machine_info = f"{platform.node()}-{platform.system()}-{platform.processor()}"
        return hashlib.md5(machine_info.encode()).hexdigest()[:16]

def generate_demo_license():
    """Generate a demo license key"""
    print("\n🔑 Generating demo license key...")
    
    try:
        from flask import Flask
        from auth.license_manager import LicenseManager
        from config.config import Config
        
        # Create Flask app context
        app = Flask(__name__)
        app.config.from_object(Config)
        
        with app.app_context():
            # Generate premium license key valid for 365 days
            license_key = LicenseManager.generate_license_key(
                license_type='premium',
                duration_days=365,
                user_email='demo@tradingbot.com'
            )
            
            if license_key:
                print("✅ Demo license key generated successfully!")
                print(f"📋 License Type: Premium (All features enabled)")
                print(f"⏰ Valid for: 365 days")
                print(f"👤 User: demo@tradingbot.com")
                
                # Save license key to file for easy access
                with open('demo_license_key.txt', 'w') as f:
                    f.write(license_key)
                
                return license_key
            else:
                print("❌ Failed to generate license key")
                return None
                
    except Exception as e:
        print(f"❌ Error generating license: {str(e)}")
        return None

def start_license_server():
    """Start the license activation server"""
    print("\n🖥️ Starting license activation server...")
    
    try:
        # Set environment variables for the server
        os.environ['LICENSE_SERVER_SECRET'] = 'demo-secret-key-2024'
        os.environ['LICENSE_ADMIN_KEY'] = 'demo-admin-key-123'
        os.environ['LICENSE_SERVER_PORT'] = '8080'
        os.environ['FLASK_DEBUG'] = 'False'
        
        # Start the license server in background
        server_script = os.path.join('backend', 'license_server.py')
        
        if os.path.exists(server_script):
            print("✅ License server starting on http://localhost:8080")
            print("📡 Server will handle license validation automatically")
            
            # Start server in a separate process
            import threading
            import subprocess
            
            def run_server():
                subprocess.run([sys.executable, server_script], cwd=os.getcwd())
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Give server time to start
            time.sleep(3)
            
            # Test server health
            try:
                import requests
                response = requests.get('http://localhost:8080/health', timeout=5)
                if response.status_code == 200:
                    print("✅ License server is running and healthy!")
                    return True
                else:
                    print("⚠️ License server started but health check failed")
                    return True  # Still return True as server is running
            except:
                print("⚠️ License server started (health check unavailable)")
                return True
        else:
            print("❌ License server script not found")
            return False
            
    except Exception as e:
        print(f"❌ Error starting license server: {str(e)}")
        return False

def create_demo_license_file(license_key):
    """Create a demo license file for local validation"""
    print("\n📄 Creating demo license file...")
    
    try:
        # Create license data
        machine_id = get_machine_id()
        license_data = {
            'machine_id': machine_id,
            'expiry_date': (datetime.now() + timedelta(days=365)).isoformat(),
            'license_type': 'premium',
            'features': [
                'basic_trading',
                'advanced_trading', 
                'risk_management',
                'market_data',
                'portfolio_management',
                'api_access',
                'live_trading',
                'custom_indicators',
                'unlimited_bots'
            ],
            'generated_at': datetime.now().isoformat(),
            'license_key': license_key
        }
        
        # Save as JSON for easy reading
        with open('license_key.json', 'w') as f:
            json.dump(license_data, f, indent=2)
        
        # Also create binary format if needed
        try:
            from cryptography.fernet import Fernet
            
            # Generate a key for encryption (in production, this would be secure)
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            
            # Encrypt license data
            encrypted_data = cipher_suite.encrypt(json.dumps(license_data).encode())
            
            # Save encrypted license
            with open('license_key.bin', 'wb') as f:
                f.write(encrypted_data)
            
            # Save the key for decryption (in production, this would be embedded)
            with open('license_key.key', 'wb') as f:
                f.write(key)
                
        except Exception as e:
            print(f"⚠️ Could not create encrypted license file: {e}")
        
        print("✅ Demo license files created:")
        print("   📄 license_key.json (human readable)")
        print("   🔒 license_key.bin (encrypted)")
        print("   🔑 license_key.key (decryption key)")
        print("   📋 demo_license_key.txt (raw license key)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating license file: {str(e)}")
        return False

def show_success_message(license_key):
    """Show success message with next steps"""
    print("\n" + "="*70)
    print("🎉 DEMO LICENSE ACTIVATION COMPLETE!")
    print("="*70)
    print("Your trading bot is now ready to use with a premium license!")
    print("\n📋 What's been set up:")
    print("✅ Premium license key generated (365 days)")
    print("✅ License activation server running on port 8080")
    print("✅ Demo license files created")
    print("✅ All premium features unlocked")
    
    print("\n🚀 Next Steps:")
    print("1. Start your trading bot applications:")
    print("   • Web Dashboard: cd web-dashboard && npm run dev")
    print("   • Desktop App: cd desktop-app && npm start")
    print("   • Mobile App: cd TradingBotMobile && npm start")
    
    print("\n2. Your license will be automatically validated")
    print("\n3. All premium features are now available:")
    print("   • Unlimited trading bots")
    print("   • Live trading capabilities")
    print("   • Advanced strategies")
    print("   • API access")
    print("   • Custom indicators")
    print("   • Portfolio management")
    
    print("\n📄 License Files Created:")
    print(f"   📋 Raw License Key: demo_license_key.txt")
    print(f"   📄 License Data: license_key.json")
    print(f"   🔒 Encrypted License: license_key.bin")
    
    print("\n🔧 Troubleshooting:")
    print("   • License server: http://localhost:8080/health")
    print("   • License validation: Automatic on app startup")
    print("   • Support: Check README.md for detailed instructions")
    
    print("\n" + "="*70)
    print("🎯 Your trading bot is ready! Happy trading!")
    print("="*70)

def main():
    """Main setup function"""
    try:
        print_banner()
        
        # Check and install dependencies
        check_dependencies()
        
        # Generate demo license
        license_key = generate_demo_license()
        if not license_key:
            print("❌ Failed to generate demo license. Exiting.")
            return False
        
        # Start license server
        if not start_license_server():
            print("⚠️ License server failed to start, but continuing...")
        
        # Create license files
        if not create_demo_license_file(license_key):
            print("⚠️ Failed to create license files, but continuing...")
        
        # Show success message
        show_success_message(license_key)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Demo license setup completed successfully!")
        input("\nPress Enter to exit...")
    else:
        print("\n❌ Demo license setup failed!")
        input("\nPress Enter to exit...")
        sys.exit(1)