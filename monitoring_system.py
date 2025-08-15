#!/usr/bin/env python3
"""
Monitoring and Logging System for TradingBot Pro
Tracks system performance, user activities, trading metrics, and alerts
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import psutil
import threading
from collections import defaultdict, deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    SYSTEM = "system"
    TRADING = "trading"
    USER = "user"
    PERFORMANCE = "performance"
    SECURITY = "security"

class MonitoringSystem:
    def __init__(self):
        self.logger = self._setup_logging()
        self.metrics_buffer = defaultdict(deque)
        self.alert_handlers = []
        self.performance_thresholds = self._initialize_thresholds()
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_metrics = {}
        
        # Initialize metric collectors
        self.system_collector = SystemMetricsCollector()
        self.trading_collector = TradingMetricsCollector()
        self.user_collector = UserMetricsCollector()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging configuration"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create logger
        logger = logging.getLogger('TradingBotPro')
        logger.setLevel(logging.DEBUG)
        
        # File handlers
        # Main application log
        app_handler = logging.FileHandler('logs/application.log')
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(detailed_formatter)
        
        # Error log
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Trading log
        trading_handler = logging.FileHandler('logs/trading.log')
        trading_handler.setLevel(logging.INFO)
        trading_handler.setFormatter(detailed_formatter)
        
        # Security log
        security_handler = logging.FileHandler('logs/security.log')
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.addHandler(trading_handler)
        logger.addHandler(security_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_thresholds(self) -> Dict:
        """Initialize performance thresholds for alerts"""
        return {
            'cpu_usage': 80.0,  # %
            'memory_usage': 85.0,  # %
            'disk_usage': 90.0,  # %
            'response_time': 2.0,  # seconds
            'error_rate': 5.0,  # %
            'failed_trades': 10,  # count per hour
            'api_errors': 20,  # count per hour
            'concurrent_users': 1000,
            'database_connections': 80  # % of max
        }
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Monitoring system started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Monitoring system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                self._collect_all_metrics()
                
                # Check thresholds and generate alerts
                self._check_thresholds()
                
                # Clean old metrics
                self._cleanup_old_metrics()
                
                # Sleep for monitoring interval
                time.sleep(30)  # 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_all_metrics(self):
        """Collect all system metrics"""
        timestamp = datetime.utcnow()
        
        # System metrics
        system_metrics = self.system_collector.collect()
        self._store_metrics(MetricType.SYSTEM, system_metrics, timestamp)
        
        # Trading metrics
        trading_metrics = self.trading_collector.collect()
        self._store_metrics(MetricType.TRADING, trading_metrics, timestamp)
        
        # User metrics
        user_metrics = self.user_collector.collect()
        self._store_metrics(MetricType.USER, user_metrics, timestamp)
    
    def _store_metrics(self, metric_type: MetricType, metrics: Dict, timestamp: datetime):
        """Store metrics in buffer"""
        metric_entry = {
            'timestamp': timestamp,
            'type': metric_type.value,
            'data': metrics
        }
        
        # Store in buffer (keep last 1000 entries)
        self.metrics_buffer[metric_type.value].append(metric_entry)
        if len(self.metrics_buffer[metric_type.value]) > 1000:
            self.metrics_buffer[metric_type.value].popleft()
        
        # Update last metrics for threshold checking
        self.last_metrics[metric_type.value] = metrics
    
    def _check_thresholds(self):
        """Check metrics against thresholds and generate alerts"""
        system_metrics = self.last_metrics.get('system', {})
        trading_metrics = self.last_metrics.get('trading', {})
        user_metrics = self.last_metrics.get('user', {})
        
        # System threshold checks
        if system_metrics.get('cpu_usage', 0) > self.performance_thresholds['cpu_usage']:
            self._generate_alert(
                AlertLevel.WARNING,
                "High CPU Usage",
                f"CPU usage is {system_metrics['cpu_usage']:.1f}%"
            )
        
        if system_metrics.get('memory_usage', 0) > self.performance_thresholds['memory_usage']:
            self._generate_alert(
                AlertLevel.WARNING,
                "High Memory Usage",
                f"Memory usage is {system_metrics['memory_usage']:.1f}%"
            )
        
        if system_metrics.get('disk_usage', 0) > self.performance_thresholds['disk_usage']:
            self._generate_alert(
                AlertLevel.ERROR,
                "High Disk Usage",
                f"Disk usage is {system_metrics['disk_usage']:.1f}%"
            )
        
        # Trading threshold checks
        if trading_metrics.get('failed_trades_per_hour', 0) > self.performance_thresholds['failed_trades']:
            self._generate_alert(
                AlertLevel.ERROR,
                "High Trade Failure Rate",
                f"Failed trades: {trading_metrics['failed_trades_per_hour']} per hour"
            )
        
        if trading_metrics.get('api_errors_per_hour', 0) > self.performance_thresholds['api_errors']:
            self._generate_alert(
                AlertLevel.WARNING,
                "High API Error Rate",
                f"API errors: {trading_metrics['api_errors_per_hour']} per hour"
            )
        
        # User threshold checks
        if user_metrics.get('concurrent_users', 0) > self.performance_thresholds['concurrent_users']:
            self._generate_alert(
                AlertLevel.INFO,
                "High User Load",
                f"Concurrent users: {user_metrics['concurrent_users']}"
            )
    
    def _generate_alert(self, level: AlertLevel, title: str, message: str):
        """Generate and handle alerts"""
        alert = {
            'timestamp': datetime.utcnow(),
            'level': level.value,
            'title': title,
            'message': message,
            'resolved': False
        }
        
        # Log alert
        log_method = getattr(self.logger, level.value.lower(), self.logger.info)
        log_method(f"ALERT: {title} - {message}")
        
        # Handle alert through registered handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for metric_type in self.metrics_buffer:
            buffer = self.metrics_buffer[metric_type]
            while buffer and buffer[0]['timestamp'] < cutoff_time:
                buffer.popleft()
    
    def add_alert_handler(self, handler):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
    
    def get_metrics_summary(self, hours: int = 1) -> Dict:
        """Get metrics summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        summary = {}
        
        for metric_type, buffer in self.metrics_buffer.items():
            recent_metrics = [m for m in buffer if m['timestamp'] >= cutoff_time]
            
            if recent_metrics:
                # Calculate averages and totals
                summary[metric_type] = self._calculate_metric_summary(recent_metrics)
        
        return summary
    
    def _calculate_metric_summary(self, metrics: List[Dict]) -> Dict:
        """Calculate summary statistics for metrics"""
        if not metrics:
            return {}
        
        # Extract numeric values
        numeric_data = defaultdict(list)
        for metric in metrics:
            for key, value in metric['data'].items():
                if isinstance(value, (int, float)):
                    numeric_data[key].append(value)
        
        # Calculate statistics
        summary = {}
        for key, values in numeric_data.items():
            if values:
                summary[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'current': values[-1] if values else 0
                }
        
        return summary
    
    def log_user_action(self, user_id: int, action: str, details: Dict = None):
        """Log user action"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'details': details or {}
        }
        
        self.logger.info(f"USER_ACTION: {json.dumps(log_entry)}")
    
    def log_trade_event(self, user_id: int, event_type: str, trade_data: Dict):
        """Log trading event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'event_type': event_type,
            'trade_data': trade_data
        }
        
        self.logger.info(f"TRADE_EVENT: {json.dumps(log_entry)}")
    
    def log_security_event(self, event_type: str, details: Dict, severity: str = "warning"):
        """Log security event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details
        }
        
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(f"SECURITY_EVENT: {json.dumps(log_entry)}")
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        latest_metrics = {}
        for metric_type, buffer in self.metrics_buffer.items():
            if buffer:
                latest_metrics[metric_type] = buffer[-1]['data']
        
        # Determine health status
        health_score = 100
        issues = []
        
        system_metrics = latest_metrics.get('system', {})
        if system_metrics.get('cpu_usage', 0) > 80:
            health_score -= 20
            issues.append("High CPU usage")
        
        if system_metrics.get('memory_usage', 0) > 85:
            health_score -= 20
            issues.append("High memory usage")
        
        trading_metrics = latest_metrics.get('trading', {})
        if trading_metrics.get('error_rate', 0) > 5:
            health_score -= 30
            issues.append("High trading error rate")
        
        # Determine status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 70:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        else:
            status = "poor"
        
        return {
            'status': status,
            'health_score': max(0, health_score),
            'issues': issues,
            'last_updated': datetime.utcnow().isoformat(),
            'metrics': latest_metrics
        }

class SystemMetricsCollector:
    """Collects system performance metrics"""
    
    def collect(self) -> Dict:
        """Collect system metrics"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': self._get_network_io(),
                'process_count': len(psutil.pids()),
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_network_io(self) -> Dict:
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except:
            return {}

class TradingMetricsCollector:
    """Collects trading-related metrics"""
    
    def collect(self) -> Dict:
        """Collect trading metrics"""
        # Mock implementation - would connect to trading engine
        return {
            'active_strategies': 25,
            'total_trades_today': 150,
            'successful_trades': 142,
            'failed_trades': 8,
            'total_volume': 125000.50,
            'profit_loss': 2500.75,
            'api_calls_per_minute': 45,
            'average_response_time': 0.25,
            'error_rate': 5.3,
            'failed_trades_per_hour': 3,
            'api_errors_per_hour': 12
        }

class UserMetricsCollector:
    """Collects user activity metrics"""
    
    def collect(self) -> Dict:
        """Collect user metrics"""
        # Mock implementation - would query user database
        return {
            'total_users': 1250,
            'active_users_today': 320,
            'concurrent_users': 85,
            'new_registrations_today': 12,
            'subscription_renewals': 8,
            'support_tickets_open': 5,
            'average_session_duration': 45.5  # minutes
        }

class EmailAlertHandler:
    """Email alert handler"""
    
    def __init__(self, smtp_config: Dict):
        self.smtp_config = smtp_config
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, alert: Dict):
        """Send email alert"""
        try:
            if alert['level'] in ['error', 'critical']:
                self._send_email(alert)
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_email(self, alert: Dict):
        """Send email notification"""
        msg = MIMEMultipart()
        msg['From'] = self.smtp_config['from_email']
        msg['To'] = self.smtp_config['to_email']
        msg['Subject'] = f"TradingBot Alert: {alert['title']}"
        
        body = f"""
        Alert Level: {alert['level'].upper()}
        Title: {alert['title']}
        Message: {alert['message']}
        Time: {alert['timestamp']}
        
        Please check the system immediately.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port']) as server:
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)

if __name__ == "__main__":
    # Initialize monitoring system
    monitoring = MonitoringSystem()
    
    # Add email alert handler
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'from_email': 'alerts@tradingbot.com',
        'to_email': 'admin@tradingbot.com'
    }
    
    email_handler = EmailAlertHandler(email_config)
    monitoring.add_alert_handler(email_handler)
    
    # Start monitoring
    monitoring.start_monitoring()
    
    print("Monitoring system started")
    print("System health:", monitoring.get_system_health())