#!/usr/bin/env python3

print("Starting minimal test...")

try:
    print("Testing Flask import...")
    from flask import Flask
    print("✓ Flask imported successfully")
    
    print("Testing database import...")
    from db import db
    print("✓ Database imported successfully")
    
    print("Testing JWT import...")
    from flask_jwt_extended import JWTManager
    print("✓ JWT imported successfully")
    
    print("Testing auth routes import...")
    from api.auth_routes import auth_bp
    print("✓ Auth routes imported successfully")
    
    print("Testing trading routes import...")
    from api.trading_routes import trading_bp
    print("✓ Trading routes imported successfully")
    
    print("Testing models import...")
    from models import User, Bot, Trade
    print("✓ Models imported successfully")
    
    print("Creating minimal Flask app...")
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    db.init_app(app)
    jwt = JWTManager(app)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(trading_bp, url_prefix='/api')
    
    print("✓ App created and blueprints registered successfully")
    
    with app.app_context():
        print("Testing app context...")
        print(f"App name: {app.name}")
        print(f"Registered blueprints: {list(app.blueprints.keys())}")
        
        # Test route registration
        print("Registered routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.rule} -> {rule.endpoint}")
    
    print("\n✅ All tests passed! No import issues detected.")
    
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    import traceback
    traceback.print_exc()