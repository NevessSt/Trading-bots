#!/usr/bin/env python3
"""
Backup and Recovery System for TradingBot Pro
Handles automated backups, data recovery, and system restoration
"""

import os
import json
import shutil
import sqlite3
import tarfile
import gzip
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import boto3
from botocore.exceptions import ClientError
import dropbox
from google.cloud import storage as gcs

class BackupType:
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    DATABASE = "database"
    CONFIG = "config"
    LOGS = "logs"

class BackupDestination:
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    DROPBOX = "dropbox"
    FTP = "ftp"

class BackupRecoverySystem:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_running = False
        self.scheduler_thread = None
        
        # Initialize backup directories
        self.backup_root = config.get('backup_root', 'backups')
        self.local_backup_dir = os.path.join(self.backup_root, 'local')
        self.temp_dir = os.path.join(self.backup_root, 'temp')
        
        # Create directories
        os.makedirs(self.local_backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize cloud storage clients
        self.cloud_clients = self._initialize_cloud_clients()
        
        # Backup metadata
        self.backup_metadata = {}
        self.metadata_file = os.path.join(self.backup_root, 'backup_metadata.json')
        self._load_metadata()
        
        # Setup backup schedule
        self._setup_backup_schedule()
    
    def _initialize_cloud_clients(self) -> Dict:
        """Initialize cloud storage clients"""
        clients = {}
        
        # AWS S3
        if 'aws' in self.config:
            try:
                clients['aws_s3'] = boto3.client(
                    's3',
                    aws_access_key_id=self.config['aws']['access_key'],
                    aws_secret_access_key=self.config['aws']['secret_key'],
                    region_name=self.config['aws'].get('region', 'us-east-1')
                )
                self.logger.info("AWS S3 client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS S3 client: {e}")
        
        # Google Cloud Storage
        if 'google_cloud' in self.config:
            try:
                clients['google_cloud'] = gcs.Client(
                    project=self.config['google_cloud']['project_id']
                )
                self.logger.info("Google Cloud Storage client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Cloud client: {e}")
        
        # Dropbox
        if 'dropbox' in self.config:
            try:
                clients['dropbox'] = dropbox.Dropbox(
                    self.config['dropbox']['access_token']
                )
                self.logger.info("Dropbox client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Dropbox client: {e}")
        
        return clients
    
    def _load_metadata(self):
        """Load backup metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    self.backup_metadata = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load backup metadata: {e}")
                self.backup_metadata = {}
    
    def _save_metadata(self):
        """Save backup metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.backup_metadata, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {e}")
    
    def _setup_backup_schedule(self):
        """Setup automated backup schedule"""
        backup_schedule = self.config.get('schedule', {})
        
        # Full backup schedule
        if 'full_backup' in backup_schedule:
            schedule.every().day.at(backup_schedule['full_backup']).do(
                self._scheduled_backup, BackupType.FULL
            )
        
        # Incremental backup schedule
        if 'incremental_backup' in backup_schedule:
            schedule.every(backup_schedule.get('incremental_interval', 6)).hours.do(
                self._scheduled_backup, BackupType.INCREMENTAL
            )
        
        # Database backup schedule
        if 'database_backup' in backup_schedule:
            schedule.every().hour.do(
                self._scheduled_backup, BackupType.DATABASE
            )
        
        # Config backup schedule
        if 'config_backup' in backup_schedule:
            schedule.every().day.do(
                self._scheduled_backup, BackupType.CONFIG
            )
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            self.backup_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("Backup scheduler started")
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        self.backup_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        self.logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.backup_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in backup scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _scheduled_backup(self, backup_type: str):
        """Execute scheduled backup"""
        try:
            self.logger.info(f"Starting scheduled {backup_type} backup")
            result = self.create_backup(backup_type)
            if result['success']:
                self.logger.info(f"Scheduled {backup_type} backup completed successfully")
            else:
                self.logger.error(f"Scheduled {backup_type} backup failed: {result.get('error')}")
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {e}")
    
    def create_backup(self, backup_type: str, destinations: List[str] = None) -> Dict:
        """Create a backup of specified type"""
        try:
            backup_id = self._generate_backup_id(backup_type)
            timestamp = datetime.utcnow()
            
            self.logger.info(f"Creating {backup_type} backup: {backup_id}")
            
            # Create backup based on type
            if backup_type == BackupType.FULL:
                backup_path = self._create_full_backup(backup_id)
            elif backup_type == BackupType.INCREMENTAL:
                backup_path = self._create_incremental_backup(backup_id)
            elif backup_type == BackupType.DIFFERENTIAL:
                backup_path = self._create_differential_backup(backup_id)
            elif backup_type == BackupType.DATABASE:
                backup_path = self._create_database_backup(backup_id)
            elif backup_type == BackupType.CONFIG:
                backup_path = self._create_config_backup(backup_id)
            elif backup_type == BackupType.LOGS:
                backup_path = self._create_logs_backup(backup_id)
            else:
                return {'success': False, 'error': f'Unknown backup type: {backup_type}'}
            
            if not backup_path:
                return {'success': False, 'error': 'Failed to create backup'}
            
            # Calculate backup size and checksum
            backup_size = os.path.getsize(backup_path)
            backup_checksum = self._calculate_checksum(backup_path)
            
            # Store backup metadata
            backup_info = {
                'id': backup_id,
                'type': backup_type,
                'timestamp': timestamp,
                'path': backup_path,
                'size': backup_size,
                'checksum': backup_checksum,
                'destinations': [],
                'status': 'completed'
            }
            
            # Upload to specified destinations
            destinations = destinations or self.config.get('default_destinations', ['local'])
            
            for destination in destinations:
                try:
                    if destination != 'local':
                        upload_result = self._upload_backup(backup_path, destination, backup_id)
                        if upload_result['success']:
                            backup_info['destinations'].append({
                                'type': destination,
                                'path': upload_result['path'],
                                'uploaded_at': datetime.utcnow()
                            })
                        else:
                            self.logger.error(f"Failed to upload to {destination}: {upload_result['error']}")
                    else:
                        backup_info['destinations'].append({
                            'type': 'local',
                            'path': backup_path,
                            'uploaded_at': timestamp
                        })
                except Exception as e:
                    self.logger.error(f"Failed to upload backup to {destination}: {e}")
            
            # Save metadata
            self.backup_metadata[backup_id] = backup_info
            self._save_metadata()
            
            # Cleanup old backups
            self._cleanup_old_backups(backup_type)
            
            self.logger.info(f"Backup {backup_id} created successfully")
            
            return {
                'success': True,
                'backup_id': backup_id,
                'path': backup_path,
                'size': backup_size,
                'destinations': backup_info['destinations']
            }
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_backup_id(self, backup_type: str) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"{backup_type}_{timestamp}"
    
    def _create_full_backup(self, backup_id: str) -> Optional[str]:
        """Create full system backup"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.tar.gz")
        
        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add application files
                app_dirs = self.config.get('backup_directories', [
                    'app.py', 'models.py', 'strategies', 'templates', 'static',
                    'config.py', 'requirements.txt'
                ])
                
                for item in app_dirs:
                    if os.path.exists(item):
                        tar.add(item, arcname=item)
                
                # Add database
                db_path = self.config.get('database_path', 'trading_bot.db')
                if os.path.exists(db_path):
                    tar.add(db_path, arcname='database.db')
                
                # Add user data
                user_data_dir = self.config.get('user_data_dir', 'user_data')
                if os.path.exists(user_data_dir):
                    tar.add(user_data_dir, arcname='user_data')
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create full backup: {e}")
            return None
    
    def _create_incremental_backup(self, backup_id: str) -> Optional[str]:
        """Create incremental backup (only changed files since last backup)"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.tar.gz")
        
        try:
            # Get last backup timestamp
            last_backup_time = self._get_last_backup_time(BackupType.INCREMENTAL)
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add only files modified since last backup
                for root, dirs, files in os.walk('.'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Skip backup directory and hidden files
                        if self.backup_root in file_path or file.startswith('.'):
                            continue
                        
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime > last_backup_time:
                                tar.add(file_path, arcname=file_path)
                        except OSError:
                            continue
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create incremental backup: {e}")
            return None
    
    def _create_differential_backup(self, backup_id: str) -> Optional[str]:
        """Create differential backup (changed files since last full backup)"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.tar.gz")
        
        try:
            # Get last full backup timestamp
            last_full_backup_time = self._get_last_backup_time(BackupType.FULL)
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add files modified since last full backup
                for root, dirs, files in os.walk('.'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if self.backup_root in file_path or file.startswith('.'):
                            continue
                        
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime > last_full_backup_time:
                                tar.add(file_path, arcname=file_path)
                        except OSError:
                            continue
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create differential backup: {e}")
            return None
    
    def _create_database_backup(self, backup_id: str) -> Optional[str]:
        """Create database backup"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.sql.gz")
        
        try:
            db_path = self.config.get('database_path', 'trading_bot.db')
            
            if not os.path.exists(db_path):
                self.logger.warning(f"Database file not found: {db_path}")
                return None
            
            # Create SQL dump
            with sqlite3.connect(db_path) as conn:
                with gzip.open(backup_path, 'wt') as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create database backup: {e}")
            return None
    
    def _create_config_backup(self, backup_id: str) -> Optional[str]:
        """Create configuration backup"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.tar.gz")
        
        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add configuration files
                config_files = self.config.get('config_files', [
                    'config.py', 'config.json', 'config.yaml',
                    '.env', 'docker-compose.yml', 'Dockerfile'
                ])
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        tar.add(config_file, arcname=config_file)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create config backup: {e}")
            return None
    
    def _create_logs_backup(self, backup_id: str) -> Optional[str]:
        """Create logs backup"""
        backup_path = os.path.join(self.local_backup_dir, f"{backup_id}.tar.gz")
        
        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add log files
                logs_dir = self.config.get('logs_dir', 'logs')
                if os.path.exists(logs_dir):
                    tar.add(logs_dir, arcname='logs')
                
                # Add individual log files
                log_files = ['app.log', 'error.log', 'trading.log', 'access.log']
                for log_file in log_files:
                    if os.path.exists(log_file):
                        tar.add(log_file, arcname=log_file)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create logs backup: {e}")
            return None
    
    def _get_last_backup_time(self, backup_type: str) -> datetime:
        """Get timestamp of last backup of specified type"""
        last_time = datetime.min
        
        for backup_id, backup_info in self.backup_metadata.items():
            if backup_info['type'] == backup_type:
                backup_time = backup_info['timestamp']
                if isinstance(backup_time, str):
                    backup_time = datetime.fromisoformat(backup_time)
                
                if backup_time > last_time:
                    last_time = backup_time
        
        return last_time
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _upload_backup(self, backup_path: str, destination: str, backup_id: str) -> Dict:
        """Upload backup to specified destination"""
        try:
            if destination == BackupDestination.AWS_S3:
                return self._upload_to_s3(backup_path, backup_id)
            elif destination == BackupDestination.GOOGLE_CLOUD:
                return self._upload_to_gcs(backup_path, backup_id)
            elif destination == BackupDestination.DROPBOX:
                return self._upload_to_dropbox(backup_path, backup_id)
            else:
                return {'success': False, 'error': f'Unknown destination: {destination}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_s3(self, backup_path: str, backup_id: str) -> Dict:
        """Upload backup to AWS S3"""
        try:
            s3_client = self.cloud_clients.get('aws_s3')
            if not s3_client:
                return {'success': False, 'error': 'S3 client not initialized'}
            
            bucket_name = self.config['aws']['bucket_name']
            s3_key = f"backups/{backup_id}/{os.path.basename(backup_path)}"
            
            s3_client.upload_file(backup_path, bucket_name, s3_key)
            
            return {
                'success': True,
                'path': f"s3://{bucket_name}/{s3_key}"
            }
            
        except ClientError as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_gcs(self, backup_path: str, backup_id: str) -> Dict:
        """Upload backup to Google Cloud Storage"""
        try:
            gcs_client = self.cloud_clients.get('google_cloud')
            if not gcs_client:
                return {'success': False, 'error': 'GCS client not initialized'}
            
            bucket_name = self.config['google_cloud']['bucket_name']
            bucket = gcs_client.bucket(bucket_name)
            
            blob_name = f"backups/{backup_id}/{os.path.basename(backup_path)}"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(backup_path)
            
            return {
                'success': True,
                'path': f"gs://{bucket_name}/{blob_name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_to_dropbox(self, backup_path: str, backup_id: str) -> Dict:
        """Upload backup to Dropbox"""
        try:
            dbx_client = self.cloud_clients.get('dropbox')
            if not dbx_client:
                return {'success': False, 'error': 'Dropbox client not initialized'}
            
            dropbox_path = f"/backups/{backup_id}/{os.path.basename(backup_path)}"
            
            with open(backup_path, 'rb') as f:
                dbx_client.files_upload(f.read(), dropbox_path)
            
            return {
                'success': True,
                'path': dropbox_path
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _cleanup_old_backups(self, backup_type: str):
        """Clean up old backups based on retention policy"""
        try:
            retention_config = self.config.get('retention', {})
            retention_days = retention_config.get(backup_type, 30)
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            backups_to_delete = []
            
            for backup_id, backup_info in self.backup_metadata.items():
                if backup_info['type'] == backup_type:
                    backup_time = backup_info['timestamp']
                    if isinstance(backup_time, str):
                        backup_time = datetime.fromisoformat(backup_time)
                    
                    if backup_time < cutoff_date:
                        backups_to_delete.append(backup_id)
            
            for backup_id in backups_to_delete:
                self._delete_backup(backup_id)
            
            if backups_to_delete:
                self.logger.info(f"Cleaned up {len(backups_to_delete)} old {backup_type} backups")
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
    
    def _delete_backup(self, backup_id: str):
        """Delete a backup and its metadata"""
        try:
            backup_info = self.backup_metadata.get(backup_id)
            if not backup_info:
                return
            
            # Delete local backup file
            if os.path.exists(backup_info['path']):
                os.remove(backup_info['path'])
            
            # Delete from cloud destinations
            for destination in backup_info.get('destinations', []):
                try:
                    self._delete_from_destination(destination, backup_id)
                except Exception as e:
                    self.logger.error(f"Failed to delete backup from {destination['type']}: {e}")
            
            # Remove from metadata
            del self.backup_metadata[backup_id]
            self._save_metadata()
            
            self.logger.info(f"Deleted backup: {backup_id}")
        
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
    
    def _delete_from_destination(self, destination: Dict, backup_id: str):
        """Delete backup from cloud destination"""
        dest_type = destination['type']
        dest_path = destination['path']
        
        if dest_type == BackupDestination.AWS_S3:
            s3_client = self.cloud_clients.get('aws_s3')
            if s3_client:
                # Parse S3 path
                s3_parts = dest_path.replace('s3://', '').split('/', 1)
                bucket_name = s3_parts[0]
                s3_key = s3_parts[1]
                s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        
        elif dest_type == BackupDestination.GOOGLE_CLOUD:
            gcs_client = self.cloud_clients.get('google_cloud')
            if gcs_client:
                # Parse GCS path
                gcs_parts = dest_path.replace('gs://', '').split('/', 1)
                bucket_name = gcs_parts[0]
                blob_name = gcs_parts[1]
                bucket = gcs_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
        
        elif dest_type == BackupDestination.DROPBOX:
            dbx_client = self.cloud_clients.get('dropbox')
            if dbx_client:
                dbx_client.files_delete_v2(dest_path)
    
    def restore_backup(self, backup_id: str, restore_path: str = None) -> Dict:
        """Restore from backup"""
        try:
            backup_info = self.backup_metadata.get(backup_id)
            if not backup_info:
                return {'success': False, 'error': f'Backup {backup_id} not found'}
            
            self.logger.info(f"Starting restore from backup: {backup_id}")
            
            # Download backup if not local
            local_backup_path = backup_info['path']
            
            if not os.path.exists(local_backup_path):
                # Try to download from cloud destinations
                download_result = self._download_backup(backup_info)
                if not download_result['success']:
                    return {'success': False, 'error': f'Failed to download backup: {download_result["error"]}'}
                local_backup_path = download_result['path']
            
            # Verify backup integrity
            if not self._verify_backup_integrity(local_backup_path, backup_info['checksum']):
                return {'success': False, 'error': 'Backup integrity check failed'}
            
            # Restore based on backup type
            restore_path = restore_path or self.config.get('restore_path', 'restore')
            
            if backup_info['type'] == BackupType.DATABASE:
                restore_result = self._restore_database(local_backup_path, restore_path)
            else:
                restore_result = self._restore_files(local_backup_path, restore_path)
            
            if restore_result['success']:
                self.logger.info(f"Backup {backup_id} restored successfully to {restore_path}")
            
            return restore_result
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _download_backup(self, backup_info: Dict) -> Dict:
        """Download backup from cloud destination"""
        for destination in backup_info.get('destinations', []):
            if destination['type'] != 'local':
                try:
                    download_result = self._download_from_destination(destination, backup_info['id'])
                    if download_result['success']:
                        return download_result
                except Exception as e:
                    self.logger.error(f"Failed to download from {destination['type']}: {e}")
                    continue
        
        return {'success': False, 'error': 'No available backup sources'}
    
    def _download_from_destination(self, destination: Dict, backup_id: str) -> Dict:
        """Download backup from specific destination"""
        dest_type = destination['type']
        dest_path = destination['path']
        
        local_path = os.path.join(self.temp_dir, f"{backup_id}_downloaded.tar.gz")
        
        try:
            if dest_type == BackupDestination.AWS_S3:
                s3_client = self.cloud_clients.get('aws_s3')
                if s3_client:
                    s3_parts = dest_path.replace('s3://', '').split('/', 1)
                    bucket_name = s3_parts[0]
                    s3_key = s3_parts[1]
                    s3_client.download_file(bucket_name, s3_key, local_path)
            
            elif dest_type == BackupDestination.GOOGLE_CLOUD:
                gcs_client = self.cloud_clients.get('google_cloud')
                if gcs_client:
                    gcs_parts = dest_path.replace('gs://', '').split('/', 1)
                    bucket_name = gcs_parts[0]
                    blob_name = gcs_parts[1]
                    bucket = gcs_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    blob.download_to_filename(local_path)
            
            elif dest_type == BackupDestination.DROPBOX:
                dbx_client = self.cloud_clients.get('dropbox')
                if dbx_client:
                    with open(local_path, 'wb') as f:
                        metadata, response = dbx_client.files_download(dest_path)
                        f.write(response.content)
            
            return {'success': True, 'path': local_path}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _verify_backup_integrity(self, backup_path: str, expected_checksum: str) -> bool:
        """Verify backup file integrity"""
        try:
            actual_checksum = self._calculate_checksum(backup_path)
            return actual_checksum == expected_checksum
        except Exception as e:
            self.logger.error(f"Failed to verify backup integrity: {e}")
            return False
    
    def _restore_database(self, backup_path: str, restore_path: str) -> Dict:
        """Restore database from backup"""
        try:
            db_restore_path = os.path.join(restore_path, 'restored_database.db')
            
            # Create restore directory
            os.makedirs(restore_path, exist_ok=True)
            
            # Restore from SQL dump
            with gzip.open(backup_path, 'rt') as f:
                sql_content = f.read()
            
            with sqlite3.connect(db_restore_path) as conn:
                conn.executescript(sql_content)
            
            return {
                'success': True,
                'restored_path': db_restore_path,
                'message': 'Database restored successfully'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _restore_files(self, backup_path: str, restore_path: str) -> Dict:
        """Restore files from backup"""
        try:
            # Create restore directory
            os.makedirs(restore_path, exist_ok=True)
            
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(path=restore_path)
            
            return {
                'success': True,
                'restored_path': restore_path,
                'message': 'Files restored successfully'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_backups(self, backup_type: str = None) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for backup_id, backup_info in self.backup_metadata.items():
            if backup_type is None or backup_info['type'] == backup_type:
                backup_summary = {
                    'id': backup_id,
                    'type': backup_info['type'],
                    'timestamp': backup_info['timestamp'],
                    'size': backup_info['size'],
                    'destinations': [d['type'] for d in backup_info.get('destinations', [])],
                    'status': backup_info.get('status', 'unknown')
                }
                backups.append(backup_summary)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def get_backup_status(self) -> Dict:
        """Get overall backup system status"""
        total_backups = len(self.backup_metadata)
        
        # Count by type
        type_counts = {}
        total_size = 0
        
        for backup_info in self.backup_metadata.values():
            backup_type = backup_info['type']
            type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
            total_size += backup_info.get('size', 0)
        
        # Get last backup times
        last_backups = {}
        for backup_type in [BackupType.FULL, BackupType.INCREMENTAL, BackupType.DATABASE]:
            last_time = self._get_last_backup_time(backup_type)
            if last_time != datetime.min:
                last_backups[backup_type] = last_time
        
        return {
            'total_backups': total_backups,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'backups_by_type': type_counts,
            'last_backups': last_backups,
            'scheduler_running': self.backup_running,
            'configured_destinations': list(self.cloud_clients.keys()) + ['local']
        }

if __name__ == "__main__":
    # Example configuration
    config = {
        'backup_root': 'backups',
        'database_path': 'trading_bot.db',
        'backup_directories': ['app.py', 'models.py', 'strategies', 'templates', 'static'],
        'config_files': ['config.py', 'config.json', '.env'],
        'logs_dir': 'logs',
        'schedule': {
            'full_backup': '02:00',  # 2 AM daily
            'incremental_interval': 6,  # Every 6 hours
        },
        'retention': {
            'full': 30,  # Keep for 30 days
            'incremental': 7,  # Keep for 7 days
            'database': 14,  # Keep for 14 days
        },
        'default_destinations': ['local'],
        'aws': {
            'access_key': 'your-access-key',
            'secret_key': 'your-secret-key',
            'bucket_name': 'tradingbot-backups',
            'region': 'us-east-1'
        }
    }
    
    # Initialize backup system
    backup_system = BackupRecoverySystem(config)
    
    # Start scheduler
    backup_system.start_scheduler()
    
    print("Backup system initialized")
    print("Status:", backup_system.get_backup_status())
    
    # Create a test backup
    result = backup_system.create_backup(BackupType.CONFIG)
    print("Backup result:", result)