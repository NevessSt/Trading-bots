#!/usr/bin/env python3
"""
TradingBot Pro - Test Runner
Comprehensive test suite for all components
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        
    def run_command(self, command, description):
        """Run a command and capture results"""
        print(f"\n🧪 {description}...")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {description} passed ({duration:.2f}s)")
                self.test_results[description] = {'status': 'PASSED', 'duration': duration}
                return True
            else:
                print(f"❌ {description} failed ({duration:.2f}s)")
                print(f"Error: {result.stderr}")
                self.test_results[description] = {'status': 'FAILED', 'duration': duration, 'error': result.stderr}
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {description} failed with exception ({duration:.2f}s)")
            print(f"Exception: {str(e)}")
            self.test_results[description] = {'status': 'ERROR', 'duration': duration, 'error': str(e)}
            return False
    
    def check_environment(self):
        """Check if test environment is properly set up"""
        print("🔍 Checking test environment...")
        
        # Check if virtual environment is activated
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ Virtual environment detected")
        else:
            print("⚠️  Virtual environment not detected")
        
        # Check if .env file exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            print("✅ .env file found")
        else:
            print("⚠️  .env file not found")
        
        # Check if required directories exist
        required_dirs = ['backend', 'tests']
        for dir_name in required_dirs:
            if (self.project_root / dir_name).exists():
                print(f"✅ {dir_name} directory found")
            else:
                print(f"⚠️  {dir_name} directory not found")
    
    def run_unit_tests(self):
        """Run unit tests using pytest"""
        commands = [
            ("python -m pytest tests/unit/ -v --tb=short", "Unit Tests"),
            ("python -m pytest tests/unit/ --cov=backend --cov-report=term-missing", "Unit Tests with Coverage")
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_integration_tests(self):
        """Run integration tests"""
        commands = [
            ("python -m pytest tests/integration/ -v --tb=short", "Integration Tests"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_api_tests(self):
        """Run API endpoint tests"""
        commands = [
            ("python -m pytest tests/api/ -v --tb=short", "API Tests"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_security_tests(self):
        """Run security tests"""
        commands = [
            ("python -m bandit -r backend/ -f json", "Security Scan (Bandit)"),
            ("python -m safety check --json", "Dependency Security Check (Safety)"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_code_quality_tests(self):
        """Run code quality checks"""
        commands = [
            ("python -m flake8 backend/ --max-line-length=100 --ignore=E203,W503", "Code Style (Flake8)"),
            ("python -m black --check backend/", "Code Formatting (Black)"),
            ("python -m isort --check-only backend/", "Import Sorting (isort)"),
            ("python -m mypy backend/ --ignore-missing-imports", "Type Checking (MyPy)"),
            ("python -m pylint backend/ --disable=C0114,C0115,C0116", "Code Analysis (Pylint)"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_performance_tests(self):
        """Run performance tests"""
        commands = [
            ("python -m pytest tests/performance/ -v --tb=short", "Performance Tests"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def run_docker_tests(self):
        """Run Docker-related tests"""
        commands = [
            ("docker-compose -f docker-compose.yml config", "Docker Compose Configuration"),
            ("docker build -t tradingbot-test --target testing .", "Docker Build Test"),
        ]
        
        for command, description in commands:
            self.run_command(command, description)
    
    def create_test_files(self):
        """Create basic test files if they don't exist"""
        test_dirs = [
            'tests/unit',
            'tests/integration',
            'tests/api',
            'tests/performance'
        ]
        
        # Create test directories
        for test_dir in test_dirs:
            (self.project_root / test_dir).mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            init_file = self.project_root / test_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
        
        # Create basic test files
        test_files = {
            'tests/conftest.py': '''
"""Pytest configuration and fixtures"""
import pytest
import os
from backend.app import create_app
from backend.database import db

@pytest.fixture
def app():
    """Create application for testing"""
    os.environ['TESTING'] = 'True'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()
''',
            'tests/unit/test_trading_engine.py': '''
"""Unit tests for TradingEngine"""
import pytest
from unittest.mock import Mock, patch
from backend.bot_engine.trading_engine import TradingEngine

class TestTradingEngine:
    def test_init(self):
        """Test TradingEngine initialization"""
        engine = TradingEngine()
        assert engine is not None
        assert hasattr(engine, 'active_bots')
    
    @patch('backend.bot_engine.trading_engine.ccxt')
    def test_get_active_bots(self, mock_ccxt):
        """Test getting active bots"""
        engine = TradingEngine()
        bots = engine.get_active_bots()
        assert isinstance(bots, list)
''',
            'tests/unit/test_strategies.py': '''
"""Unit tests for trading strategies"""
import pytest
from backend.strategies.rsi_strategy import RSIStrategy
from backend.strategies.macd_strategy import MACDStrategy

class TestRSIStrategy:
    def test_init(self):
        """Test RSI strategy initialization"""
        strategy = RSIStrategy()
        assert strategy is not None
    
    def test_generate_signal(self):
        """Test signal generation"""
        strategy = RSIStrategy()
        # Mock data would be needed here
        pass

class TestMACDStrategy:
    def test_init(self):
        """Test MACD strategy initialization"""
        strategy = MACDStrategy()
        assert strategy is not None
''',
            'tests/api/test_auth.py': '''
"""API tests for authentication"""
import pytest
import json

class TestAuthAPI:
    def test_register(self, client):
        """Test user registration"""
        response = client.post('/api/auth/register', 
                             json={'username': 'test', 'password': 'test123'})
        # Add assertions based on your API response
        pass
    
    def test_login(self, client):
        """Test user login"""
        response = client.post('/api/auth/login',
                             json={'username': 'test', 'password': 'test123'})
        # Add assertions based on your API response
        pass
''',
            'tests/integration/test_bot_lifecycle.py': '''
"""Integration tests for bot lifecycle"""
import pytest
from backend.bot_engine.trading_engine import TradingEngine

class TestBotLifecycle:
    def test_start_stop_bot(self):
        """Test starting and stopping a bot"""
        engine = TradingEngine()
        # Add integration test logic
        pass
''',
            'tests/performance/test_performance.py': '''
"""Performance tests"""
import pytest
import time
from backend.bot_engine.trading_engine import TradingEngine

class TestPerformance:
    def test_bot_creation_performance(self):
        """Test bot creation performance"""
        engine = TradingEngine()
        start_time = time.time()
        
        # Performance test logic
        
        duration = time.time() - start_time
        assert duration < 1.0  # Should complete within 1 second
'''
        }
        
        for file_path, content in test_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                with open(full_path, 'w') as f:
                    f.write(content)
                print(f"Created: {file_path}")
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASSED')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAILED')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Errors: {error_tests} ⚠️")
        
        if failed_tests > 0 or error_tests > 0:
            print("\nFailed/Error Tests:")
            for test_name, result in self.test_results.items():
                if result['status'] in ['FAILED', 'ERROR']:
                    print(f"  - {test_name}: {result['status']}")
                    if 'error' in result:
                        print(f"    Error: {result['error'][:100]}...")
        
        total_duration = sum(result['duration'] for result in self.test_results.values())
        print(f"\nTotal Duration: {total_duration:.2f}s")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 All tests passed!")
        elif success_rate >= 80:
            print("\n👍 Most tests passed, but some issues need attention.")
        else:
            print("\n⚠️  Many tests failed. Please review and fix issues.")

def main():
    parser = argparse.ArgumentParser(description='TradingBot Pro Test Runner')
    parser.add_argument('--type', choices=['unit', 'integration', 'api', 'security', 'quality', 'performance', 'docker', 'all'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--create-files', action='store_true', help='Create basic test files')
    parser.add_argument('--check-env', action='store_true', help='Check test environment')
    
    args = parser.parse_args()
    runner = TestRunner()
    
    if args.create_files:
        runner.create_test_files()
        print("✅ Test files created")
        return
    
    if args.check_env:
        runner.check_environment()
        return
    
    print("🚀 Starting TradingBot Pro Test Suite")
    print(f"Test Type: {args.type}")
    
    if args.type in ['unit', 'all']:
        runner.run_unit_tests()
    
    if args.type in ['integration', 'all']:
        runner.run_integration_tests()
    
    if args.type in ['api', 'all']:
        runner.run_api_tests()
    
    if args.type in ['security', 'all']:
        runner.run_security_tests()
    
    if args.type in ['quality', 'all']:
        runner.run_code_quality_tests()
    
    if args.type in ['performance', 'all']:
        runner.run_performance_tests()
    
    if args.type in ['docker', 'all']:
        runner.run_docker_tests()
    
    runner.print_summary()

if __name__ == '__main__':
    main()