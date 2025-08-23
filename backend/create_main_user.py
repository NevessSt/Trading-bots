from app import app
from models import User
from db import db
import getpass

def create_main_user():
    with app.app_context():
        print('Creating your main user account...')
        print('Please provide the following information:')
        
        email = input('Email: ').strip()
        username = input('Username: ').strip()
        password = getpass.getpass('Password (min 8 characters): ')
        first_name = input('First Name (optional): ').strip() or None
        last_name = input('Last Name (optional): ').strip() or None
        
        # Validate inputs
        if not email or '@' not in email:
            print('Error: Invalid email format')
            return
            
        if not username:
            print('Error: Username cannot be empty')
            return
            
        if len(password) < 8:
            print('Error: Password must be at least 8 characters long')
            return
        
        # Check if user already exists
        if User.find_by_email(email):
            print(f'Error: Email {email} is already registered')
            return
            
        if User.find_by_username(username):
            print(f'Error: Username {username} is already taken')
            return
        
        try:
            # Create user
            user_data = {
                'email': email,
                'username': username,
                'password': password,
                'first_name': first_name,
                'last_name': last_name
            }
            
            new_user = User.create_user(user_data)
            
            print(f'\n✓ User created successfully!')
            print(f'Email: {new_user.email}')
            print(f'Username: {new_user.username}')
            print(f'User ID: {new_user.id}')
            print(f'\nYou can now log in with these credentials.')
            
        except Exception as e:
            print(f'Error creating user: {e}')
            db.session.rollback()

if __name__ == '__main__':
    create_main_user()