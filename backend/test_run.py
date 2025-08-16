#!/usr/bin/env python3

print("Starting test script...")

try:
    import sys
    print(f"Python version: {sys.version}")
    
    import os
    print(f"Current directory: {os.getcwd()}")
    
    # Test basic imports
    from flask import Flask
    print("Flask import successful")
    
    from dotenv import load_dotenv
    print("dotenv import successful")
    
    # Test database import
    from db import db
    print("Database import successful")
    
    # Test models import
    from models import User, Subscription, Trade, Bot, APIKey
    print("Models import successful")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()

print("Test script completed.")