from models.user import User
from db import db
from app import app

app.app_context().push()

user = User.query.filter_by(email='danielmanji38@gmail.com').first()
if user:
    print(f'User found: {user.username}')
    print(f'Email: {user.email}')
    print(f'Is verified: {user.is_verified}')
    print(f'Is active: {user.is_active}')
    print(f'Password check with "newpassword123": {user.check_password("newpassword123")}')
else:
    print('User not found')