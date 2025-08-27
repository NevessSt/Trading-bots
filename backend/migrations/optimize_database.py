#!/usr/bin/env python3
"""
Database Optimization Migration Script
Applies indexes, optimizations, and performance improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config.config import DevelopmentConfig
from db import db
from services.database_optimizer import DatabaseOptimizer
from models import User, Bot, Trade, APIKey
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    
    db.init_app(app)
    
    return app

def run_optimization_migration():
    """Run the complete database optimization migration"""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting database optimization migration...")
        
        optimizer = DatabaseOptimizer()
        
        # Step 1: Create database indexes
        logger.info("Creating database indexes...")
        if optimizer.create_database_indexes():
            logger.info("✓ Database indexes created successfully")
        else:
            logger.error("✗ Failed to create database indexes")
            return False
        
        # Step 2: Analyze tables for updated statistics
        logger.info("Analyzing tables for updated statistics...")
        if optimizer.analyze_tables():
            logger.info("✓ Table statistics updated successfully")
        else:
            logger.error("✗ Failed to update table statistics")
            return False
        
        # Step 3: Apply database-level optimizations (optional - requires superuser)
        logger.info("Applying database-level optimizations...")
        try:
            if optimizer.optimize_database_settings():
                logger.info("✓ Database optimizations applied successfully")
            else:
                logger.warning("⚠ Database optimizations failed (may require superuser privileges)")
        except Exception as e:
            logger.warning(f"⚠ Database optimizations skipped: {e}")
        
        # Step 4: Test cache functionality
        logger.info("Testing cache functionality...")
        test_key = "migration_test"
        test_value = {"timestamp": "2024-01-01", "test": True}
        
        if optimizer.set_cached(test_key, test_value, 'short'):
            cached_result = optimizer.get_cached(test_key)
            if cached_result == test_value:
                logger.info("✓ Cache functionality working correctly")
                optimizer.redis_client.delete(test_key)  # Cleanup
            else:
                logger.warning("⚠ Cache read/write mismatch")
        else:
            logger.warning("⚠ Cache functionality not available (Redis may not be running)")
        
        logger.info("Database optimization migration completed successfully!")
        return True

def rollback_optimization():
    """Rollback optimization changes (remove indexes)"""
    app = create_app()
    
    with app.app_context():
        logger.info("Rolling back database optimizations...")
        
        # List of indexes to remove
        indexes_to_remove = [
            'idx_users_email', 'idx_users_username', 'idx_users_license_type',
            'idx_users_created_at', 'idx_users_last_login',
            'idx_trades_user_id', 'idx_trades_bot_id', 'idx_trades_symbol',
            'idx_trades_status', 'idx_trades_created_at', 'idx_trades_executed_at',
            'idx_trades_exchange', 'idx_trades_strategy',
            'idx_trades_user_status', 'idx_trades_user_symbol', 'idx_trades_user_created',
            'idx_trades_bot_created', 'idx_trades_symbol_created', 'idx_trades_status_created',
            'idx_bots_user_id', 'idx_bots_strategy', 'idx_bots_symbol',
            'idx_bots_is_active', 'idx_bots_is_running', 'idx_bots_created_at',
            'idx_bots_last_run_at', 'idx_bots_user_active', 'idx_bots_user_running',
            'idx_bots_strategy_active', 'idx_api_keys_user_id', 'idx_api_keys_exchange',
            'idx_api_keys_is_active'
        ]
        
        try:
            from sqlalchemy import text
            for index_name in indexes_to_remove:
                try:
                    db.session.execute(text(f"DROP INDEX IF EXISTS {index_name};"))
                    logger.info(f"Dropped index: {index_name}")
                except Exception as e:
                    logger.warning(f"Failed to drop index {index_name}: {e}")
            
            db.session.commit()
            logger.info("✓ Rollback completed successfully")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"✗ Rollback failed: {e}")
            return False

def check_optimization_status():
    """Check current optimization status"""
    app = create_app()
    
    with app.app_context():
        logger.info("Checking database optimization status...")
        
        from sqlalchemy import text
        
        # Detect database type
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        is_sqlite = 'sqlite' in db_url.lower()
        is_postgres = 'postgresql' in db_url.lower()
        
        logger.info(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL' if is_postgres else 'Unknown'}")
        
        # Check indexes based on database type
        if is_sqlite:
            # SQLite index query
            result = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ))
            indexes = [row[0] for row in result.fetchall()]
        elif is_postgres:
            # PostgreSQL index query
            result = db.session.execute(text(
                "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%'"
            ))
            indexes = [row[0] for row in result.fetchall()]
        else:
            indexes = []
            logger.warning("Unknown database type, cannot check indexes")
        
        logger.info(f"Found {len(indexes)} optimization indexes:")
        for index in sorted(indexes):
            logger.info(f"  - {index}")
        
        # Check table information based on database type
        if is_sqlite:
            # SQLite table info
            tables = ['users', 'bots', 'trades', 'api_keys']
            logger.info("\nTable information:")
            for table in tables:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    logger.info(f"  {table}: {count} records")
                except Exception as e:
                    logger.info(f"  {table}: Error - {e}")
        elif is_postgres:
            # PostgreSQL table statistics
            result = db.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public' 
                AND tablename IN ('users', 'bots', 'trades', 'api_keys')
                ORDER BY tablename, attname
            """))
            
            logger.info("\nTable statistics:")
            current_table = None
            for row in result.fetchall():
                if row.tablename != current_table:
                    current_table = row.tablename
                    logger.info(f"\n{current_table.upper()}:")
                logger.info(f"  {row.attname}: distinct={row.n_distinct}, correlation={row.correlation}")
        
        # Test cache connection
        optimizer = DatabaseOptimizer()
        if optimizer.redis_client:
            try:
                optimizer.redis_client.ping()
                logger.info("\n✓ Redis cache connection: OK")
            except:
                logger.info("\n✗ Redis cache connection: FAILED")
        else:
            logger.info("\n✗ Redis cache: NOT CONFIGURED")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Optimization Migration")
    parser.add_argument('action', choices=['migrate', 'rollback', 'status'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        success = run_optimization_migration()
        sys.exit(0 if success else 1)
    elif args.action == 'rollback':
        success = rollback_optimization()
        sys.exit(0 if success else 1)
    elif args.action == 'status':
        check_optimization_status()
        sys.exit(0)