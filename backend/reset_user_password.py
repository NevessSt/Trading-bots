from models.user import User
from db import db
from app import app

app.app_context().push()

user = User.query.filter_by(email='danielmanji38@gmail.com').first()
if user:
    print(f'Found user: {user.username} ({user.email})')
    
    # Reset password to a known value
    new_password = 'newpassword123'
    user.set_password(new_password)  # Use the proper method to hash the password
    
    # Also set the user as verified
    user.is_verified = True
    
    db.session.commit()
    
    print(f'Password reset to: {new_password}')
    print(f'User is now verified: {user.is_verified}')
    print('Please use this password to log in.')
else:
    print('User not found')