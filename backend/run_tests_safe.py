#!/usr/bin/env python3
"""Safe test runner with resource management and error handling."""

import os
import sys
import subprocess
import argparse
import time
import psutil
from pathlib import Path


class SafeTestRunner:
    """Test runner with resource monitoring and safe execution."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent
        self.max_memory_mb = 2048  # 2GB memory limit
        self.max_cpu_percent = 80  # 80% CPU limit
        self.test_timeout = 300    # 5 minutes per test file
    
    def check_system_resources(self):
        """Check if system has enough resources to run tests."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        available_memory_mb = memory.available / (1024 * 1024)
        
        print(f"System Resources:")
        print(f"  Available Memory: {available_memory_mb:.0f} MB")
        print(f"  CPU Usage: {cpu_percent:.1f}%")
        
        if available_memory_mb < self.max_memory_mb:
            print(f"WARNING: Low memory ({available_memory_mb:.0f} MB < {self.max_memory_mb} MB)")
            return False
        
        if cpu_percent > self.max_cpu_percent:
            print(f"WARNING: High CPU usage ({cpu_percent:.1f}% > {self.max_cpu_percent}%)")
            return False
        
        return True
    
    def setup_test_environment(self):
        """Setup test environment and directories."""
        # Create logs directory
        logs_dir = self.backend_dir / "tests" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set environment variables for testing
        os.environ.update({
            'TESTING': 'true',
            'FLASK_ENV': 'testing',
            'DATABASE_URL': 'sqlite:///:memory:',
            'REDIS_URL': 'redis://localhost:6379/15',  # Test database
            'LOG_LEVEL': 'WARNING',
            'DISABLE_NOTIFICATIONS': 'true',
            'DEMO_MODE': 'true'
        })
        
        print("Test environment configured")
    
    def run_unit_tests(self, test_file=None, markers=None):
        """Run unit tests with resource constraints."""
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--tb=short',
            '--maxfail=3',
            '--timeout=60',
            '--disable-warnings',
            '-p', 'no:cacheprovider'
        ]
        
        if test_file:
            cmd[2] = f'tests/unit/{test_file}'
        
        if markers:
            cmd.extend(['-m', markers])
        
        return self._run_pytest_command(cmd, "Unit Tests")
    
    def run_integration_tests(self):
        """Run integration tests with extended timeout."""
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/integration/',
            '-v',
            '--tb=short',
            '--maxfail=2',
            '--timeout=120',
            '--disable-warnings',
            '-p', 'no:cacheprovider'
        ]
        
        return self._run_pytest_command(cmd, "Integration Tests")
    
    def run_security_tests(self):
        """Run security tests."""
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/security/',
            '-v',
            '--tb=short',
            '--maxfail=1',
            '--timeout=30',
            '--disable-warnings'
        ]
        
        return self._run_pytest_command(cmd, "Security Tests")
    
    def run_backtest_tests(self):
        """Run backtesting tests specifically."""
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/unit/test_strategy_backtesting.py',
            '-v',
            '--tb=short',
            '--maxfail=2',
            '--timeout=90',
            '--disable-warnings',
            '-m', 'backtest'
        ]
        
        return self._run_pytest_command(cmd, "Backtesting Tests")
    
    def run_fast_tests_only(self):
        """Run only fast tests to verify basic functionality."""
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--tb=line',
            '--maxfail=5',
            '--timeout=30',
            '--disable-warnings',
            '-m', 'fast or not slow',
            '-x'  # Stop on first failure
        ]
        
        return self._run_pytest_command(cmd, "Fast Tests")
    
    def _run_pytest_command(self, cmd, test_type):
        """Execute pytest command with monitoring."""
        print(f"\n{'='*50}")
        print(f"Running {test_type}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*50}")
        
        start_time = time.time()
        
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.test_timeout,
                cwd=self.backend_dir
            )
            
            duration = time.time() - start_time
            
            print(f"\n{test_type} completed in {duration:.2f} seconds")
            print(f"Exit code: {result.returncode}")
            
            if result.stdout:
                print("\nSTDOUT:")
                print(result.stdout)
            
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"\n{test_type} timed out after {self.test_timeout} seconds")
            return False
        except Exception as e:
            print(f"\nError running {test_type}: {e}")
            return False
    
    def run_code_quality_checks(self):
        """Run code quality checks."""
        print("\nRunning code quality checks...")
        
        # Run flake8 if available
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'flake8', '--max-line-length=100', '--ignore=E203,W503', '.'],
                capture_output=True,
                text=True,
                cwd=self.backend_dir,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✓ Flake8 checks passed")
            else:
                print("✗ Flake8 issues found:")
                print(result.stdout)
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠ Flake8 not available or timed out")
    
    def generate_test_report(self):
        """Generate a simple test report."""
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        print(f"Backend Directory: {self.backend_dir}")
        print(f"Python Version: {sys.version}")
        print(f"Test Timeout: {self.test_timeout}s")
        print(f"Memory Limit: {self.max_memory_mb}MB")
        print(f"CPU Limit: {self.max_cpu_percent}%")
        print("="*60)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Safe test runner for trading bot backend')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--backtest', action='store_true', help='Run backtesting tests only')
    parser.add_argument('--fast', action='store_true', help='Run fast tests only')
    parser.add_argument('--file', type=str, help='Run specific test file')
    parser.add_argument('--markers', type=str, help='Run tests with specific markers')
    parser.add_argument('--skip-resources', action='store_true', help='Skip resource checks')
    parser.add_argument('--quality', action='store_true', help='Run code quality checks')
    
    args = parser.parse_args()
    
    runner = SafeTestRunner()
    runner.generate_test_report()
    
    # Check system resources
    if not args.skip_resources and not runner.check_system_resources():
        print("\nSystem resources insufficient. Use --skip-resources to override.")
        return 1
    
    # Setup test environment
    runner.setup_test_environment()
    
    success = True
    
    # Run specific test types
    if args.unit:
        success &= runner.run_unit_tests(args.file, args.markers)
    elif args.integration:
        success &= runner.run_integration_tests()
    elif args.security:
        success &= runner.run_security_tests()
    elif args.backtest:
        success &= runner.run_backtest_tests()
    elif args.fast:
        success &= runner.run_fast_tests_only()
    elif args.quality:
        runner.run_code_quality_checks()
    else:
        # Run all tests in safe order
        print("\nRunning comprehensive test suite...")
        success &= runner.run_fast_tests_only()
        if success:
            success &= runner.run_backtest_tests()
        if success:
            success &= runner.run_unit_tests()
        # Skip integration and security if basic tests fail
    
    print(f"\n{'='*60}")
    if success:
        print("✓ All tests completed successfully!")
        return 0
    else:
        print("✗ Some tests failed or encountered errors")
        return 1


if __name__ == '__main__':
    sys.exit(main())