#!/usr/bin/env python
"""Enhanced test runner with comprehensive testing capabilities."""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class TestRunner:
    """Enhanced test runner for the trading bot application."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.test_dir = self.base_dir / 'tests'
        self.coverage_dir = self.base_dir / 'htmlcov'
        self.reports_dir = self.base_dir / 'test-results'
        
        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test environment variables
        self.test_env = {
            'FLASK_ENV': 'testing',
            'TESTING': 'True',
            'DATABASE_URL': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key',
            'JWT_SECRET_KEY': 'test-jwt-secret',
            'PYTHONPATH': str(self.base_dir),
            **os.environ
        }
    
    def run_command(self, cmd, description=""):
        """Run a command and return the result."""
        if description:
            print(f"\n{'='*60}")
            print(f"Running: {description}")
            print(f"Command: {' '.join(cmd)}")
            print(f"{'='*60}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                env=self.test_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            print(f"Command timed out: {' '.join(cmd)}")
            return False
        except Exception as e:
            print(f"Error running command: {e}")
            return False
    
    def install_dependencies(self):
        """Install test dependencies."""
        print("Installing test dependencies...")
        
        # Check if requirements-test.txt exists
        req_file = self.base_dir / 'requirements-test.txt'
        if not req_file.exists():
            print("requirements-test.txt not found, installing basic dependencies")
            basic_deps = [
                'pytest>=7.0.0',
                'pytest-cov>=4.0.0',
                'pytest-mock>=3.10.0',
                'flask-testing>=0.8.1'
            ]
            
            for dep in basic_deps:
                success = self.run_command(
                    [sys.executable, '-m', 'pip', 'install', dep],
                    f"Installing {dep}"
                )
                if not success:
                    print(f"Failed to install {dep}")
                    return False
        else:
            success = self.run_command(
                [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
                "Installing from requirements-test.txt"
            )
            if not success:
                print("Failed to install test dependencies")
                return False
        
        return True
    
    def run_unit_tests(self, verbose=False, coverage=True):
        """Run unit tests."""
        cmd = [sys.executable, '-m', 'pytest']
        
        # Test path
        unit_test_path = self.test_dir / 'unit'
        if unit_test_path.exists():
            cmd.append(str(unit_test_path))
        else:
            print("Unit test directory not found, running all tests")
            cmd.append(str(self.test_dir))
        
        # Coverage options
        if coverage:
            cmd.extend([
                '--cov=app',
                '--cov-report=html',
                '--cov-report=xml',
                '--cov-report=term-missing',
                f'--cov-report=html:{self.coverage_dir}'
            ])
        
        # Verbose output
        if verbose:
            cmd.append('-v')
        
        # JUnit XML output
        cmd.extend([
            '--junitxml=' + str(self.reports_dir / 'unit-tests.xml'),
            '--tb=short'
        ])
        
        # Markers
        cmd.extend(['-m', 'unit or not integration and not e2e'])
        
        return self.run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests."""
        cmd = [sys.executable, '-m', 'pytest']
        
        # Test path
        integration_test_path = self.test_dir / 'integration'
        if integration_test_path.exists():
            cmd.append(str(integration_test_path))
        else:
            cmd.extend([str(self.test_dir), '-m', 'integration'])
        
        # Verbose output
        if verbose:
            cmd.append('-v')
        
        # JUnit XML output
        cmd.extend([
            '--junitxml=' + str(self.reports_dir / 'integration-tests.xml'),
            '--tb=short'
        ])
        
        return self.run_command(cmd, "Integration Tests")
    
    def run_e2e_tests(self, verbose=False):
        """Run end-to-end tests."""
        cmd = [sys.executable, '-m', 'pytest']
        
        # Test path
        e2e_test_path = self.test_dir / 'e2e'
        if e2e_test_path.exists():
            cmd.append(str(e2e_test_path))
        else:
            cmd.extend([str(self.test_dir), '-m', 'e2e'])
        
        # Verbose output
        if verbose:
            cmd.append('-v')
        
        # JUnit XML output
        cmd.extend([
            '--junitxml=' + str(self.reports_dir / 'e2e-tests.xml'),
            '--tb=short',
            '--timeout=60'  # Longer timeout for E2E tests
        ])
        
        return self.run_command(cmd, "End-to-End Tests")
    
    def run_security_tests(self, verbose=False):
        """Run security tests."""
        cmd = [sys.executable, '-m', 'pytest']
        
        cmd.extend([
            str(self.test_dir),
            '-m', 'security',
            '--junitxml=' + str(self.reports_dir / 'security-tests.xml')
        ])
        
        if verbose:
            cmd.append('-v')
        
        return self.run_command(cmd, "Security Tests")
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests."""
        cmd = [sys.executable, '-m', 'pytest']
        
        cmd.extend([
            str(self.test_dir),
            '-m', 'performance',
            '--benchmark-only',
            '--benchmark-json=' + str(self.reports_dir / 'benchmark.json'),
            '--junitxml=' + str(self.reports_dir / 'performance-tests.xml')
        ])
        
        if verbose:
            cmd.append('-v')
        
        return self.run_command(cmd, "Performance Tests")
    
    def run_linting(self):
        """Run code linting."""
        success = True
        
        # Flake8
        flake8_cmd = [sys.executable, '-m', 'flake8', 'app', 'tests']
        if not self.run_command(flake8_cmd, "Flake8 Linting"):
            success = False
        
        # Black (code formatting check)
        black_cmd = [sys.executable, '-m', 'black', '--check', 'app', 'tests']
        if not self.run_command(black_cmd, "Black Code Formatting Check"):
            print("Code formatting issues found. Run 'black app tests' to fix.")
            success = False
        
        return success
    
    def run_type_checking(self):
        """Run type checking with mypy."""
        cmd = [sys.executable, '-m', 'mypy', 'app']
        return self.run_command(cmd, "Type Checking (MyPy)")
    
    def run_security_scan(self):
        """Run security scanning."""
        success = True
        
        # Bandit security scan
        bandit_cmd = [
            sys.executable, '-m', 'bandit',
            '-r', 'app',
            '-f', 'json',
            '-o', str(self.reports_dir / 'bandit-report.json')
        ]
        if not self.run_command(bandit_cmd, "Bandit Security Scan"):
            success = False
        
        # Safety check for known vulnerabilities
        safety_cmd = [sys.executable, '-m', 'safety', 'check', '--json']
        if not self.run_command(safety_cmd, "Safety Vulnerability Check"):
            success = False
        
        return success
    
    def generate_coverage_report(self):
        """Generate coverage report."""
        if not self.coverage_dir.exists():
            print("No coverage data found. Run tests with coverage first.")
            return False
        
        print(f"\nCoverage report generated at: {self.coverage_dir}/index.html")
        print(f"Test reports available at: {self.reports_dir}")
        return True
    
    def run_all_tests(self, verbose=False, fast=False):
        """Run all tests in sequence."""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE")
        print("="*80)
        
        start_time = time.time()
        results = {}
        
        # Install dependencies first
        if not self.install_dependencies():
            print("Failed to install dependencies")
            return False
        
        # Run tests in order
        test_suites = [
            ('Unit Tests', lambda: self.run_unit_tests(verbose, coverage=True)),
            ('Integration Tests', lambda: self.run_integration_tests(verbose)),
        ]
        
        if not fast:
            test_suites.extend([
                ('End-to-End Tests', lambda: self.run_e2e_tests(verbose)),
                ('Security Tests', lambda: self.run_security_tests(verbose)),
                ('Performance Tests', lambda: self.run_performance_tests(verbose)),
                ('Code Linting', self.run_linting),
                ('Type Checking', self.run_type_checking),
                ('Security Scan', self.run_security_scan)
            ])
        
        for test_name, test_func in test_suites:
            print(f"\n{'='*60}")
            print(f"Running {test_name}...")
            print(f"{'='*60}")
            
            success = test_func()
            results[test_name] = success
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        
        # Generate final report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:<30} {status}")
        
        print(f"\nTotal: {passed}/{total} test suites passed")
        print(f"Duration: {duration:.2f} seconds")
        
        # Generate coverage report
        self.generate_coverage_report()
        
        return all(results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--e2e', action='store_true', help='Run end-to-end tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--lint', action='store_true', help='Run linting only')
    parser.add_argument('--type-check', action='store_true', help='Run type checking only')
    parser.add_argument('--security-scan', action='store_true', help='Run security scan only')
    parser.add_argument('--all', action='store_true', help='Run all tests and checks')
    parser.add_argument('--fast', action='store_true', help='Run fast tests only (unit + integration)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies only')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle specific test types
    if args.install_deps:
        return 0 if runner.install_dependencies() else 1
    
    if args.unit:
        return 0 if runner.run_unit_tests(args.verbose, args.coverage) else 1
    
    if args.integration:
        return 0 if runner.run_integration_tests(args.verbose) else 1
    
    if args.e2e:
        return 0 if runner.run_e2e_tests(args.verbose) else 1
    
    if args.security:
        return 0 if runner.run_security_tests(args.verbose) else 1
    
    if args.performance:
        return 0 if runner.run_performance_tests(args.verbose) else 1
    
    if args.lint:
        return 0 if runner.run_linting() else 1
    
    if args.type_check:
        return 0 if runner.run_type_checking() else 1
    
    if args.security_scan:
        return 0 if runner.run_security_scan() else 1
    
    if args.coverage:
        return 0 if runner.generate_coverage_report() else 1
    
    # Default: run all tests or fast tests
    if args.all or args.fast or len(sys.argv) == 1:
        return 0 if runner.run_all_tests(args.verbose, args.fast) else 1
    
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())