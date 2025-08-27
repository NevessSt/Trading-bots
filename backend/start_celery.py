#!/usr/bin/env python3
"""
Celery startup script for development.
This script starts Redis, Celery worker, and Celery beat in separate processes.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

class CeleryManager:
    def __init__(self):
        self.processes = []
        self.redis_process = None
        self.worker_process = None
        self.beat_process = None
        self.flower_process = None
        
    def start_redis(self):
        """Start Redis server if not already running."""
        try:
            # Check if Redis is already running
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("✓ Redis is already running")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        try:
            print("Starting Redis server...")
            self.redis_process = subprocess.Popen(
                ['redis-server', '--port', '6379'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(self.redis_process)
            
            # Wait for Redis to start
            for i in range(10):
                try:
                    result = subprocess.run(['redis-cli', 'ping'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and 'PONG' in result.stdout:
                        print("✓ Redis started successfully")
                        return True
                except subprocess.TimeoutExpired:
                    pass
                time.sleep(1)
                
            print("✗ Failed to start Redis")
            return False
            
        except FileNotFoundError:
            print("✗ Redis not found. Please install Redis server.")
            print("  On Windows: Download from https://github.com/microsoftarchive/redis/releases")
            print("  On macOS: brew install redis")
            print("  On Ubuntu: sudo apt-get install redis-server")
            return False
            
    def start_worker(self):
        """Start Celery worker."""
        try:
            print("Starting Celery worker...")
            env = os.environ.copy()
            env['PYTHONPATH'] = str(backend_dir)
            
            self.worker_process = subprocess.Popen(
                [sys.executable, 'worker.py'],
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            self.processes.append(self.worker_process)
            print("✓ Celery worker started")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start Celery worker: {e}")
            return False
            
    def start_beat(self):
        """Start Celery beat scheduler."""
        try:
            print("Starting Celery beat scheduler...")
            env = os.environ.copy()
            env['PYTHONPATH'] = str(backend_dir)
            
            self.beat_process = subprocess.Popen(
                [sys.executable, 'beat.py'],
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            self.processes.append(self.beat_process)
            print("✓ Celery beat scheduler started")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start Celery beat: {e}")
            return False
            
    def start_flower(self):
        """Start Celery Flower monitoring (optional)."""
        try:
            print("Starting Celery Flower monitoring...")
            env = os.environ.copy()
            env['PYTHONPATH'] = str(backend_dir)
            
            self.flower_process = subprocess.Popen(
                ['celery', '-A', 'celery_app', 'flower', '--port=5555'],
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            self.processes.append(self.flower_process)
            print("✓ Celery Flower started at http://localhost:5555")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start Celery Flower: {e}")
            return False
            
    def stop_all(self):
        """Stop all processes."""
        print("\nStopping all processes...")
        
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    
        print("✓ All processes stopped")
        
    def run(self):
        """Run all Celery services."""
        print("=== Trading Bot Celery Services ===")
        print("Starting services...\n")
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            print("\nReceived interrupt signal")
            self.stop_all()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start services
            if not self.start_redis():
                return False
                
            time.sleep(2)  # Give Redis time to fully start
            
            if not self.start_worker():
                return False
                
            if not self.start_beat():
                return False
                
            # Optionally start Flower
            if '--flower' in sys.argv:
                self.start_flower()
                
            print("\n=== All services started successfully ===")
            print("Services running:")
            print("  - Redis: localhost:6379")
            print("  - Celery Worker: Processing tasks")
            print("  - Celery Beat: Scheduling periodic tasks")
            if '--flower' in sys.argv:
                print("  - Flower Monitoring: http://localhost:5555")
            print("\nPress Ctrl+C to stop all services")
            
            # Keep the script running
            while True:
                time.sleep(1)
                # Check if any process died
                for process in self.processes:
                    if process and process.poll() is not None:
                        print(f"\n✗ Process {process.pid} died unexpectedly")
                        self.stop_all()
                        return False
                        
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop_all()
            return True
        except Exception as e:
            print(f"\n✗ Error: {e}")
            self.stop_all()
            return False

if __name__ == '__main__':
    manager = CeleryManager()
    success = manager.run()
    sys.exit(0 if success else 1)