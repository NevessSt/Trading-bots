from models.user import User
from db import db
from app import app

app.app_context().push()

print("Testing User.authenticate method...")

# Test authentication
user = User.authenticate('danielmanji38@gmail.com', 'newpassword123')
if user:
    print(f"Authentication successful! User: {user.username} ({user.email})")
    print(f"User ID: {user.id}")
    print(f"Is active: {user.is_active}")
    print(f"Is verified: {user.is_verified}")
else:
    print("Authentication failed!")
    
    # Let's check if the user exists
    user_check = User.query.filter_by(email='danielmanji38@gmail.com').first()
    if user_check:
        print(f"User exists: {user_check.username}")
        print(f"Is active: {user_check.is_active}")
        print(f"Is locked: {user_check.is_locked()}")
        print(f"Password check: {user_check.check_password('newpassword123')}")
    else:
        print("User not found in database!")