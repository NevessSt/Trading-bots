#!/usr/bin/env python3

try:
    print("Testing imports...")
    
    print("Importing config...")
    from config.config import get_config
    print("✓ Config imported successfully")
    
    print("Importing models...")
    from models.user import User
    print("✓ User model imported successfully")
    
    print("Importing bot_engine...")
    from bot_engine import TradingEngine
    print("✓ TradingEngine imported successfully")
    
    print("Importing utils...")
    from utils.logger import logger
    print("✓ Logger imported successfully")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()