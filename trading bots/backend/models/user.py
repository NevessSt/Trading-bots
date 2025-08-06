from flask import current_app
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class User:
    """User model for database operations"""
    
    @staticmethod
    def get_collection():
        """Get the users collection from MongoDB"""
        mongo_client = MongoClient(current_app.config['MONGO_URI'])
        db = mongo_client.get_database()
        return db.users
    
    @staticmethod
    def create(user_data):
        """Create a new user
        
        Args:
            user_data (dict): User data including email, username, password, etc.
            
        Returns:
            ObjectId: ID of the created user, or None if creation failed
        """
        users = User.get_collection()
        
        # Add created_at timestamp if not present
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.utcnow()
        
        result = users.insert_one(user_data)
        
        if result.inserted_id:
            return result.inserted_id
        return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find a user by ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User document, or None if not found
        """
        users = User.get_collection()
        
        try:
            return users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    @staticmethod
    def find_by_email(email):
        """Find a user by email
        
        Args:
            email (str): User email
            
        Returns:
            dict: User document, or None if not found
        """
        users = User.get_collection()
        return users.find_one({'email': email})
    
    @staticmethod
    def find_by_username(username):
        """Find a user by username
        
        Args:
            username (str): Username
            
        Returns:
            dict: User document, or None if not found
        """
        users = User.get_collection()
        return users.find_one({'username': username})
    
    @staticmethod
    def update(user_id, update_data):
        """Update a user
        
        Args:
            user_id (str): User ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        users = User.get_collection()
        
        # Add updated_at timestamp
        update_data['updated_at'] = datetime.utcnow()
        
        try:
            result = users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    @staticmethod
    def delete(user_id):
        """Delete a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        users = User.get_collection()
        
        try:
            result = users.delete_one({'_id': ObjectId(user_id)})
            return result.deleted_count > 0
        except:
            return False
    
    @staticmethod
    def list_all(limit=100, skip=0):
        """List all users with pagination
        
        Args:
            limit (int): Maximum number of users to return
            skip (int): Number of users to skip
            
        Returns:
            list: List of user documents
        """
        users = User.get_collection()
        
        cursor = users.find().limit(limit).skip(skip)
        return list(cursor)