#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from database import db

def unlock_user(email):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User found: {user.username}")
            print(f"Is active: {user.is_active}")
            print(f"Is locked: {user.is_locked()}")
            print(f"Login attempts: {user.login_attempts}")
            print(f"Locked until: {user.locked_until}")
            
            # Unlock the user
            user.locked_until = None
            user.login_attempts = 0
            
            db.session.commit()
            print(f"User {user.username} has been unlocked!")
        else:
            print(f"User with email {email} not found.")

if __name__ == "__main__":
    unlock_user("danielmanji38@gmail.com")