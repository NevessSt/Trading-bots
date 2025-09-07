#!/usr/bin/env python3
"""
Real-Time Monitoring System
Comprehensive monitoring with alerts, performance tracking, and system health monitoring
"""

import logging
import time
import threading
import psutil
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import asyncio
import websockets
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor
import queue
import statistics
from abc import ABC, abstractmethod

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics to monitor"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class SystemStatus(Enum):
    """System status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DOWN = "down"

@dataclass
class Alert:
    """Alert information"""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledgments: List[str] = field(default_factory=list)

@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    active_connections: int
    response_time_avg: float
    error_rate: float
    throughput: float
    custom_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    check_function: Callable[[], bool]
    interval: int  # seconds
    timeout: int = 30
    retries: int = 3
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_status: bool = True
    consecutive_failures: int = 0

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str  # Python expression
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for alert"""
        pass

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
            Alert: {alert.title}
            Severity: {alert.severity.value.upper()}
            Source: {alert.source}
            Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Message:
            {alert.message}
            
            Metadata:
            {json.dumps(alert.metadata, indent=2)}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent for alert: {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False

class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                'alert_id': alert.alert_id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            self.logger.info(f"Webhook notification sent for alert: {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False

class MetricsCollector:
    """Collects and stores metrics"""
    
    def __init__(self, max_history: int = 10000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def record_metric(self, metric: Metric):
        """Record a metric"""
        try:
            with self.lock:
                self.metrics[metric.name].append(metric)
                
                if metric.metric_type == MetricType.COUNTER:
                    self.counters[metric.name] += metric.value
                elif metric.metric_type == MetricType.GAUGE:
                    self.gauges[metric.name] = metric.value
                elif metric.metric_type == MetricType.HISTOGRAM:
                    self.histograms[metric.name].append(metric.value)
                    # Keep only last 1000 values for histograms
                    if len(self.histograms[metric.name]) > 1000:
                        self.histograms[metric.name] = self.histograms[metric.name][-1000:]
                elif metric.metric_type == MetricType.TIMER:
                    self.timers[metric.name].append(metric.value)
                    # Keep only last 1000 values for timers
                    if len(self.timers[metric.name]) > 1000:
                        self.timers[metric.name] = self.timers[metric.name][-1000:]
                        
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")
    
    def get_metric_value(self, name: str, metric_type: MetricType) -> Optional[Union[int, float, List[float]]]:
        """Get current metric value"""
        try:
            with self.lock:
                if metric_type == MetricType.COUNTER:
                    return self.counters.get(name, 0)
                elif metric_type == MetricType.GAUGE:
                    return self.gauges.get(name, 0.0)
                elif metric_type == MetricType.HISTOGRAM:
                    return self.histograms.get(name, [])
                elif metric_type == MetricType.TIMER:
                    return self.timers.get(name, [])
                return None
        except Exception as e:
            self.logger.error(f"Failed to get metric value: {e}")
            return None
    
    def get_metric_statistics(self, name: str, metric_type: MetricType, 
                            time_window_minutes: int = 60) -> Dict[str, float]:
        """Get metric statistics for a time window"""
        try:
            with self.lock:
                if name not in self.metrics:
                    return {}
                
                cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
                recent_metrics = [m for m in self.metrics[name] if m.timestamp >= cutoff_time]
                
                if not recent_metrics:
                    return {}
                
                values = [m.value for m in recent_metrics]
                
                stats = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'sum': sum(values)
                }
                
                if len(values) > 1:
                    stats['std'] = statistics.stdev(values)
                    stats['median'] = statistics.median(values)
                    
                    # Percentiles
                    sorted_values = sorted(values)
                    stats['p50'] = statistics.median(sorted_values)
                    stats['p90'] = sorted_values[int(0.9 * len(sorted_values))]
                    stats['p95'] = sorted_values[int(0.95 * len(sorted_values))]
                    stats['p99'] = sorted_values[int(0.99 * len(sorted_values))]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get metric statistics: {e}")
            return {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.record_metric(metric)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.record_metric(metric)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.record_metric(metric)
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer value (in milliseconds)"""
        metric = Metric(
            name=name,
            value=duration,
            metric_type=MetricType.TIMER,
            timestamp=datetime.now(),
            tags=tags or {},
            unit="ms"
        )
        self.record_metric(metric)

class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.monitor_thread = None
        self.network_io_baseline = None
    
    def start_monitoring(self, interval: int = 30):
        """Start system monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.set_gauge("system.cpu.percent", cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge("system.memory.percent", memory.percent)
            self.metrics_collector.set_gauge("system.memory.available", memory.available)
            self.metrics_collector.set_gauge("system.memory.used", memory.used)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_collector.set_gauge("system.disk.percent", disk_percent)
            self.metrics_collector.set_gauge("system.disk.free", disk.free)
            self.metrics_collector.set_gauge("system.disk.used", disk.used)
            
            # Network metrics
            network_io = psutil.net_io_counters()
            if self.network_io_baseline is None:
                self.network_io_baseline = network_io
            else:
                bytes_sent_delta = network_io.bytes_sent - self.network_io_baseline.bytes_sent
                bytes_recv_delta = network_io.bytes_recv - self.network_io_baseline.bytes_recv
                
                self.metrics_collector.set_gauge("system.network.bytes_sent_rate", bytes_sent_delta)
                self.metrics_collector.set_gauge("system.network.bytes_recv_rate", bytes_recv_delta)
                
                self.network_io_baseline = network_io
            
            # Process metrics
            process_count = len(psutil.pids())
            self.metrics_collector.set_gauge("system.processes.count", process_count)
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                self.metrics_collector.set_gauge("system.load.1min", load_avg[0])
                self.metrics_collector.set_gauge("system.load.5min", load_avg[1])
                self.metrics_collector.set_gauge("system.load.15min", load_avg[2])
            except AttributeError:
                # Windows doesn't have load average
                pass
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network_io = psutil.net_io_counters()
            
            # Get connection count (approximate)
            try:
                connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = 0
            
            # Get response time and error rate from metrics
            response_time_stats = self.metrics_collector.get_metric_statistics(
                "api.response_time", MetricType.TIMER, 5
            )
            response_time_avg = response_time_stats.get('avg', 0.0)
            
            error_rate_stats = self.metrics_collector.get_metric_statistics(
                "api.errors", MetricType.COUNTER, 5
            )
            total_requests_stats = self.metrics_collector.get_metric_statistics(
                "api.requests", MetricType.COUNTER, 5
            )
            
            error_count = error_rate_stats.get('sum', 0)
            total_requests = total_requests_stats.get('sum', 1)
            error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
            
            # Calculate throughput (requests per minute)
            throughput = total_requests_stats.get('count', 0) / 5.0 * 60  # Convert to per minute
            
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_io={
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                active_connections=connections,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                throughput=throughput
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get performance snapshot: {e}")
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={},
                active_connections=0,
                response_time_avg=0.0,
                error_rate=0.0,
                throughput=0.0
            )

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        
        self.alerts = {}  # alert_id -> Alert
        self.alert_rules = {}  # rule_name -> AlertRule
        self.notification_channels = []  # List of NotificationChannel
        
        self.alert_queue = queue.Queue()
        self.processing = False
        self.processor_thread = None
        
        self.lock = threading.Lock()
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.notification_channels.append(channel)
        self.logger.info(f"Added notification channel: {type(channel).__name__}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self.lock:
            self.alert_rules[rule.name] = rule
            self.logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        with self.lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                self.logger.info(f"Removed alert rule: {rule_name}")
    
    def start_processing(self):
        """Start alert processing"""
        if self.processing:
            return
        
        self.processing = True
        self.processor_thread = threading.Thread(
            target=self._process_alerts,
            daemon=True
        )
        self.processor_thread.start()
        self.logger.info("Alert processing started")
    
    def stop_processing(self):
        """Stop alert processing"""
        self.processing = False
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        self.logger.info("Alert processing stopped")
    
    def _process_alerts(self):
        """Process alerts from queue"""
        while self.processing:
            try:
                alert = self.alert_queue.get(timeout=1)
                asyncio.run(self._send_notifications(alert))
                self.alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing alert: {e}")
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for alert"""
        tasks = []
        for channel in self.notification_channels:
            tasks.append(channel.send_notification(alert))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            self.logger.info(f"Sent notifications for alert {alert.alert_id}: {success_count}/{len(tasks)} successful")
    
    def create_alert(self, title: str, message: str, severity: AlertSeverity, 
                    source: str, metadata: Dict[str, Any] = None) -> str:
        """Create and queue alert"""
        try:
            alert_id = f"alert_{int(time.time() * 1000)}"
            
            alert = Alert(
                alert_id=alert_id,
                title=title,
                message=message,
                severity=severity,
                source=source,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            with self.lock:
                self.alerts[alert_id] = alert
            
            # Queue for notification
            self.alert_queue.put(alert)
            
            # Record metric
            self.metrics_collector.increment_counter(
                "alerts.created",
                tags={'severity': severity.value, 'source': source}
            )
            
            self.logger.info(f"Alert created: {alert_id} - {title}")
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
            return ""
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "") -> bool:
        """Resolve alert"""
        try:
            with self.lock:
                if alert_id in self.alerts:
                    alert = self.alerts[alert_id]
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    
                    if resolved_by:
                        alert.acknowledgments.append(f"Resolved by {resolved_by} at {datetime.now()}")
                    
                    self.logger.info(f"Alert resolved: {alert_id}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert"""
        try:
            with self.lock:
                if alert_id in self.alerts:
                    alert = self.alerts[alert_id]
                    acknowledgment = f"Acknowledged by {acknowledged_by} at {datetime.now()}"
                    alert.acknowledgments.append(acknowledgment)
                    
                    self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def evaluate_alert_rules(self):
        """Evaluate all alert rules"""
        try:
            current_time = datetime.now()
            
            with self.lock:
                for rule_name, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue
                    
                    # Check cooldown
                    if rule.last_triggered:
                        cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                        if current_time < cooldown_end:
                            continue
                    
                    try:
                        # Evaluate condition
                        if self._evaluate_condition(rule.condition):
                            # Trigger alert
                            message = self._format_alert_message(rule.message_template)
                            
                            alert_id = self.create_alert(
                                title=f"Alert Rule: {rule.name}",
                                message=message,
                                severity=rule.severity,
                                source="alert_rule",
                                metadata={'rule_name': rule.name, 'condition': rule.condition}
                            )
                            
                            rule.last_triggered = current_time
                            rule.trigger_count += 1
                            
                            self.logger.warning(f"Alert rule triggered: {rule.name} - {alert_id}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to evaluate alert rule {rule.name}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Failed to evaluate alert rules: {e}")
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Create safe evaluation context
            context = {
                'cpu_percent': self.metrics_collector.get_metric_value('system.cpu.percent', MetricType.GAUGE) or 0,
                'memory_percent': self.metrics_collector.get_metric_value('system.memory.percent', MetricType.GAUGE) or 0,
                'disk_percent': self.metrics_collector.get_metric_value('system.disk.percent', MetricType.GAUGE) or 0,
                'error_rate': 0,  # Calculate from metrics
                'response_time': 0,  # Calculate from metrics
            }
            
            # Add custom metrics to context
            for metric_name in ['api.errors', 'api.requests', 'api.response_time']:
                stats = self.metrics_collector.get_metric_statistics(metric_name, MetricType.COUNTER, 5)
                context[metric_name.replace('.', '_')] = stats.get('avg', 0)
            
            # Safely evaluate condition
            return eval(condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def _format_alert_message(self, template: str) -> str:
        """Format alert message template"""
        try:
            # Get current metrics for template variables
            context = {
                'cpu_percent': self.metrics_collector.get_metric_value('system.cpu.percent', MetricType.GAUGE) or 0,
                'memory_percent': self.metrics_collector.get_metric_value('system.memory.percent', MetricType.GAUGE) or 0,
                'disk_percent': self.metrics_collector.get_metric_value('system.disk.percent', MetricType.GAUGE) or 0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return template.format(**context)
            
        except Exception as e:
            self.logger.error(f"Failed to format alert message: {e}")
            return template
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        try:
            with self.lock:
                alerts = []
                for alert in self.alerts.values():
                    if not alert.resolved:
                        if severity is None or alert.severity == severity:
                            alerts.append({
                                'alert_id': alert.alert_id,
                                'title': alert.title,
                                'message': alert.message,
                                'severity': alert.severity.value,
                                'source': alert.source,
                                'timestamp': alert.timestamp.isoformat(),
                                'metadata': alert.metadata,
                                'acknowledgments': alert.acknowledgments
                            })
                
                # Sort by timestamp (newest first)
                alerts.sort(key=lambda x: x['timestamp'], reverse=True)
                return alerts
                
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.lock:
                recent_alerts = [a for a in self.alerts.values() if a.timestamp >= cutoff_time]
                
                stats = {
                    'total_alerts': len(recent_alerts),
                    'active_alerts': len([a for a in recent_alerts if not a.resolved]),
                    'resolved_alerts': len([a for a in recent_alerts if a.resolved]),
                    'by_severity': {},
                    'by_source': {},
                    'resolution_time_avg': 0.0
                }
                
                # Count by severity
                for severity in AlertSeverity:
                    count = len([a for a in recent_alerts if a.severity == severity])
                    stats['by_severity'][severity.value] = count
                
                # Count by source
                sources = set(a.source for a in recent_alerts)
                for source in sources:
                    count = len([a for a in recent_alerts if a.source == source])
                    stats['by_source'][source] = count
                
                # Calculate average resolution time
                resolved_alerts = [a for a in recent_alerts if a.resolved and a.resolved_at]
                if resolved_alerts:
                    resolution_times = [
                        (a.resolved_at - a.timestamp).total_seconds() / 60  # minutes
                        for a in resolved_alerts
                    ]
                    stats['resolution_time_avg'] = statistics.mean(resolution_times)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}

class HealthCheckManager:
    """Manages health checks"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(__name__)
        
        self.health_checks = {}  # name -> HealthCheck
        self.checking = False
        self.checker_thread = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.lock = threading.Lock()
    
    def add_health_check(self, health_check: HealthCheck):
        """Add health check"""
        with self.lock:
            self.health_checks[health_check.name] = health_check
            self.logger.info(f"Added health check: {health_check.name}")
    
    def remove_health_check(self, name: str):
        """Remove health check"""
        with self.lock:
            if name in self.health_checks:
                del self.health_checks[name]
                self.logger.info(f"Removed health check: {name}")
    
    def start_checking(self, interval: int = 60):
        """Start health checking"""
        if self.checking:
            return
        
        self.checking = True
        self.checker_thread = threading.Thread(
            target=self._check_loop,
            args=(interval,),
            daemon=True
        )
        self.checker_thread.start()
        self.logger.info("Health checking started")
    
    def stop_checking(self):
        """Stop health checking"""
        self.checking = False
        if self.checker_thread:
            self.checker_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        self.logger.info("Health checking stopped")
    
    def _check_loop(self, interval: int):
        """Main health checking loop"""
        while self.checking:
            try:
                self._run_health_checks()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                time.sleep(interval)
    
    def _run_health_checks(self):
        """Run all enabled health checks"""
        try:
            current_time = datetime.now()
            
            with self.lock:
                checks_to_run = []
                
                for name, check in self.health_checks.items():
                    if not check.enabled:
                        continue
                    
                    # Check if it's time to run this check
                    if check.last_check is None or \
                       (current_time - check.last_check).total_seconds() >= check.interval:
                        checks_to_run.append((name, check))
            
            # Run checks in parallel
            if checks_to_run:
                futures = []
                for name, check in checks_to_run:
                    future = self.executor.submit(self._execute_health_check, name, check)
                    futures.append(future)
                
                # Wait for all checks to complete
                for future in futures:
                    try:
                        future.result(timeout=30)
                    except Exception as e:
                        self.logger.error(f"Health check execution failed: {e}")
                        
        except Exception as e:
            self.logger.error(f"Failed to run health checks: {e}")
    
    def _execute_health_check(self, name: str, check: HealthCheck):
        """Execute a single health check"""
        try:
            check.last_check = datetime.now()
            
            # Run the check function with timeout
            success = False
            for attempt in range(check.retries + 1):
                try:
                    success = check.check_function()
                    if success:
                        break
                except Exception as e:
                    self.logger.warning(f"Health check {name} attempt {attempt + 1} failed: {e}")
                    if attempt < check.retries:
                        time.sleep(1)  # Brief delay between retries
            
            # Update check status
            if success:
                if not check.last_status:
                    # Recovery from failure
                    self.alert_manager.create_alert(
                        title=f"Health Check Recovered: {name}",
                        message=f"Health check '{name}' has recovered after {check.consecutive_failures} failures.",
                        severity=AlertSeverity.INFO,
                        source="health_check",
                        metadata={'check_name': name, 'consecutive_failures': check.consecutive_failures}
                    )
                
                check.last_status = True
                check.consecutive_failures = 0
                
                # Record success metric
                self.metrics_collector.increment_counter(
                    "health_check.success",
                    tags={'check_name': name}
                )
            else:
                check.last_status = False
                check.consecutive_failures += 1
                
                # Create alert for failure
                severity = AlertSeverity.WARNING
                if check.consecutive_failures >= 3:
                    severity = AlertSeverity.ERROR
                if check.consecutive_failures >= 5:
                    severity = AlertSeverity.CRITICAL
                
                self.alert_manager.create_alert(
                    title=f"Health Check Failed: {name}",
                    message=f"Health check '{name}' has failed {check.consecutive_failures} consecutive times.",
                    severity=severity,
                    source="health_check",
                    metadata={'check_name': name, 'consecutive_failures': check.consecutive_failures}
                )
                
                # Record failure metric
                self.metrics_collector.increment_counter(
                    "health_check.failure",
                    tags={'check_name': name}
                )
            
            # Record check execution
            self.metrics_collector.increment_counter(
                "health_check.executed",
                tags={'check_name': name, 'status': 'success' if success else 'failure'}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute health check {name}: {e}")
            check.last_status = False
            check.consecutive_failures += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        try:
            with self.lock:
                total_checks = len(self.health_checks)
                passing_checks = sum(1 for check in self.health_checks.values() if check.last_status)
                failing_checks = total_checks - passing_checks
                
                # Determine overall status
                if total_checks == 0:
                    overall_status = SystemStatus.HEALTHY
                elif failing_checks == 0:
                    overall_status = SystemStatus.HEALTHY
                elif failing_checks <= total_checks * 0.2:  # 20% or less failing
                    overall_status = SystemStatus.WARNING
                elif failing_checks <= total_checks * 0.5:  # 50% or less failing
                    overall_status = SystemStatus.DEGRADED
                else:
                    overall_status = SystemStatus.CRITICAL
                
                check_details = []
                for name, check in self.health_checks.items():
                    check_details.append({
                        'name': name,
                        'status': 'passing' if check.last_status else 'failing',
                        'last_check': check.last_check.isoformat() if check.last_check else None,
                        'consecutive_failures': check.consecutive_failures,
                        'enabled': check.enabled
                    })
                
                return {
                    'overall_status': overall_status.value,
                    'total_checks': total_checks,
                    'passing_checks': passing_checks,
                    'failing_checks': failing_checks,
                    'checks': check_details,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return {
                'overall_status': SystemStatus.CRITICAL.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class MonitoringSystem:
    """Main monitoring system coordinating all components"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.health_check_manager = HealthCheckManager(self.metrics_collector, self.alert_manager)
        
        # WebSocket server for real-time updates
        self.websocket_server = None
        self.websocket_clients = set()
        
        # Monitoring state
        self.running = False
        self.rule_evaluation_thread = None
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.alert_manager.add_notification_channel(channel)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_manager.add_alert_rule(rule)
    
    def add_health_check(self, health_check: HealthCheck):
        """Add health check"""
        self.health_check_manager.add_health_check(health_check)
    
    def start(self):
        """Start monitoring system"""
        if self.running:
            return
        
        try:
            self.running = True
            
            # Start components
            self.system_monitor.start_monitoring()
            self.alert_manager.start_processing()
            self.health_check_manager.start_checking()
            
            # Start rule evaluation thread
            self.rule_evaluation_thread = threading.Thread(
                target=self._rule_evaluation_loop,
                daemon=True
            )
            self.rule_evaluation_thread.start()
            
            # Start WebSocket server
            self._start_websocket_server()
            
            self.logger.info("Monitoring system started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop monitoring system"""
        if not self.running:
            return
        
        try:
            self.running = False
            
            # Stop components
            self.system_monitor.stop_monitoring()
            self.alert_manager.stop_processing()
            self.health_check_manager.stop_checking()
            
            # Stop WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
            
            self.logger.info("Monitoring system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")
    
    def _rule_evaluation_loop(self):
        """Evaluate alert rules periodically"""
        while self.running:
            try:
                self.alert_manager.evaluate_alert_rules()
                time.sleep(60)  # Evaluate every minute
            except Exception as e:
                self.logger.error(f"Error in rule evaluation loop: {e}")
                time.sleep(60)
    
    def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        try:
            port = self.config.get('websocket_port', 8765)
            
            async def handle_client(websocket, path):
                self.websocket_clients.add(websocket)
                try:
                    await websocket.wait_closed()
                finally:
                    self.websocket_clients.discard(websocket)
            
            # Start server in a separate thread
            def run_server():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                start_server = websockets.serve(handle_client, "localhost", port)
                self.websocket_server = loop.run_until_complete(start_server)
                
                try:
                    loop.run_forever()
                except Exception as e:
                    self.logger.error(f"WebSocket server error: {e}")
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            self.logger.info(f"WebSocket server started on port {port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
    
    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast update to all WebSocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps({
            'type': update_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket message: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get performance snapshot
            performance = self.system_monitor.get_performance_snapshot()
            
            # Get health status
            health_status = self.health_check_manager.get_health_status()
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            # Get alert statistics
            alert_stats = self.alert_manager.get_alert_statistics()
            
            # Get key metrics
            key_metrics = {
                'cpu_percent': self.metrics_collector.get_metric_value('system.cpu.percent', MetricType.GAUGE),
                'memory_percent': self.metrics_collector.get_metric_value('system.memory.percent', MetricType.GAUGE),
                'disk_percent': self.metrics_collector.get_metric_value('system.disk.percent', MetricType.GAUGE),
                'api_requests_per_minute': self.metrics_collector.get_metric_statistics('api.requests', MetricType.COUNTER, 1).get('count', 0),
                'api_error_rate': 0,  # Calculate from metrics
                'api_response_time_avg': self.metrics_collector.get_metric_statistics('api.response_time', MetricType.TIMER, 5).get('avg', 0)
            }
            
            return {
                'performance': {
                    'timestamp': performance.timestamp.isoformat(),
                    'cpu_percent': performance.cpu_percent,
                    'memory_percent': performance.memory_percent,
                    'disk_usage_percent': performance.disk_usage_percent,
                    'network_io': performance.network_io,
                    'active_connections': performance.active_connections,
                    'response_time_avg': performance.response_time_avg,
                    'error_rate': performance.error_rate,
                    'throughput': performance.throughput
                },
                'health': health_status,
                'alerts': {
                    'active': active_alerts,
                    'statistics': alert_stats
                },
                'metrics': key_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def record_api_request(self, endpoint: str, method: str, response_time: float, 
                          status_code: int, user_id: str = ""):
        """Record API request metrics"""
        try:
            tags = {
                'endpoint': endpoint,
                'method': method,
                'status_code': str(status_code),
                'user_id': user_id
            }
            
            # Record request count
            self.metrics_collector.increment_counter('api.requests', tags=tags)
            
            # Record response time
            self.metrics_collector.record_timer('api.response_time', response_time, tags=tags)
            
            # Record errors
            if status_code >= 400:
                self.metrics_collector.increment_counter('api.errors', tags=tags)
            
        except Exception as e:
            self.logger.error(f"Failed to record API request metrics: {e}")
    
    def record_trading_metrics(self, symbol: str, action: str, quantity: float, 
                             price: float, profit_loss: float = 0.0):
        """Record trading-specific metrics"""
        try:
            tags = {
                'symbol': symbol,
                'action': action
            }
            
            # Record trade count
            self.metrics_collector.increment_counter('trading.trades', tags=tags)
            
            # Record trade volume
            self.metrics_collector.record_histogram('trading.volume', quantity, tags=tags)
            
            # Record trade value
            trade_value = quantity * price
            self.metrics_collector.record_histogram('trading.value', trade_value, tags=tags)
            
            # Record profit/loss
            if profit_loss != 0.0:
                self.metrics_collector.record_histogram('trading.pnl', profit_loss, tags=tags)
            
        except Exception as e:
            self.logger.error(f"Failed to record trading metrics: {e}")

# Example usage and built-in health checks
def create_default_health_checks() -> List[HealthCheck]:
    """Create default health checks"""
    
    def check_disk_space() -> bool:
        """Check if disk space is sufficient"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            return usage_percent < 90  # Alert if disk usage > 90%
        except Exception:
            return False
    
    def check_memory_usage() -> bool:
        """Check if memory usage is reasonable"""
        try:
            memory = psutil.virtual_memory()
            return memory.percent < 85  # Alert if memory usage > 85%
        except Exception:
            return False
    
    def check_cpu_usage() -> bool:
        """Check if CPU usage is reasonable"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent < 80  # Alert if CPU usage > 80%
        except Exception:
            return False
    
    def check_database_connection() -> bool:
        """Check database connectivity"""
        try:
            # This is a placeholder - implement actual database check
            # conn = sqlite3.connect('database.db')
            # conn.execute('SELECT 1')
            # conn.close()
            return True
        except Exception:
            return False
    
    return [
        HealthCheck(
            name="disk_space",
            check_function=check_disk_space,
            interval=300,  # 5 minutes
            timeout=10
        ),
        HealthCheck(
            name="memory_usage",
            check_function=check_memory_usage,
            interval=60,  # 1 minute
            timeout=5
        ),
        HealthCheck(
            name="cpu_usage",
            check_function=check_cpu_usage,
            interval=60,  # 1 minute
            timeout=5
        ),
        HealthCheck(
            name="database_connection",
            check_function=check_database_connection,
            interval=120,  # 2 minutes
            timeout=10
        )
    ]

def create_default_alert_rules() -> List[AlertRule]:
    """Create default alert rules"""
    return [
        AlertRule(
            name="high_cpu_usage",
            condition="cpu_percent > 80",
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage detected: {cpu_percent:.1f}% at {timestamp}",
            cooldown_minutes=5
        ),
        AlertRule(
            name="high_memory_usage",
            condition="memory_percent > 85",
            severity=AlertSeverity.WARNING,
            message_template="High memory usage detected: {memory_percent:.1f}% at {timestamp}",
            cooldown_minutes=5
        ),
        AlertRule(
            name="high_disk_usage",
            condition="disk_percent > 90",
            severity=AlertSeverity.ERROR,
            message_template="High disk usage detected: {disk_percent:.1f}% at {timestamp}",
            cooldown_minutes=10
        ),
        AlertRule(
            name="high_error_rate",
            condition="error_rate > 5",
            severity=AlertSeverity.ERROR,
            message_template="High error rate detected: {error_rate:.1f}% at {timestamp}",
            cooldown_minutes=3
        )
    ]

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create monitoring system
    config = {
        'websocket_port': 8765
    }
    
    monitoring = MonitoringSystem(config)
    
    # Add notification channels
    # email_channel = EmailNotificationChannel(
    #     smtp_server="smtp.gmail.com",
    #     smtp_port=587,
    #     username="your-email@gmail.com",
    #     password="your-password",
    #     from_email="alerts@yourcompany.com",
    #     to_emails=["admin@yourcompany.com"]
    # )
    # monitoring.add_notification_channel(email_channel)
    
    webhook_channel = WebhookNotificationChannel(
        webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        headers={"Content-Type": "application/json"}
    )
    monitoring.add_notification_channel(webhook_channel)
    
    # Add default health checks
    for health_check in create_default_health_checks():
        monitoring.add_health_check(health_check)
    
    # Add default alert rules
    for alert_rule in create_default_alert_rules():
        monitoring.add_alert_rule(alert_rule)
    
    try:
        # Start monitoring
        monitoring.start()
        
        print("Monitoring system started. Press Ctrl+C to stop.")
        
        # Simulate some activity
        while True:
            # Record some sample metrics
            monitoring.record_api_request("/api/trades", "GET", 150.0, 200, "user123")
            monitoring.record_trading_metrics("BTCUSDT", "buy", 0.1, 45000.0, 100.0)
            
            # Get dashboard data
            dashboard_data = monitoring.get_dashboard_data()
            print(f"Dashboard update: {dashboard_data['performance']['cpu_percent']:.1f}% CPU")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nStopping monitoring system...")
        monitoring.stop()
        print("Monitoring system stopped.")