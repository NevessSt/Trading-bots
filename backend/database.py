"""Database management utilities and operations."""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import current_app
from db import db

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database operations and management."""
    
    def __init__(self, app=None):
        """Initialize DatabaseManager."""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the database manager with Flask app."""
        self.app = app
    
    def create_tables(self):
        """Create all database tables."""
        try:
            with self.app.app_context():
                db.create_all()
                logger.info("Database tables created successfully")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables."""
        try:
            with self.app.app_context():
                db.drop_all()
                logger.info("Database tables dropped successfully")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {e}")
            return False
    
    def reset_database(self):
        """Reset the database by dropping and recreating all tables."""
        try:
            self.drop_tables()
            self.create_tables()
            logger.info("Database reset successfully")
            return True
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
        """Execute a raw SQL query."""
        try:
            with db.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return None
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Get information about a specific table."""
        try:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
            result = self.execute_query(query, {'table_name': table_name})
            return result
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")
            return None
    
    def get_database_stats(self) -> Optional[Dict]:
        """Get database statistics."""
        try:
            stats = {}
            
            # Get table counts
            from models.user import User
            from models.bot import Bot
            from models.trade import Trade
            from models.subscription import Subscription
            from models.api_key import APIKey
            
            stats['users'] = User.query.count()
            stats['bots'] = Bot.query.count()
            stats['trades'] = Trade.query.count()
            stats['subscriptions'] = Subscription.query.count()
            stats['api_keys'] = APIKey.query.count()
            
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return None
    
    def backup_table(self, table_name: str) -> Optional[List[Dict]]:
        """Create a backup of a table's data."""
        try:
            query = f"SELECT * FROM {table_name}"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error backing up table {table_name}: {e}")
            return None
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """Perform database optimization tasks."""
        try:
            # This is PostgreSQL specific - adjust for other databases
            with db.engine.connect() as connection:
                connection.execute(text("VACUUM ANALYZE"))
                logger.info("Database optimization completed")
                return True
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return False
    
    def get_active_connections(self) -> Optional[int]:
        """Get the number of active database connections."""
        try:
            query = """
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """
            result = self.execute_query(query)
            if result:
                return result[0]['active_connections']
            return None
        except Exception as e:
            logger.error(f"Error getting active connections: {e}")
            return None
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data from the database."""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up old trades (example)
            from models.trade import Trade
            old_trades = Trade.query.filter(Trade.created_at < cutoff_date).all()
            
            for trade in old_trades:
                db.session.delete(trade)
            
            db.session.commit()
            logger.info(f"Cleaned up {len(old_trades)} old trades")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.session.rollback()
            return False
    
    def migrate_data(self, migration_script: str) -> bool:
        """Execute a data migration script."""
        try:
            with db.engine.connect() as connection:
                connection.execute(text(migration_script))
                logger.info("Data migration completed successfully")
                return True
        except Exception as e:
            logger.error(f"Error during data migration: {e}")
            return False


# Global database manager instance
database_manager = DatabaseManager()