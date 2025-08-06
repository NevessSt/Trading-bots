from flask import current_app
from pymongo import MongoClient, DESCENDING
from bson.objectid import ObjectId
from datetime import datetime

class Trade:
    """Trade model for database operations"""
    
    @staticmethod
    def get_collection():
        """Get the trades collection from MongoDB"""
        mongo_client = MongoClient(current_app.config['MONGO_URI'])
        db = mongo_client.get_database()
        return db.trades
    
    @staticmethod
    def create(trade_data):
        """Create a new trade record
        
        Args:
            trade_data (dict): Trade data including user_id, symbol, type, etc.
            
        Returns:
            ObjectId: ID of the created trade, or None if creation failed
        """
        trades = Trade.get_collection()
        
        # Add timestamp if not present
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.utcnow()
        
        result = trades.insert_one(trade_data)
        
        if result.inserted_id:
            return result.inserted_id
        return None
    
    @staticmethod
    def find_by_id(trade_id):
        """Find a trade by ID
        
        Args:
            trade_id (str): Trade ID
            
        Returns:
            dict: Trade document, or None if not found
        """
        trades = Trade.get_collection()
        
        try:
            return trades.find_one({'_id': ObjectId(trade_id)})
        except:
            return None
    
    @staticmethod
    def find(filters, limit=100, skip=0, sort_by='timestamp', sort_order=DESCENDING):
        """Find trades with filters and pagination
        
        Args:
            filters (dict): Filter criteria
            limit (int): Maximum number of trades to return
            skip (int): Number of trades to skip
            sort_by (str): Field to sort by
            sort_order (int): Sort order (pymongo.ASCENDING or pymongo.DESCENDING)
            
        Returns:
            list: List of trade documents
        """
        trades = Trade.get_collection()
        
        cursor = trades.find(filters).sort(sort_by, sort_order).limit(limit).skip(skip)
        
        # Convert ObjectId to string for JSON serialization
        result = []
        for trade in cursor:
            trade['_id'] = str(trade['_id'])
            if 'user_id' in trade and isinstance(trade['user_id'], ObjectId):
                trade['user_id'] = str(trade['user_id'])
            result.append(trade)
        
        return result
    
    @staticmethod
    def count(filters):
        """Count trades matching filters
        
        Args:
            filters (dict): Filter criteria
            
        Returns:
            int: Number of matching trades
        """
        trades = Trade.get_collection()
        return trades.count_documents(filters)
    
    @staticmethod
    def get_recent_trades(user_id, limit=10):
        """Get recent trades for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of trades to return
            
        Returns:
            list: List of recent trade documents
        """
        return Trade.find({'user_id': user_id}, limit=limit)
    
    @staticmethod
    def get_trades_by_symbol(user_id, symbol, limit=100, skip=0):
        """Get trades for a user by symbol
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            limit (int): Maximum number of trades to return
            skip (int): Number of trades to skip
            
        Returns:
            list: List of trade documents
        """
        return Trade.find({'user_id': user_id, 'symbol': symbol}, limit=limit, skip=skip)
    
    @staticmethod
    def get_trades_by_date_range(user_id, start_date, end_date, limit=100, skip=0):
        """Get trades for a user within a date range
        
        Args:
            user_id (str): User ID
            start_date (datetime): Start date
            end_date (datetime): End date
            limit (int): Maximum number of trades to return
            skip (int): Number of trades to skip
            
        Returns:
            list: List of trade documents
        """
        return Trade.find({
            'user_id': user_id,
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }, limit=limit, skip=skip)
    
    @staticmethod
    def get_profit_loss(user_id, start_date=None, end_date=None):
        """Calculate profit/loss for a user
        
        Args:
            user_id (str): User ID
            start_date (datetime, optional): Start date
            end_date (datetime, optional): End date
            
        Returns:
            float: Total profit/loss
        """
        trades = Trade.get_collection()
        
        # Build match stage
        match_stage = {'user_id': user_id}
        
        if start_date or end_date:
            match_stage['timestamp'] = {}
            
            if start_date:
                match_stage['timestamp']['$gte'] = start_date
            
            if end_date:
                match_stage['timestamp']['$lte'] = end_date
        
        # Aggregate to calculate profit/loss
        pipeline = [
            {'$match': match_stage},
            {'$group': {
                '_id': None,
                'total_profit_loss': {'$sum': '$profit_loss'}
            }}
        ]
        
        result = list(trades.aggregate(pipeline))
        
        if result:
            return result[0]['total_profit_loss']
        return 0.0