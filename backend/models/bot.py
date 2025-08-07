from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import os

class Bot:
    """Bot model for MongoDB operations"""
    
    @staticmethod
    def get_collection():
        """Get the bots collection"""
        client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        db = client.trading_bot
        return db.bots
    
    @staticmethod
    def create(bot_data):
        """Create a new bot
        
        Args:
            bot_data (dict): Bot data
            
        Returns:
            str: Bot ID
        """
        collection = Bot.get_collection()
        bot_data['created_at'] = datetime.utcnow()
        bot_data['updated_at'] = datetime.utcnow()
        bot_data['is_active'] = False
        bot_data['is_running'] = False
        
        result = collection.insert_one(bot_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(bot_id):
        """Find bot by ID
        
        Args:
            bot_id (str): Bot ID
            
        Returns:
            dict: Bot data or None
        """
        collection = Bot.get_collection()
        bot = collection.find_one({'_id': ObjectId(bot_id)})
        if bot:
            bot['_id'] = str(bot['_id'])
        return bot
    
    @staticmethod
    def find_by_user(user_id, skip=0, limit=10):
        """Find bots by user ID
        
        Args:
            user_id (str): User ID
            skip (int): Number of documents to skip
            limit (int): Maximum number of documents to return
            
        Returns:
            list: List of bots
        """
        collection = Bot.get_collection()
        bots = list(collection.find({'user_id': user_id})
                   .sort('created_at', -1)
                   .skip(skip)
                   .limit(limit))
        
        for bot in bots:
            bot['_id'] = str(bot['_id'])
        
        return bots
    
    @staticmethod
    def update(bot_id, update_data):
        """Update bot data
        
        Args:
            bot_id (str): Bot ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if updated successfully
        """
        collection = Bot.get_collection()
        update_data['updated_at'] = datetime.utcnow()
        
        result = collection.update_one(
            {'_id': ObjectId(bot_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def delete(bot_id):
        """Delete bot by ID
        
        Args:
            bot_id (str): Bot ID
            
        Returns:
            bool: True if deleted successfully
        """
        collection = Bot.get_collection()
        result = collection.delete_one({'_id': ObjectId(bot_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def find_active_by_user(user_id):
        """Find active bots by user ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of active bots
        """
        collection = Bot.get_collection()
        bots = list(collection.find({
            'user_id': user_id,
            'is_active': True
        }).sort('created_at', -1))
        
        for bot in bots:
            bot['_id'] = str(bot['_id'])
        
        return bots
    
    @staticmethod
    def find_running_by_user(user_id):
        """Find running bots by user ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of running bots
        """
        collection = Bot.get_collection()
        bots = list(collection.find({
            'user_id': user_id,
            'is_running': True
        }).sort('created_at', -1))
        
        for bot in bots:
            bot['_id'] = str(bot['_id'])
        
        return bots
    
    @staticmethod
    def count_by_user(user_id):
        """Count bots by user ID
        
        Args:
            user_id (str): User ID
            
        Returns:
            int: Number of bots
        """
        collection = Bot.get_collection()
        return collection.count_documents({'user_id': user_id})
    
    @staticmethod
    def set_running_status(bot_id, is_running):
        """Set bot running status
        
        Args:
            bot_id (str): Bot ID
            is_running (bool): Running status
            
        Returns:
            bool: True if updated successfully
        """
        collection = Bot.get_collection()
        result = collection.update_one(
            {'_id': ObjectId(bot_id)},
            {'$set': {
                'is_running': is_running,
                'updated_at': datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def set_active_status(bot_id, is_active):
        """Set bot active status
        
        Args:
            bot_id (str): Bot ID
            is_active (bool): Active status
            
        Returns:
            bool: True if updated successfully
        """
        collection = Bot.get_collection()
        result = collection.update_one(
            {'_id': ObjectId(bot_id)},
            {'$set': {
                'is_active': is_active,
                'updated_at': datetime.utcnow()
            }}
        )
        return result.modified_count > 0