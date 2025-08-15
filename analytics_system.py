#!/usr/bin/env python3
"""
Analytics System for TradingBot Pro
Provides comprehensive analytics, reporting, and insights on trading performance,
user behavior, and system metrics.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import time
import sqlite3
import csv
import pickle
from pathlib import Path
from collections import defaultdict, Counter
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class AnalyticsType(Enum):
    TRADING = "trading"
    USER = "user"
    SYSTEM = "system"
    FINANCIAL = "financial"
    MARKETING = "marketing"

class TimeFrame(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"
    PNG = "png"

@dataclass
class AnalyticsConfig:
    enabled: bool = True
    data_retention_days: int = 365
    collection_interval_seconds: int = 300  # 5 minutes
    database_path: str = "analytics.db"
    export_directory: str = "analytics_exports"
    auto_generate_reports: bool = True
    report_schedule: str = "0 0 * * 0"  # Weekly on Sunday at midnight
    anonymize_user_data: bool = True
    track_user_behavior: bool = True
    track_system_metrics: bool = True
    track_trading_metrics: bool = True
    track_financial_metrics: bool = True
    enable_machine_learning: bool = True
    enable_real_time_alerts: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "profit_loss_percent": 10.0,
        "trade_volume_change": 50.0,
        "user_activity_drop": 30.0,
        "system_cpu_usage": 80.0,
        "system_memory_usage": 80.0
    })

@dataclass
class TradingMetrics:
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    profit_loss: float = 0.0
    profit_loss_percent: float = 0.0
    average_trade_duration: float = 0.0  # in seconds
    trade_volume: float = 0.0
    largest_trade: float = 0.0
    smallest_trade: float = 0.0
    most_traded_pair: str = ""
    most_profitable_pair: str = ""
    least_profitable_pair: str = ""
    most_used_strategy: str = ""
    most_profitable_strategy: str = ""
    win_loss_ratio: float = 0.0
    average_profit_per_trade: float = 0.0
    average_loss_per_trade: float = 0.0
    risk_reward_ratio: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0  # in seconds
    volatility: float = 0.0

@dataclass
class UserMetrics:
    total_users: int = 0
    active_users: int = 0
    new_users: int = 0
    churned_users: int = 0
    premium_users: int = 0
    free_users: int = 0
    average_session_duration: float = 0.0  # in seconds
    average_sessions_per_user: float = 0.0
    most_active_time: str = ""
    most_used_features: List[str] = field(default_factory=list)
    user_retention_rate: float = 0.0
    conversion_rate: float = 0.0
    average_response_time: float = 0.0  # in seconds
    most_common_user_actions: List[str] = field(default_factory=list)
    geographic_distribution: Dict[str, int] = field(default_factory=dict)
    device_distribution: Dict[str, int] = field(default_factory=dict)
    browser_distribution: Dict[str, int] = field(default_factory=dict)
    average_trades_per_user: float = 0.0
    user_satisfaction_score: float = 0.0

@dataclass
class SystemMetrics:
    cpu_usage: float = 0.0  # percentage
    memory_usage: float = 0.0  # percentage
    disk_usage: float = 0.0  # percentage
    network_traffic: float = 0.0  # bytes
    response_time: float = 0.0  # in seconds
    error_rate: float = 0.0  # percentage
    request_rate: float = 0.0  # requests per second
    database_size: float = 0.0  # bytes
    database_connections: int = 0
    cache_hit_rate: float = 0.0  # percentage
    background_jobs: int = 0
    queue_size: int = 0
    average_job_duration: float = 0.0  # in seconds
    uptime: float = 0.0  # in seconds
    api_calls: int = 0
    websocket_connections: int = 0
    thread_count: int = 0
    open_file_descriptors: int = 0

@dataclass
class FinancialMetrics:
    total_revenue: float = 0.0
    subscription_revenue: float = 0.0
    transaction_revenue: float = 0.0
    other_revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    profit_margin: float = 0.0
    average_revenue_per_user: float = 0.0
    lifetime_value: float = 0.0
    customer_acquisition_cost: float = 0.0
    churn_rate: float = 0.0
    mrr: float = 0.0  # Monthly Recurring Revenue
    arr: float = 0.0  # Annual Recurring Revenue
    mrr_growth: float = 0.0  # percentage
    payment_success_rate: float = 0.0  # percentage
    refund_rate: float = 0.0  # percentage
    average_subscription_duration: float = 0.0  # in days

@dataclass
class MarketingMetrics:
    website_visitors: int = 0
    conversion_rate: float = 0.0  # percentage
    bounce_rate: float = 0.0  # percentage
    traffic_sources: Dict[str, int] = field(default_factory=dict)
    campaign_performance: Dict[str, Dict] = field(default_factory=dict)
    email_open_rate: float = 0.0  # percentage
    email_click_rate: float = 0.0  # percentage
    social_media_engagement: Dict[str, int] = field(default_factory=dict)
    cost_per_acquisition: float = 0.0
    landing_page_conversion: float = 0.0  # percentage
    referral_rate: float = 0.0  # percentage
    average_time_to_conversion: float = 0.0  # in days

@dataclass
class AnalyticsRecord:
    timestamp: datetime
    record_type: AnalyticsType
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AnalyticsSystem:
    def __init__(self, config: AnalyticsConfig = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or AnalyticsConfig()
        self.db_path = self.config.database_path
        self.export_dir = Path(self.config.export_directory)
        self.export_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize database
        self._init_database()
        
        # Collection thread
        self.collection_thread = None
        self.stop_collection = threading.Event()
        
        # Cached metrics
        self.cached_metrics = {
            AnalyticsType.TRADING: TradingMetrics(),
            AnalyticsType.USER: UserMetrics(),
            AnalyticsType.SYSTEM: SystemMetrics(),
            AnalyticsType.FINANCIAL: FinancialMetrics(),
            AnalyticsType.MARKETING: MarketingMetrics()
        }
        
        # Last update timestamps
        self.last_updates = {}
        
        # Machine learning models
        self.ml_models = {}
        
        self.logger.info("Analytics system initialized")
    
    def _init_database(self):
        """Initialize the analytics database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                record_type TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                data TEXT NOT NULL,
                metadata TEXT
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_trades INTEGER,
                successful_trades INTEGER,
                failed_trades INTEGER,
                profit_loss REAL,
                profit_loss_percent REAL,
                average_trade_duration REAL,
                trade_volume REAL,
                win_loss_ratio REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                volatility REAL
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_users INTEGER,
                active_users INTEGER,
                new_users INTEGER,
                churned_users INTEGER,
                premium_users INTEGER,
                free_users INTEGER,
                average_session_duration REAL,
                user_retention_rate REAL,
                conversion_rate REAL
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_traffic REAL,
                response_time REAL,
                error_rate REAL,
                request_rate REAL,
                uptime REAL
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_revenue REAL,
                subscription_revenue REAL,
                transaction_revenue REAL,
                costs REAL,
                profit REAL,
                profit_margin REAL,
                average_revenue_per_user REAL,
                mrr REAL,
                arr REAL
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                report_type TEXT NOT NULL,
                time_frame TEXT NOT NULL,
                file_path TEXT NOT NULL,
                metadata TEXT
            )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics_records (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_records (record_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_records (user_id)")
            
            conn.commit()
            conn.close()
            
            self.logger.info("Analytics database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics database: {e}")
            raise
    
    def start_collection(self):
        """Start the metrics collection thread"""
        if not self.config.enabled:
            self.logger.info("Analytics system is disabled")
            return
        
        if self.collection_thread and self.collection_thread.is_alive():
            self.logger.warning("Collection thread is already running")
            return
        
        self.stop_collection.clear()
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            daemon=True
        )
        self.collection_thread.start()
        self.logger.info("Analytics collection started")
    
    def stop_collection(self):
        """Stop the metrics collection thread"""
        if self.collection_thread and self.collection_thread.is_alive():
            self.stop_collection.set()
            self.collection_thread.join(timeout=10)
            self.logger.info("Analytics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop that runs in a separate thread"""
        while not self.stop_collection.is_set():
            try:
                # Collect all metrics
                if self.config.track_trading_metrics:
                    self._collect_trading_metrics()
                
                if self.config.track_user_behavior:
                    self._collect_user_metrics()
                
                if self.config.track_system_metrics:
                    self._collect_system_metrics()
                
                if self.config.track_financial_metrics:
                    self._collect_financial_metrics()
                
                # Generate reports if scheduled
                if self.config.auto_generate_reports:
                    self._check_report_schedule()
                
                # Clean up old data
                self._cleanup_old_data()
                
            except Exception as e:
                self.logger.error(f"Error in analytics collection: {e}")
            
            # Sleep until next collection interval
            self.stop_collection.wait(self.config.collection_interval_seconds)
    
    def _collect_trading_metrics(self):
        """Collect trading performance metrics"""
        try:
            # In a real implementation, this would query the database or trading system
            # For now, we'll just use placeholder logic
            
            # Example: Query recent trades
            # trades = self._query_recent_trades()
            
            # For demonstration, we'll create sample metrics
            metrics = TradingMetrics(
                total_trades=1250,
                successful_trades=875,
                failed_trades=375,
                profit_loss=12500.75,
                profit_loss_percent=8.5,
                average_trade_duration=1800,  # 30 minutes
                trade_volume=250000.0,
                largest_trade=5000.0,
                smallest_trade=100.0,
                most_traded_pair="BTC/USD",
                most_profitable_pair="ETH/USD",
                least_profitable_pair="XRP/USD",
                most_used_strategy="MovingAverageCrossover",
                most_profitable_strategy="RSIStrategy",
                win_loss_ratio=2.33,
                average_profit_per_trade=25.5,
                average_loss_per_trade=15.2,
                risk_reward_ratio=1.68,
                sharpe_ratio=1.25,
                max_drawdown=12.5,
                max_drawdown_duration=86400,  # 1 day
                volatility=0.15
            )
            
            # Store metrics in database
            self._store_trading_metrics(metrics)
            
            # Update cached metrics
            self.cached_metrics[AnalyticsType.TRADING] = metrics
            self.last_updates[AnalyticsType.TRADING] = datetime.now()
            
            # Check for alerts
            if self.config.enable_real_time_alerts:
                self._check_trading_alerts(metrics)
            
            self.logger.debug("Trading metrics collected")
            
        except Exception as e:
            self.logger.error(f"Failed to collect trading metrics: {e}")
    
    def _collect_user_metrics(self):
        """Collect user behavior metrics"""
        try:
            # In a real implementation, this would query the database or user system
            # For now, we'll just use placeholder logic
            
            # Example: Query user activity
            # user_activity = self._query_user_activity()
            
            # For demonstration, we'll create sample metrics
            metrics = UserMetrics(
                total_users=5000,
                active_users=2500,
                new_users=150,
                churned_users=75,
                premium_users=1000,
                free_users=4000,
                average_session_duration=1200,  # 20 minutes
                average_sessions_per_user=3.5,
                most_active_time="18:00-20:00",
                most_used_features=["Dashboard", "Trading", "Analytics"],
                user_retention_rate=85.0,
                conversion_rate=12.5,
                average_response_time=0.35,
                most_common_user_actions=["View Dashboard", "Check Portfolio", "Place Trade"],
                geographic_distribution={
                    "United States": 2000,
                    "United Kingdom": 800,
                    "Germany": 500,
                    "Canada": 400,
                    "Australia": 300
                },
                device_distribution={
                    "Desktop": 3000,
                    "Mobile": 1500,
                    "Tablet": 500
                },
                browser_distribution={
                    "Chrome": 2500,
                    "Firefox": 1000,
                    "Safari": 1000,
                    "Edge": 500
                },
                average_trades_per_user=5.2,
                user_satisfaction_score=4.2
            )
            
            # Store metrics in database
            self._store_user_metrics(metrics)
            
            # Update cached metrics
            self.cached_metrics[AnalyticsType.USER] = metrics
            self.last_updates[AnalyticsType.USER] = datetime.now()
            
            # Check for alerts
            if self.config.enable_real_time_alerts:
                self._check_user_alerts(metrics)
            
            self.logger.debug("User metrics collected")
            
        except Exception as e:
            self.logger.error(f"Failed to collect user metrics: {e}")
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # In a real implementation, this would query the system or monitoring tools
            # For now, we'll just use placeholder logic
            
            # Example: Query system stats
            # system_stats = self._query_system_stats()
            
            # For demonstration, we'll create sample metrics
            metrics = SystemMetrics(
                cpu_usage=45.0,
                memory_usage=60.0,
                disk_usage=55.0,
                network_traffic=1500000,  # 1.5 MB
                response_time=0.25,
                error_rate=1.2,
                request_rate=25.0,
                database_size=500000000,  # 500 MB
                database_connections=50,
                cache_hit_rate=85.0,
                background_jobs=15,
                queue_size=25,
                average_job_duration=5.5,
                uptime=1209600,  # 14 days
                api_calls=15000,
                websocket_connections=500,
                thread_count=25,
                open_file_descriptors=150
            )
            
            # Store metrics in database
            self._store_system_metrics(metrics)
            
            # Update cached metrics
            self.cached_metrics[AnalyticsType.SYSTEM] = metrics
            self.last_updates[AnalyticsType.SYSTEM] = datetime.now()
            
            # Check for alerts
            if self.config.enable_real_time_alerts:
                self._check_system_alerts(metrics)
            
            self.logger.debug("System metrics collected")
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def _collect_financial_metrics(self):
        """Collect financial metrics"""
        try:
            # In a real implementation, this would query the financial system
            # For now, we'll just use placeholder logic
            
            # Example: Query financial data
            # financial_data = self._query_financial_data()
            
            # For demonstration, we'll create sample metrics
            metrics = FinancialMetrics(
                total_revenue=125000.0,
                subscription_revenue=100000.0,
                transaction_revenue=20000.0,
                other_revenue=5000.0,
                costs=75000.0,
                profit=50000.0,
                profit_margin=40.0,
                average_revenue_per_user=25.0,
                lifetime_value=750.0,
                customer_acquisition_cost=50.0,
                churn_rate=5.0,
                mrr=35000.0,
                arr=420000.0,
                mrr_growth=3.5,
                payment_success_rate=98.5,
                refund_rate=1.2,
                average_subscription_duration=180  # 6 months
            )
            
            # Store metrics in database
            self._store_financial_metrics(metrics)
            
            # Update cached metrics
            self.cached_metrics[AnalyticsType.FINANCIAL] = metrics
            self.last_updates[AnalyticsType.FINANCIAL] = datetime.now()
            
            # Check for alerts
            if self.config.enable_real_time_alerts:
                self._check_financial_alerts(metrics)
            
            self.logger.debug("Financial metrics collected")
            
        except Exception as e:
            self.logger.error(f"Failed to collect financial metrics: {e}")
    
    def _store_trading_metrics(self, metrics: TradingMetrics):
        """Store trading metrics in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO trading_metrics (
                timestamp, total_trades, successful_trades, failed_trades,
                profit_loss, profit_loss_percent, average_trade_duration,
                trade_volume, win_loss_ratio, sharpe_ratio, max_drawdown, volatility
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                metrics.total_trades,
                metrics.successful_trades,
                metrics.failed_trades,
                metrics.profit_loss,
                metrics.profit_loss_percent,
                metrics.average_trade_duration,
                metrics.trade_volume,
                metrics.win_loss_ratio,
                metrics.sharpe_ratio,
                metrics.max_drawdown,
                metrics.volatility
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store trading metrics: {e}")
    
    def _store_user_metrics(self, metrics: UserMetrics):
        """Store user metrics in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO user_metrics (
                timestamp, total_users, active_users, new_users, churned_users,
                premium_users, free_users, average_session_duration,
                user_retention_rate, conversion_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                metrics.total_users,
                metrics.active_users,
                metrics.new_users,
                metrics.churned_users,
                metrics.premium_users,
                metrics.free_users,
                metrics.average_session_duration,
                metrics.user_retention_rate,
                metrics.conversion_rate
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store user metrics: {e}")
    
    def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO system_metrics (
                timestamp, cpu_usage, memory_usage, disk_usage, network_traffic,
                response_time, error_rate, request_rate, uptime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.disk_usage,
                metrics.network_traffic,
                metrics.response_time,
                metrics.error_rate,
                metrics.request_rate,
                metrics.uptime
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store system metrics: {e}")
    
    def _store_financial_metrics(self, metrics: FinancialMetrics):
        """Store financial metrics in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO financial_metrics (
                timestamp, total_revenue, subscription_revenue, transaction_revenue,
                costs, profit, profit_margin, average_revenue_per_user, mrr, arr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                metrics.total_revenue,
                metrics.subscription_revenue,
                metrics.transaction_revenue,
                metrics.costs,
                metrics.profit,
                metrics.profit_margin,
                metrics.average_revenue_per_user,
                metrics.mrr,
                metrics.arr
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store financial metrics: {e}")
    
    def track_event(self, event_type: str, user_id: str = None, session_id: str = None, 
                   data: Dict[str, Any] = None, metadata: Dict[str, Any] = None):
        """Track a specific event"""
        if not self.config.enabled:
            return
        
        try:
            record = AnalyticsRecord(
                timestamp=datetime.now(),
                record_type=AnalyticsType.USER,
                data=data or {},
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            # Add event type to data
            record.data['event_type'] = event_type
            
            # Store in database
            self._store_analytics_record(record)
            
            self.logger.debug(f"Tracked event: {event_type} for user: {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track event: {e}")
    
    def track_trade(self, trade_data: Dict[str, Any], user_id: str = None):
        """Track a trading operation"""
        if not self.config.enabled or not self.config.track_trading_metrics:
            return
        
        try:
            record = AnalyticsRecord(
                timestamp=datetime.now(),
                record_type=AnalyticsType.TRADING,
                data=trade_data,
                user_id=user_id
            )
            
            # Store in database
            self._store_analytics_record(record)
            
            self.logger.debug(f"Tracked trade for user: {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track trade: {e}")
    
    def track_user_session(self, user_id: str, session_id: str, session_data: Dict[str, Any]):
        """Track a user session"""
        if not self.config.enabled or not self.config.track_user_behavior:
            return
        
        try:
            record = AnalyticsRecord(
                timestamp=datetime.now(),
                record_type=AnalyticsType.USER,
                data=session_data,
                user_id=user_id,
                session_id=session_id
            )
            
            # Add session tracking data
            record.data['event_type'] = 'session'
            
            # Store in database
            self._store_analytics_record(record)
            
            self.logger.debug(f"Tracked session for user: {user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track user session: {e}")
    
    def _store_analytics_record(self, record: AnalyticsRecord):
        """Store an analytics record in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO analytics_records (
                timestamp, record_type, user_id, session_id, data, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp.isoformat(),
                record.record_type.value,
                record.user_id,
                record.session_id,
                json.dumps(record.data),
                json.dumps(record.metadata) if record.metadata else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store analytics record: {e}")
    
    def _check_trading_alerts(self, metrics: TradingMetrics):
        """Check for trading alerts based on thresholds"""
        alerts = []
        
        # Check profit/loss threshold
        profit_loss_threshold = self.config.alert_thresholds.get('profit_loss_percent', 10.0)
        if abs(metrics.profit_loss_percent) > profit_loss_threshold:
            alerts.append({
                'type': 'trading',
                'severity': 'high' if metrics.profit_loss_percent < 0 else 'info',
                'message': f"Profit/Loss threshold exceeded: {metrics.profit_loss_percent:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check trade volume change
        if AnalyticsType.TRADING in self.last_updates:
            last_metrics = self.cached_metrics[AnalyticsType.TRADING]
            if last_metrics.trade_volume > 0:
                volume_change = ((metrics.trade_volume - last_metrics.trade_volume) / 
                                last_metrics.trade_volume * 100)
                volume_threshold = self.config.alert_thresholds.get('trade_volume_change', 50.0)
                
                if abs(volume_change) > volume_threshold:
                    alerts.append({
                        'type': 'trading',
                        'severity': 'medium',
                        'message': f"Trade volume changed by {volume_change:.2f}%",
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Process alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert['message']}")
            # In a real system, you would send these alerts via email, Slack, etc.
    
    def _check_user_alerts(self, metrics: UserMetrics):
        """Check for user alerts based on thresholds"""
        alerts = []
        
        # Check user activity drop
        if AnalyticsType.USER in self.last_updates:
            last_metrics = self.cached_metrics[AnalyticsType.USER]
            if last_metrics.active_users > 0:
                activity_change = ((metrics.active_users - last_metrics.active_users) / 
                                  last_metrics.active_users * 100)
                activity_threshold = self.config.alert_thresholds.get('user_activity_drop', 30.0)
                
                if activity_change < -activity_threshold:
                    alerts.append({
                        'type': 'user',
                        'severity': 'high',
                        'message': f"User activity dropped by {abs(activity_change):.2f}%",
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Process alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert['message']}")
            # In a real system, you would send these alerts via email, Slack, etc.
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system alerts based on thresholds"""
        alerts = []
        
        # Check CPU usage
        cpu_threshold = self.config.alert_thresholds.get('system_cpu_usage', 80.0)
        if metrics.cpu_usage > cpu_threshold:
            alerts.append({
                'type': 'system',
                'severity': 'high',
                'message': f"CPU usage is high: {metrics.cpu_usage:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check memory usage
        memory_threshold = self.config.alert_thresholds.get('system_memory_usage', 80.0)
        if metrics.memory_usage > memory_threshold:
            alerts.append({
                'type': 'system',
                'severity': 'high',
                'message': f"Memory usage is high: {metrics.memory_usage:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check error rate
        if metrics.error_rate > 5.0:  # 5% error rate threshold
            alerts.append({
                'type': 'system',
                'severity': 'high',
                'message': f"Error rate is high: {metrics.error_rate:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Process alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert['message']}")
            # In a real system, you would send these alerts via email, Slack, etc.
    
    def _check_financial_alerts(self, metrics: FinancialMetrics):
        """Check for financial alerts based on thresholds"""
        alerts = []
        
        # Check MRR change
        if AnalyticsType.FINANCIAL in self.last_updates:
            last_metrics = self.cached_metrics[AnalyticsType.FINANCIAL]
            if last_metrics.mrr > 0:
                mrr_change = ((metrics.mrr - last_metrics.mrr) / last_metrics.mrr * 100)
                
                if mrr_change < -10.0:  # 10% MRR drop threshold
                    alerts.append({
                        'type': 'financial',
                        'severity': 'high',
                        'message': f"MRR dropped by {abs(mrr_change):.2f}%",
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Check churn rate
        if metrics.churn_rate > 10.0:  # 10% churn rate threshold
            alerts.append({
                'type': 'financial',
                'severity': 'high',
                'message': f"Churn rate is high: {metrics.churn_rate:.2f}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Process alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert['message']}")
            # In a real system, you would send these alerts via email, Slack, etc.
    
    def _check_report_schedule(self):
        """Check if reports need to be generated based on schedule"""
        # In a real implementation, this would check the cron-like schedule
        # For now, we'll just check if it's been a day since the last report
        
        last_report_time = self._get_last_report_time()
        if last_report_time is None or (datetime.now() - last_report_time).days >= 1:
            self.generate_reports()
    
    def _get_last_report_time(self) -> Optional[datetime]:
        """Get the timestamp of the last generated report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT timestamp FROM reports ORDER BY timestamp DESC LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return datetime.fromisoformat(result[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get last report time: {e}")
            return None
    
    def _cleanup_old_data(self):
        """Clean up old analytics data based on retention policy"""
        if self.config.data_retention_days <= 0:
            return  # No cleanup if retention is disabled
        
        try:
            retention_date = datetime.now() - timedelta(days=self.config.data_retention_days)
            retention_date_str = retention_date.isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old records from all tables
            tables = [
                'analytics_records',
                'trading_metrics',
                'user_metrics',
                'system_metrics',
                'financial_metrics'
            ]
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (retention_date_str,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up data older than {retention_date_str}")
            
        except Exception as e:
            self.logger.error(f"Failed to clean up old data: {e}")
    
    def generate_reports(self, report_types: List[AnalyticsType] = None, 
                        time_frame: TimeFrame = TimeFrame.DAILY):
        """Generate analytics reports"""
        if not self.config.enabled:
            return []
        
        if report_types is None:
            report_types = list(AnalyticsType)
        
        report_files = []
        
        try:
            for report_type in report_types:
                report_file = self._generate_report(report_type, time_frame)
                if report_file:
                    report_files.append(report_file)
                    
                    # Store report metadata in database
                    self._store_report_metadata(report_type, time_frame, report_file)
            
            self.logger.info(f"Generated {len(report_files)} reports")
            return report_files
            
        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")
            return []
    
    def _generate_report(self, report_type: AnalyticsType, time_frame: TimeFrame) -> Optional[str]:
        """Generate a specific report"""
        try:
            # Get time range for the report
            start_date, end_date = self._get_time_range(time_frame)
            
            # Get data for the report
            data = self._get_report_data(report_type, start_date, end_date)
            if not data:
                self.logger.warning(f"No data for {report_type.value} report in {time_frame.value} time frame")
                return None
            
            # Create report file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{report_type.value}_{time_frame.value}_{timestamp}.json"
            file_path = self.export_dir / file_name
            
            # Write report data to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Generated {report_type.value} report: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate {report_type.value} report: {e}")
            return None
    
    def _get_time_range(self, time_frame: TimeFrame) -> Tuple[datetime, datetime]:
        """Get start and end dates for a time frame"""
        end_date = datetime.now()
        
        if time_frame == TimeFrame.HOURLY:
            start_date = end_date - timedelta(hours=1)
        elif time_frame == TimeFrame.DAILY:
            start_date = end_date - timedelta(days=1)
        elif time_frame == TimeFrame.WEEKLY:
            start_date = end_date - timedelta(weeks=1)
        elif time_frame == TimeFrame.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif time_frame == TimeFrame.QUARTERLY:
            start_date = end_date - timedelta(days=90)
        elif time_frame == TimeFrame.YEARLY:
            start_date = end_date - timedelta(days=365)
        else:  # CUSTOM or fallback
            start_date = end_date - timedelta(days=7)  # Default to 7 days
        
        return start_date, end_date
    
    def _get_report_data(self, report_type: AnalyticsType, 
                        start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get data for a specific report type and time range"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()
            
            if report_type == AnalyticsType.TRADING:
                cursor.execute("""
                SELECT * FROM trading_metrics 
                WHERE timestamp BETWEEN ? AND ? 
                ORDER BY timestamp
                """, (start_date_str, end_date_str))
            
            elif report_type == AnalyticsType.USER:
                cursor.execute("""
                SELECT * FROM user_metrics 
                WHERE timestamp BETWEEN ? AND ? 
                ORDER BY timestamp
                """, (start_date_str, end_date_str))
            
            elif report_type == AnalyticsType.SYSTEM:
                cursor.execute("""
                SELECT * FROM system_metrics 
                WHERE timestamp BETWEEN ? AND ? 
                ORDER BY timestamp
                """, (start_date_str, end_date_str))
            
            elif report_type == AnalyticsType.FINANCIAL:
                cursor.execute("""
                SELECT * FROM financial_metrics 
                WHERE timestamp BETWEEN ? AND ? 
                ORDER BY timestamp
                """, (start_date_str, end_date_str))
            
            else:  # Generic analytics records
                cursor.execute("""
                SELECT * FROM analytics_records 
                WHERE record_type = ? AND timestamp BETWEEN ? AND ? 
                ORDER BY timestamp
                """, (report_type.value, start_date_str, end_date_str))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert rows to list of dictionaries
            data = [dict(row) for row in rows]
            
            # Add summary statistics
            summary = self._calculate_summary_statistics(data, report_type)
            
            return {
                'report_type': report_type.value,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'generated_at': datetime.now().isoformat(),
                'summary': summary,
                'data': data
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get report data: {e}")
            return {}
    
    def _calculate_summary_statistics(self, data: List[Dict], 
                                    report_type: AnalyticsType) -> Dict[str, Any]:
        """Calculate summary statistics for report data"""
        if not data:
            return {}
        
        summary = {
            'count': len(data),
            'first_timestamp': data[0]['timestamp'],
            'last_timestamp': data[-1]['timestamp']
        }
        
        # Calculate specific statistics based on report type
        if report_type == AnalyticsType.TRADING:
            # Extract numeric columns for statistics
            numeric_columns = [
                'total_trades', 'successful_trades', 'failed_trades',
                'profit_loss', 'profit_loss_percent', 'trade_volume',
                'win_loss_ratio', 'sharpe_ratio', 'max_drawdown'
            ]
            
            for column in numeric_columns:
                values = [float(row[column]) for row in data if column in row]
                if values:
                    summary[f'{column}_avg'] = sum(values) / len(values)
                    summary[f'{column}_min'] = min(values)
                    summary[f'{column}_max'] = max(values)
        
        elif report_type == AnalyticsType.USER:
            # Calculate user growth
            if len(data) >= 2:
                first_total = data[0]['total_users']
                last_total = data[-1]['total_users']
                if first_total > 0:
                    growth_percent = ((last_total - first_total) / first_total) * 100
                    summary['user_growth_percent'] = growth_percent
            
            # Average active users
            active_users = [row['active_users'] for row in data if 'active_users' in row]
            if active_users:
                summary['average_active_users'] = sum(active_users) / len(active_users)
        
        elif report_type == AnalyticsType.SYSTEM:
            # Average system metrics
            for column in ['cpu_usage', 'memory_usage', 'disk_usage', 'response_time', 'error_rate']:
                values = [float(row[column]) for row in data if column in row]
                if values:
                    summary[f'average_{column}'] = sum(values) / len(values)
                    summary[f'max_{column}'] = max(values)
        
        elif report_type == AnalyticsType.FINANCIAL:
            # Calculate revenue growth
            if len(data) >= 2:
                first_revenue = data[0]['total_revenue']
                last_revenue = data[-1]['total_revenue']
                if first_revenue > 0:
                    growth_percent = ((last_revenue - first_revenue) / first_revenue) * 100
                    summary['revenue_growth_percent'] = growth_percent
            
            # Total profit
            profits = [row['profit'] for row in data if 'profit' in row]
            if profits:
                summary['total_profit'] = sum(profits)
                summary['average_profit'] = sum(profits) / len(profits)
        
        return summary
    
    def _store_report_metadata(self, report_type: AnalyticsType, 
                             time_frame: TimeFrame, file_path: str):
        """Store report metadata in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO reports (
                timestamp, report_type, time_frame, file_path, metadata
            ) VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                report_type.value,
                time_frame.value,
                file_path,
                json.dumps({
                    'generated_by': 'analytics_system',
                    'version': '1.0'
                })
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store report metadata: {e}")
    
    def export_data(self, data_type: AnalyticsType, start_date: datetime, 
                   end_date: datetime, format: ExportFormat = ExportFormat.CSV) -> Optional[str]:
        """Export analytics data to a file"""
        try:
            # Get data
            data = self._get_report_data(data_type, start_date, end_date)
            if not data or not data.get('data'):
                self.logger.warning(f"No data to export for {data_type.value}")
                return None
            
            # Create export file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"export_{data_type.value}_{timestamp}.{format.value}"
            file_path = self.export_dir / file_name
            
            # Export based on format
            if format == ExportFormat.CSV:
                self._export_to_csv(data['data'], file_path)
            elif format == ExportFormat.JSON:
                self._export_to_json(data, file_path)
            elif format == ExportFormat.EXCEL:
                self._export_to_excel(data['data'], file_path)
            else:
                self.logger.warning(f"Unsupported export format: {format.value}")
                return None
            
            self.logger.info(f"Exported {data_type.value} data to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return None
    
    def _export_to_csv(self, data: List[Dict], file_path: str):
        """Export data to CSV file"""
        if not data:
            return
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _export_to_json(self, data: Dict, file_path: str):
        """Export data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _export_to_excel(self, data: List[Dict], file_path: str):
        """Export data to Excel file"""
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
    
    def generate_visualizations(self, data_type: AnalyticsType, 
                              start_date: datetime, end_date: datetime) -> List[str]:
        """Generate visualizations for analytics data"""
        try:
            # Get data
            data = self._get_report_data(data_type, start_date, end_date)
            if not data or not data.get('data'):
                self.logger.warning(f"No data for visualizations for {data_type.value}")
                return []
            
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame(data['data'])
            
            # Create timestamp for file names
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate visualizations based on data type
            visualization_files = []
            
            if data_type == AnalyticsType.TRADING:
                # Time series of profit/loss
                if 'profit_loss' in df.columns and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    plt.figure(figsize=(12, 6))
                    plt.plot(df['timestamp'], df['profit_loss'])
                    plt.title('Profit/Loss Over Time')
                    plt.xlabel('Date')
                    plt.ylabel('Profit/Loss')
                    plt.grid(True)
                    
                    file_name = f"viz_trading_profit_loss_{timestamp}.png"
                    file_path = self.export_dir / file_name
                    plt.savefig(file_path)
                    plt.close()
                    
                    visualization_files.append(str(file_path))
                
                # Win/loss ratio over time
                if 'win_loss_ratio' in df.columns and 'timestamp' in df.columns:
                    plt.figure(figsize=(12, 6))
                    plt.plot(df['timestamp'], df['win_loss_ratio'])
                    plt.title('Win/Loss Ratio Over Time')
                    plt.xlabel('Date')
                    plt.ylabel('Ratio')
                    plt.grid(True)
                    
                    file_name = f"viz_trading_win_loss_ratio_{timestamp}.png"
                    file_path = self.export_dir / file_name
                    plt.savefig(file_path)
                    plt.close()
                    
                    visualization_files.append(str(file_path))
            
            elif data_type == AnalyticsType.USER:
                # User growth over time
                if 'total_users' in df.columns and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    plt.figure(figsize=(12, 6))
                    plt.plot(df['timestamp'], df['total_users'], label='Total Users')
                    if 'active_users' in df.columns:
                        plt.plot(df['timestamp'], df['active_users'], label='Active Users')
                    plt.title('User Growth Over Time')
                    plt.xlabel('Date')
                    plt.ylabel('Users')
                    plt.legend()
                    plt.grid(True)
                    
                    file_name = f"viz_user_growth_{timestamp}.png"
                    file_path = self.export_dir / file_name
                    plt.savefig(file_path)
                    plt.close()
                    
                    visualization_files.append(str(file_path))
            
            elif data_type == AnalyticsType.SYSTEM:
                # System metrics over time
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
                    metrics = [m for m in metrics if m in df.columns]
                    
                    if metrics:
                        plt.figure(figsize=(12, 6))
                        for metric in metrics:
                            plt.plot(df['timestamp'], df[metric], label=metric)
                        plt.title('System Metrics Over Time')
                        plt.xlabel('Date')
                        plt.ylabel('Usage (%)')
                        plt.legend()
                        plt.grid(True)
                        
                        file_name = f"viz_system_metrics_{timestamp}.png"
                        file_path = self.export_dir / file_name
                        plt.savefig(file_path)
                        plt.close()
                        
                        visualization_files.append(str(file_path))
            
            elif data_type == AnalyticsType.FINANCIAL:
                # Revenue breakdown
                revenue_columns = ['subscription_revenue', 'transaction_revenue', 'other_revenue']
                revenue_columns = [c for c in revenue_columns if c in df.columns]
                
                if revenue_columns and len(df) > 0:
                    # Use the latest data point for the pie chart
                    latest = df.iloc[-1]
                    values = [latest[c] for c in revenue_columns]
                    
                    plt.figure(figsize=(10, 8))
                    plt.pie(values, labels=revenue_columns, autopct='%1.1f%%')
                    plt.title('Revenue Breakdown')
                    
                    file_name = f"viz_financial_revenue_breakdown_{timestamp}.png"
                    file_path = self.export_dir / file_name
                    plt.savefig(file_path)
                    plt.close()
                    
                    visualization_files.append(str(file_path))
            
            self.logger.info(f"Generated {len(visualization_files)} visualizations")
            return visualization_files
            
        except Exception as e:
            self.logger.error(f"Failed to generate visualizations: {e}")
            return []
    
    def analyze_user_behavior(self) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        if not self.config.enabled or not self.config.track_user_behavior:
            return {}
        
        try:
            # Get user behavior data from the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user events
            cursor.execute("""
            SELECT user_id, data, timestamp FROM analytics_records 
            WHERE record_type = 'user' AND timestamp BETWEEN ? AND ?
            """, (start_date.isoformat(), end_date.isoformat()))
            
            events = cursor.fetchall()
            conn.close()
            
            if not events:
                return {'message': 'No user behavior data available'}
            
            # Analyze patterns
            user_sessions = defaultdict(list)
            event_counts = Counter()
            hourly_activity = defaultdict(int)
            
            for user_id, data_json, timestamp in events:
                try:
                    data = json.loads(data_json)
                    event_type = data.get('event_type', 'unknown')
                    
                    user_sessions[user_id].append({
                        'event_type': event_type,
                        'timestamp': timestamp,
                        'data': data
                    })
                    
                    event_counts[event_type] += 1
                    
                    # Extract hour for activity analysis
                    dt = datetime.fromisoformat(timestamp)
                    hourly_activity[dt.hour] += 1
                    
                except json.JSONDecodeError:
                    continue
            
            # Calculate insights
            total_users = len(user_sessions)
            total_events = sum(event_counts.values())
            most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0
            
            # User segmentation
            user_segments = {
                'highly_active': 0,  # >50 events
                'moderately_active': 0,  # 10-50 events
                'low_active': 0  # <10 events
            }
            
            for user_id, sessions in user_sessions.items():
                event_count = len(sessions)
                if event_count > 50:
                    user_segments['highly_active'] += 1
                elif event_count >= 10:
                    user_segments['moderately_active'] += 1
                else:
                    user_segments['low_active'] += 1
            
            return {
                'analysis_period': f"{start_date.date()} to {end_date.date()}",
                'total_users_analyzed': total_users,
                'total_events': total_events,
                'average_events_per_user': total_events / total_users if total_users > 0 else 0,
                'most_common_events': dict(event_counts.most_common(10)),
                'most_active_hour': most_active_hour,
                'hourly_activity_distribution': dict(hourly_activity),
                'user_segments': user_segments,
                'insights': self._generate_behavior_insights(user_sessions, event_counts, hourly_activity)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze user behavior: {e}")
            return {'error': str(e)}
    
    def _generate_behavior_insights(self, user_sessions: Dict, event_counts: Counter, 
                                  hourly_activity: Dict) -> List[str]:
        """Generate insights from user behavior analysis"""
        insights = []
        
        # Most popular features
        if event_counts:
            top_event = event_counts.most_common(1)[0]
            insights.append(f"Most popular feature: {top_event[0]} ({top_event[1]} uses)")
        
        # Peak activity time
        if hourly_activity:
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0]
            insights.append(f"Peak activity time: {peak_hour}:00-{peak_hour+1}:00")
        
        # User engagement patterns
        session_lengths = [len(sessions) for sessions in user_sessions.values()]
        if session_lengths:
            avg_session_length = sum(session_lengths) / len(session_lengths)
            insights.append(f"Average user engagement: {avg_session_length:.1f} events per user")
        
        return insights
    
    def predict_user_churn(self) -> Dict[str, Any]:
        """Predict user churn using machine learning"""
        if not self.config.enable_machine_learning:
            return {'message': 'Machine learning is disabled'}
        
        try:
            # Get user activity data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)  # 60 days of data
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user metrics over time
            cursor.execute("""
            SELECT user_id, COUNT(*) as event_count, 
                   MAX(timestamp) as last_activity,
                   MIN(timestamp) as first_activity
            FROM analytics_records 
            WHERE record_type = 'user' AND timestamp BETWEEN ? AND ?
            GROUP BY user_id
            """, (start_date.isoformat(), end_date.isoformat()))
            
            user_data = cursor.fetchall()
            conn.close()
            
            if len(user_data) < 10:  # Need minimum data for ML
                return {'message': 'Insufficient data for churn prediction'}
            
            # Prepare features for ML model
            features = []
            labels = []
            user_ids = []
            
            for user_id, event_count, last_activity, first_activity in user_data:
                # Calculate features
                last_activity_dt = datetime.fromisoformat(last_activity)
                first_activity_dt = datetime.fromisoformat(first_activity)
                
                days_since_last_activity = (end_date - last_activity_dt).days
                total_activity_days = (last_activity_dt - first_activity_dt).days + 1
                activity_frequency = event_count / max(total_activity_days, 1)
                
                features.append([
                    event_count,
                    days_since_last_activity,
                    total_activity_days,
                    activity_frequency
                ])
                
                # Label as churned if no activity in last 14 days
                labels.append(1 if days_since_last_activity > 14 else 0)
                user_ids.append(user_id)
            
            # Train simple model (in production, use more sophisticated models)
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
            
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Predict churn for all users
            churn_probabilities = model.predict_proba(X)[:, 1]  # Probability of churn
            
            # Identify high-risk users
            high_risk_users = []
            for i, (user_id, prob) in enumerate(zip(user_ids, churn_probabilities)):
                if prob > 0.7:  # High churn probability threshold
                    high_risk_users.append({
                        'user_id': user_id,
                        'churn_probability': float(prob),
                        'event_count': features[i][0],
                        'days_since_last_activity': features[i][1]
                    })
            
            return {
                'model_accuracy': float(accuracy),
                'total_users_analyzed': len(user_ids),
                'high_risk_users_count': len(high_risk_users),
                'high_risk_users': sorted(high_risk_users, key=lambda x: x['churn_probability'], reverse=True)[:20],
                'churn_rate_prediction': float(np.mean(churn_probabilities)),
                'feature_importance': {
                    'event_count': float(model.feature_importances_[0]),
                    'days_since_last_activity': float(model.feature_importances_[1]),
                    'total_activity_days': float(model.feature_importances_[2]),
                    'activity_frequency': float(model.feature_importances_[3])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to predict user churn: {e}")
            return {'error': str(e)}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for analytics dashboard"""
        try:
            dashboard_data = {
                'last_updated': datetime.now().isoformat(),
                'metrics': {},
                'charts': {},
                'alerts': []
            }
            
            # Get current metrics
            for analytics_type in AnalyticsType:
                if analytics_type in self.cached_metrics:
                    dashboard_data['metrics'][analytics_type.value] = asdict(self.cached_metrics[analytics_type])
            
            # Get recent trends (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            for analytics_type in [AnalyticsType.TRADING, AnalyticsType.USER, AnalyticsType.SYSTEM]:
                trend_data = self._get_report_data(analytics_type, start_date, end_date)
                if trend_data and trend_data.get('data'):
                    dashboard_data['charts'][f'{analytics_type.value}_trend'] = trend_data['data'][-10:]  # Last 10 data points
            
            # Add system status
            dashboard_data['system_status'] = {
                'analytics_enabled': self.config.enabled,
                'collection_running': self.collection_thread and self.collection_thread.is_alive(),
                'last_collection': max(self.last_updates.values()) if self.last_updates else None,
                'database_size': self._get_database_size(),
                'total_records': self._get_total_records()
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}
    
    def _get_database_size(self) -> int:
        """Get the size of the analytics database in bytes"""
        try:
            return os.path.getsize(self.db_path)
        except:
            return 0
    
    def _get_total_records(self) -> int:
        """Get the total number of analytics records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analytics_records")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def get_metrics(self, analytics_type: AnalyticsType = None) -> Dict[str, Any]:
        """Get current metrics"""
        if analytics_type:
            return asdict(self.cached_metrics.get(analytics_type, {}))
        else:
            return {k.value: asdict(v) for k, v in self.cached_metrics.items()}
    
    def get_status(self) -> Dict[str, Any]:
        """Get analytics system status"""
        return {
            'enabled': self.config.enabled,
            'collection_running': self.collection_thread and self.collection_thread.is_alive(),
            'database_path': self.db_path,
            'export_directory': str(self.export_dir),
            'last_updates': {k.value: v.isoformat() for k, v in self.last_updates.items()},
            'data_retention_days': self.config.data_retention_days,
            'collection_interval_seconds': self.config.collection_interval_seconds,
            'database_size_bytes': self._get_database_size(),
            'total_records': self._get_total_records()
        }

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Pro Analytics System')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--start', action='store_true', help='Start analytics collection')
    parser.add_argument('--stop', action='store_true', help='Stop analytics collection')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--generate-reports', action='store_true', help='Generate reports')
    parser.add_argument('--export', choices=['csv', 'json', 'excel'], help='Export data format')
    parser.add_argument('--type', choices=[t.value for t in AnalyticsType], help='Analytics type')
    parser.add_argument('--days', type=int, default=7, help='Number of days for export/reports')
    
    args = parser.parse_args()
    
    # Initialize analytics system
    config = AnalyticsConfig()
    if args.config:
        # Load config from file (implementation depends on config format)
        pass
    
    analytics = AnalyticsSystem(config)
    
    try:
        if args.start:
            analytics.start_collection()
            print("Analytics collection started")
        
        elif args.stop:
            analytics.stop_collection()
            print("Analytics collection stopped")
        
        elif args.status:
            status = analytics.get_status()
            print(json.dumps(status, indent=2))
        
        elif args.generate_reports:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            report_types = [AnalyticsType(args.type)] if args.type else list(AnalyticsType)
            reports = analytics.generate_reports(report_types)
            print(f"Generated {len(reports)} reports:")
            for report in reports:
                print(f"  - {report}")
        
        elif args.export:
            if not args.type:
                print("Error: --type is required for export")
                return
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
            
            export_format = ExportFormat(args.export)
            analytics_type = AnalyticsType(args.type)
            
            file_path = analytics.export_data(analytics_type, start_date, end_date, export_format)
            if file_path:
                print(f"Data exported to: {file_path}")
            else:
                print("Export failed")
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        analytics.stop_collection()
    except Exception as e:
        print(f"Error: {e}")
        analytics.stop_collection()

if __name__ == '__main__':
    main()