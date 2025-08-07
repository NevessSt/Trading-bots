#!/usr/bin/env python3

print("Starting simple test...")

try:
    print("Testing Flask import...")
    from flask import Flask
    print("✓ Flask imported successfully")
    
    print("Creating Flask app...")
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return 'Hello World!'
    
    print("✓ Flask app created successfully")
    print("Starting server on port 5000...")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()