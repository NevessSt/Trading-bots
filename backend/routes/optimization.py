from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.database_optimizer import DatabaseOptimizer, optimized_queries
from models.user import User
from utils.decorators import admin_required
from datetime import datetime, timedelta
import time

optimization_bp = Blueprint('optimization', __name__, url_prefix='/api/optimization')

@optimization_bp.route('/status', methods=['GET'])
@jwt_required()
@admin_required
def get_optimization_status():
    """Get current database optimization status"""
    try:
        optimizer = DatabaseOptimizer()
        
        # Check Redis connection
        redis_status = False
        if optimizer.redis_client:
            try:
                optimizer.redis_client.ping()
                redis_status = True
            except:
                pass
        
        # Get cache statistics
        cache_stats = {}
        if redis_status:
            try:
                info = optimizer.redis_client.info()
                cache_stats = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'hit_rate': 0
                }
                
                total_requests = cache_stats['keyspace_hits'] + cache_stats['keyspace_misses']
                if total_requests > 0:
                    cache_stats['hit_rate'] = (cache_stats['keyspace_hits'] / total_requests) * 100
            except Exception as e:
                current_app.logger.warning(f"Failed to get cache stats: {e}")
        
        # Check database indexes
        from sqlalchemy import text
        from db import db
        
        result = db.session.execute(text(
            "SELECT COUNT(*) as index_count FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%'"
        ))
        index_count = result.fetchone()[0]
        
        # Get table sizes
        result = db.session.execute(text("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'bots', 'trades', 'api_keys')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """))
        
        table_sizes = {row.tablename: row.size for row in result.fetchall()}
        
        return jsonify({
            'status': 'success',
            'data': {
                'redis_connected': redis_status,
                'cache_stats': cache_stats,
                'optimization_indexes': index_count,
                'table_sizes': table_sizes,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get optimization status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@optimization_bp.route('/apply', methods=['POST'])
@jwt_required()
@admin_required
def apply_optimizations():
    """Apply database optimizations"""
    try:
        optimizer = DatabaseOptimizer()
        
        results = {
            'indexes_created': False,
            'tables_analyzed': False,
            'db_settings_optimized': False
        }
        
        # Create indexes
        if optimizer.create_database_indexes():
            results['indexes_created'] = True
            current_app.logger.info("Database indexes created successfully")
        
        # Analyze tables
        if optimizer.analyze_tables():
            results['tables_analyzed'] = True
            current_app.logger.info("Table statistics updated successfully")
        
        # Apply database settings (may fail without superuser)
        try:
            if optimizer.optimize_database_settings():
                results['db_settings_optimized'] = True
                current_app.logger.info("Database settings optimized successfully")
        except Exception as e:
            current_app.logger.warning(f"Database settings optimization failed: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Database optimizations applied',
            'results': results
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to apply optimizations: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@optimization_bp.route('/cache/clear', methods=['POST'])
@jwt_required()
@admin_required
def clear_cache():
    """Clear all cache entries"""
    try:
        optimizer = DatabaseOptimizer()
        
        if not optimizer.redis_client:
            return jsonify({
                'status': 'error',
                'message': 'Redis cache not available'
            }), 400
        
        # Get cache pattern from request
        data = request.get_json() or {}
        pattern = data.get('pattern', '*')
        
        # Clear cache entries
        keys = optimizer.redis_client.keys(pattern)
        if keys:
            optimizer.redis_client.delete(*keys)
            cleared_count = len(keys)
        else:
            cleared_count = 0
        
        return jsonify({
            'status': 'success',
            'message': f'Cleared {cleared_count} cache entries',
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to clear cache: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@optimization_bp.route('/performance/queries', methods=['GET'])
@jwt_required()
@admin_required
def get_query_performance():
    """Get query performance metrics"""
    try:
        from sqlalchemy import text
        from db import db
        
        # Get slow queries from PostgreSQL stats
        result = db.session.execute(text("""
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements 
            WHERE mean_time > 100
            ORDER BY mean_time DESC 
            LIMIT 10
        """))
        
        slow_queries = []
        for row in result.fetchall():
            slow_queries.append({
                'query': row.query[:200] + '...' if len(row.query) > 200 else row.query,
                'calls': row.calls,
                'total_time': round(row.total_time, 2),
                'mean_time': round(row.mean_time, 2),
                'rows': row.rows
            })
        
        # Get table statistics
        result = db.session.execute(text("""
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY seq_scan DESC
        """))
        
        table_stats = []
        for row in result.fetchall():
            table_stats.append({
                'table': row.tablename,
                'sequential_scans': row.seq_scan,
                'seq_rows_read': row.seq_tup_read,
                'index_scans': row.idx_scan,
                'idx_rows_fetched': row.idx_tup_fetch,
                'inserts': row.n_tup_ins,
                'updates': row.n_tup_upd,
                'deletes': row.n_tup_del
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'slow_queries': slow_queries,
                'table_statistics': table_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get query performance: {e}")
        return jsonify({
            'status': 'success',  # Don't fail if pg_stat_statements not available
            'data': {
                'slow_queries': [],
                'table_statistics': [],
                'message': 'Query performance monitoring not available (pg_stat_statements extension may not be installed)'
            }
        })

@optimization_bp.route('/test/performance', methods=['POST'])
@jwt_required()
@admin_required
def test_performance():
    """Test query performance with and without optimizations"""
    try:
        data = request.get_json() or {}
        test_type = data.get('type', 'user_trades')
        user_id = data.get('user_id', 1)
        
        results = {}
        
        if test_type == 'user_trades':
            # Test optimized vs non-optimized user trades query
            start_time = time.time()
            optimized_result = optimized_queries.get_user_trades_optimized(user_id, limit=100)
            optimized_time = time.time() - start_time
            
            # Test regular query
            from models.trade import Trade
            start_time = time.time()
            regular_trades = Trade.query.filter_by(user_id=user_id).limit(100).all()
            regular_result = [trade.to_dict() for trade in regular_trades]
            regular_time = time.time() - start_time
            
            results = {
                'test_type': 'user_trades',
                'optimized_time': round(optimized_time * 1000, 2),  # ms
                'regular_time': round(regular_time * 1000, 2),  # ms
                'improvement': round(((regular_time - optimized_time) / regular_time) * 100, 2) if regular_time > 0 else 0,
                'optimized_count': len(optimized_result),
                'regular_count': len(regular_result)
            }
        
        elif test_type == 'user_stats':
            # Test optimized vs non-optimized user stats
            start_time = time.time()
            optimized_result = optimized_queries.get_user_trading_stats(user_id)
            optimized_time = time.time() - start_time
            
            # Test regular query
            from models.trade import Trade
            start_time = time.time()
            regular_result = Trade.get_trade_stats(user_id=user_id)
            regular_time = time.time() - start_time
            
            results = {
                'test_type': 'user_stats',
                'optimized_time': round(optimized_time * 1000, 2),  # ms
                'regular_time': round(regular_time * 1000, 2),  # ms
                'improvement': round(((regular_time - optimized_time) / regular_time) * 100, 2) if regular_time > 0 else 0,
                'results_match': optimized_result.get('total_trades') == regular_result.get('total_trades')
            }
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        current_app.logger.error(f"Performance test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@optimization_bp.route('/cache/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """Get cache statistics for current user"""
    try:
        current_user_id = get_jwt_identity()
        optimizer = DatabaseOptimizer()
        
        if not optimizer.redis_client:
            return jsonify({
                'status': 'error',
                'message': 'Cache not available'
            }), 400
        
        # Get user-specific cache keys
        user_patterns = [
            f'*user_trades:{current_user_id}*',
            f'*user_stats:{current_user_id}*'
        ]
        
        cache_info = {
            'user_cache_keys': 0,
            'total_cache_keys': 0
        }
        
        # Count user-specific cache entries
        for pattern in user_patterns:
            keys = optimizer.redis_client.keys(pattern)
            cache_info['user_cache_keys'] += len(keys)
        
        # Count total cache entries
        all_keys = optimizer.redis_client.keys('*')
        cache_info['total_cache_keys'] = len(all_keys)
        
        return jsonify({
            'status': 'success',
            'data': cache_info
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get cache stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500