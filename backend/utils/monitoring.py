import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from utils.logger import get_logger
import json

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = None
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels or {}
        }

@dataclass
class SystemHealth:
    """System health status"""
    status: str  # 'healthy', 'warning', 'critical'
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    error_rate: float
    response_time_avg: float
    timestamp: datetime
    
    def to_dict(self):
        return asdict(self)

class MetricsCollector:
    """Centralized metrics collection and monitoring"""
    
    def __init__(self, retention_hours: int = 24):
        self.logger = get_logger('monitoring')
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # System metrics
        self.system_metrics = deque(maxlen=1000)
        self.api_metrics = deque(maxlen=1000)
        self.trade_metrics = deque(maxlen=1000)
        self.error_metrics = deque(maxlen=1000)
        
        # Real-time tracking
        self.active_requests = 0
        self.total_requests = 0
        self.error_count = 0
        self.response_times = deque(maxlen=100)
        
        # Start background collection
        self._start_collection_thread()
        
    def _start_collection_thread(self):
        """Start background thread for system metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(30)  # Collect every 30 seconds
                except Exception as e:
                    self.logger.error(f"Error collecting system metrics: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
        
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Calculate error rate
            error_rate = (self.error_count / max(self.total_requests, 1)) * 100
            
            # Average response time
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            
            health = SystemHealth(
                status=self._determine_health_status(cpu_percent, memory.percent, error_rate),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                active_connections=connections,
                error_rate=error_rate,
                response_time_avg=avg_response_time,
                timestamp=datetime.utcnow()
            )
            
            self.system_metrics.append(health)
            
            # Log critical issues
            if health.status == 'critical':
                self.logger.error(f"System health critical: CPU={cpu_percent}%, Memory={memory.percent}%, Errors={error_rate}%")
            elif health.status == 'warning':
                self.logger.warning(f"System health warning: CPU={cpu_percent}%, Memory={memory.percent}%, Errors={error_rate}%")
                
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def _determine_health_status(self, cpu: float, memory: float, error_rate: float) -> str:
        """Determine overall system health status"""
        if cpu > 90 or memory > 90 or error_rate > 10:
            return 'critical'
        elif cpu > 70 or memory > 70 or error_rate > 5:
            return 'warning'
        else:
            return 'healthy'
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self.counters[key] += value
        
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            value=self.counters[key],
            labels=labels
        )
        self.metrics[name].append(metric)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self.gauges[key] = value
        
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels
        )
        self.metrics[name].append(metric)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
        self.histograms[key].append(value)
        
        # Keep only recent values (last 1000)
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        metric = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels
        )
        self.metrics[name].append(metric)
    
    def start_timer(self, name: str) -> 'Timer':
        """Start a timer for measuring duration"""
        return Timer(self, name)
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API call metrics"""
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_count += 1
        
        # Record detailed metrics
        labels = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        }
        
        self.increment_counter('api_requests_total', labels=labels)
        self.record_histogram('api_response_time', response_time, labels=labels)
        
        # Store API metrics
        api_metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time
        }
        self.api_metrics.append(api_metric)
    
    def record_trade(self, user_id: str, bot_id: str, symbol: str, side: str, 
                    amount: float, price: float, status: str, error: str = None):
        """Record trade execution metrics"""
        labels = {
            'symbol': symbol,
            'side': side,
            'status': status
        }
        
        self.increment_counter('trades_total', labels=labels)
        self.set_gauge('last_trade_price', price, {'symbol': symbol})
        self.record_histogram('trade_amount', amount, labels=labels)
        
        # Store trade metrics
        trade_metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'bot_id': bot_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': status,
            'error': error
        }
        self.trade_metrics.append(trade_metric)
        
        if error:
            self.record_error('trade_execution', error, {'symbol': symbol, 'bot_id': bot_id})
    
    def record_error(self, error_type: str, error_message: str, labels: Dict[str, str] = None):
        """Record error metrics"""
        error_labels = {'error_type': error_type}
        if labels:
            error_labels.update(labels)
        
        self.increment_counter('errors_total', labels=error_labels)
        
        # Store error details
        error_metric = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'labels': labels or {}
        }
        self.error_metrics.append(error_metric)
    
    def get_metrics(self, name: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Get metrics for a specific name within time range"""
        if name not in self.metrics:
            return []
        
        metrics = list(self.metrics[name])
        
        if start_time or end_time:
            filtered_metrics = []
            for metric in metrics:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                filtered_metrics.append(metric)
            metrics = filtered_metrics
        
        return [metric.to_dict() for metric in metrics]
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        if not self.system_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        latest = self.system_metrics[-1]
        return latest.to_dict()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        return {
            'system_health': self.get_system_health(),
            'api_metrics': {
                'total_requests': self.total_requests,
                'error_rate': (self.error_count / max(self.total_requests, 1)) * 100,
                'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                'active_requests': self.active_requests
            },
            'recent_trades': list(self.trade_metrics)[-10:],  # Last 10 trades
            'recent_errors': list(self.error_metrics)[-10:],  # Last 10 errors
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timestamp': now.isoformat()
        }
    
    def cleanup_old_metrics(self):
        """Clean up old metrics beyond retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for name, metric_list in self.metrics.items():
            # Remove old metrics
            while metric_list and metric_list[0].timestamp < cutoff_time:
                metric_list.popleft()
        
        # Clean up system metrics
        while self.system_metrics and self.system_metrics[0].timestamp < cutoff_time:
            self.system_metrics.popleft()
        
        # Clean up other metrics
        for metric_list in [self.api_metrics, self.trade_metrics, self.error_metrics]:
            while metric_list and datetime.fromisoformat(metric_list[0]['timestamp']) < cutoff_time:
                metric_list.popleft()

class Timer:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_histogram(self.name, duration, self.labels)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector