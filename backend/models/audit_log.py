from datetime import datetime
from bson import ObjectId
from database import get_db

class AuditLog:
    """Audit log model for tracking security events and user actions"""
    
    @staticmethod
    def create(log_data):
        """Create a new audit log entry"""
        db = get_db()
        
        # Ensure required fields
        log_entry = {
            'user_id': log_data.get('user_id'),
            'action': log_data.get('action'),
            'details': log_data.get('details', {}),
            'ip_address': log_data.get('ip_address'),
            'user_agent': log_data.get('user_agent'),
            'timestamp': log_data.get('timestamp', datetime.utcnow()),
            'severity': log_data.get('severity', 'low'),
            'created_at': datetime.utcnow()
        }
        
        result = db.audit_logs.insert_one(log_entry)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(log_id):
        """Find audit log by ID"""
        db = get_db()
        return db.audit_logs.find_one({'_id': ObjectId(log_id)})
    
    @staticmethod
    def find(query, projection=None):
        """Find audit logs matching query"""
        db = get_db()
        return list(db.audit_logs.find(query, projection))
    
    @staticmethod
    def find_by_user(user_id, limit=100, skip=0):
        """Find audit logs for a specific user"""
        db = get_db()
        return list(db.audit_logs.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).limit(limit).skip(skip))
    
    @staticmethod
    def find_by_action(action, limit=100, skip=0):
        """Find audit logs for a specific action"""
        db = get_db()
        return list(db.audit_logs.find(
            {'action': action}
        ).sort('timestamp', -1).limit(limit).skip(skip))
    
    @staticmethod
    def find_by_severity(severity, limit=100, skip=0):
        """Find audit logs by severity level"""
        db = get_db()
        return list(db.audit_logs.find(
            {'severity': severity}
        ).sort('timestamp', -1).limit(limit).skip(skip))
    
    @staticmethod
    def find_recent(hours=24, limit=100):
        """Find recent audit logs within specified hours"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return list(db.audit_logs.find(
            {'timestamp': {'$gte': cutoff_time}}
        ).sort('timestamp', -1).limit(limit))
    
    @staticmethod
    def count(query):
        """Count audit logs matching query"""
        db = get_db()
        return db.audit_logs.count_documents(query)
    
    @staticmethod
    def get_user_activity_summary(user_id, days=30):
        """Get activity summary for a user"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$action',
                    'count': {'$sum': 1},
                    'last_occurrence': {'$max': '$timestamp'}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]
        
        return list(db.audit_logs.aggregate(pipeline))
    
    @staticmethod
    def get_security_events(days=7, severity_filter=None):
        """Get security events for monitoring"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        query = {
            'timestamp': {'$gte': cutoff_time}
        }
        
        if severity_filter:
            if isinstance(severity_filter, list):
                query['severity'] = {'$in': severity_filter}
            else:
                query['severity'] = severity_filter
        
        return list(db.audit_logs.find(query).sort('timestamp', -1))
    
    @staticmethod
    def cleanup_old_logs(days=90):
        """Clean up audit logs older than specified days"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Keep critical and high severity logs longer
        result_low = db.audit_logs.delete_many({
            'timestamp': {'$lt': cutoff_time},
            'severity': {'$in': ['low', 'medium']}
        })
        
        # Keep high/critical logs for 1 year
        year_cutoff = datetime.utcnow() - timedelta(days=365)
        result_high = db.audit_logs.delete_many({
            'timestamp': {'$lt': year_cutoff},
            'severity': {'$in': ['high', 'critical']}
        })
        
        return {
            'deleted_low_medium': result_low.deleted_count,
            'deleted_high_critical': result_high.deleted_count
        }
    
    @staticmethod
    def get_failed_login_attempts(user_id=None, hours=24):
        """Get failed login attempts"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = {
            'action': 'login_failed',
            'timestamp': {'$gte': cutoff_time}
        }
        
        if user_id:
            query['user_id'] = user_id
        
        return list(db.audit_logs.find(query).sort('timestamp', -1))
    
    @staticmethod
    def get_suspicious_activities(days=7):
        """Get potentially suspicious activities"""
        db = get_db()
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Find users with multiple failed logins
        failed_logins_pipeline = [
            {
                '$match': {
                    'action': 'login_failed',
                    'timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$user_id',
                    'failed_attempts': {'$sum': 1},
                    'ip_addresses': {'$addToSet': '$ip_address'}
                }
            },
            {
                '$match': {
                    'failed_attempts': {'$gte': 5}
                }
            }
        ]
        
        # Find users with logins from multiple IPs
        multiple_ips_pipeline = [
            {
                '$match': {
                    'action': 'login_success',
                    'timestamp': {'$gte': cutoff_time}
                }
            },
            {
                '$group': {
                    '_id': '$user_id',
                    'ip_addresses': {'$addToSet': '$ip_address'},
                    'login_count': {'$sum': 1}
                }
            },
            {
                '$match': {
                    '$expr': {'$gte': [{'$size': '$ip_addresses'}, 3]}
                }
            }
        ]
        
        return {
            'multiple_failed_logins': list(db.audit_logs.aggregate(failed_logins_pipeline)),
            'multiple_ip_logins': list(db.audit_logs.aggregate(multiple_ips_pipeline))
        }
    
    @staticmethod
    def create_indexes():
        """Create database indexes for better performance"""
        db = get_db()
        
        # Create indexes for common queries
        db.audit_logs.create_index('user_id')
        db.audit_logs.create_index('action')
        db.audit_logs.create_index('timestamp')
        db.audit_logs.create_index('severity')
        db.audit_logs.create_index([('user_id', 1), ('timestamp', -1)])
        db.audit_logs.create_index([('action', 1), ('timestamp', -1)])
        db.audit_logs.create_index('ip_address')
        
        # TTL index for automatic cleanup (optional)
        # db.audit_logs.create_index('timestamp', expireAfterSeconds=7776000)  # 90 days
        
        return True