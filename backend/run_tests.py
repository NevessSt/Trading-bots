#!/usr/bin/env python3
"""Comprehensive test runner for the trading bot platform."""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional
import json


class TestRunner:
    """Comprehensive test runner with multiple test types and reporting."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: List[str], description: str) -> Dict:
        """Run a command and capture results."""
        self.log(f"Running {description}...")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration,
                'command': ' '.join(command)
            }
        
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {description}", "ERROR")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'duration': time.time() - start_time,
                'command': ' '.join(command)
            }
        
        except Exception as e:
            self.log(f"Command failed: {description} - {str(e)}", "ERROR")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': time.time() - start_time,
                'command': ' '.join(command)
            }
    
    def setup_environment(self):
        """Set up the test environment."""
        self.log("Setting up test environment...")
        
        # Set environment variables for testing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
        
        # Create necessary directories
        (self.project_root / 'test-results').mkdir(exist_ok=True)
        (self.project_root / 'htmlcov').mkdir(exist_ok=True)
    
    def run_unit_tests(self) -> Dict:
        """Run unit tests."""
        command = [
            'python', '-m', 'pytest',
            'tests/unit/',
            '-v',
            '--cov=.',
            '--cov-report=xml:test-results/coverage-unit.xml',
            '--cov-report=html:htmlcov/unit',
            '--junit-xml=test-results/unit-tests.xml',
            '--tb=short'
        ]
        
        result = self.run_command(command, "Unit Tests")
        self.test_results['unit_tests'] = result
        
        if result['success']:
            self.log("✅ Unit tests passed", "SUCCESS")
        else:
            self.log("❌ Unit tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_integration_tests(self) -> Dict:
        """Run integration tests."""
        command = [
            'python', '-m', 'pytest',
            'tests/integration/',
            '-v',
            '--cov=.',
            '--cov-append',
            '--cov-report=xml:test-results/coverage-integration.xml',
            '--cov-report=html:htmlcov/integration',
            '--junit-xml=test-results/integration-tests.xml',
            '--tb=short'
        ]
        
        result = self.run_command(command, "Integration Tests")
        self.test_results['integration_tests'] = result
        
        if result['success']:
            self.log("✅ Integration tests passed", "SUCCESS")
        else:
            self.log("❌ Integration tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_e2e_tests(self) -> Dict:
        """Run end-to-end tests."""
        command = [
            'python', '-m', 'pytest',
            'tests/e2e/',
            '-v',
            '--junit-xml=test-results/e2e-tests.xml',
            '--tb=short'
        ]
        
        result = self.run_command(command, "End-to-End Tests")
        self.test_results['e2e_tests'] = result
        
        if result['success']:
            self.log("✅ E2E tests passed", "SUCCESS")
        else:
            self.log("❌ E2E tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_security_tests(self) -> Dict:
        """Run security tests."""
        command = [
            'python', '-m', 'pytest',
            'tests/security/',
            '-v',
            '--junit-xml=test-results/security-tests.xml',
            '--tb=short'
        ]
        
        result = self.run_command(command, "Security Tests")
        self.test_results['security_tests'] = result
        
        if result['success']:
            self.log("✅ Security tests passed", "SUCCESS")
        else:
            self.log("❌ Security tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_performance_tests(self) -> Dict:
        """Run performance tests."""
        command = [
            'python', '-m', 'pytest',
            'tests/performance/',
            '-v',
            '--junit-xml=test-results/performance-tests.xml',
            '--tb=short'
        ]
        
        result = self.run_command(command, "Performance Tests")
        self.test_results['performance_tests'] = result
        
        if result['success']:
            self.log("✅ Performance tests passed", "SUCCESS")
        else:
            self.log("❌ Performance tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def run_linting(self) -> Dict:
        """Run code linting."""
        command = [
            'python', '-m', 'flake8',
            '.',
            '--count',
            '--statistics',
            '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s',
            '--output-file=test-results/flake8-report.txt'
        ]
        
        result = self.run_command(command, "Code Linting (flake8)")
        self.test_results['linting'] = result
        
        if result['success']:
            self.log("✅ Linting passed", "SUCCESS")
        else:
            self.log("⚠️ Linting issues found", "WARNING")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
        
        return result
    
    def run_type_checking(self) -> Dict:
        """Run type checking with mypy."""
        command = [
            'python', '-m', 'mypy',
            '.',
            '--ignore-missing-imports',
            '--no-strict-optional',
            '--txt-report', 'test-results',
            '--html-report', 'test-results/mypy-html'
        ]
        
        result = self.run_command(command, "Type Checking (mypy)")
        self.test_results['type_checking'] = result
        
        if result['success']:
            self.log("✅ Type checking passed", "SUCCESS")
        else:
            self.log("⚠️ Type checking issues found", "WARNING")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
        
        return result
    
    def run_security_scan(self) -> Dict:
        """Run security scanning with bandit."""
        command = [
            'python', '-m', 'bandit',
            '-r', '.',
            '-f', 'json',
            '-o', 'test-results/bandit-report.json'
        ]
        
        result = self.run_command(command, "Security Scanning (bandit)")
        self.test_results['security_scan'] = result
        
        if result['success']:
            self.log("✅ Security scan passed", "SUCCESS")
        else:
            self.log("⚠️ Security issues found", "WARNING")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
        
        return result
    
    def generate_coverage_report(self) -> Dict:
        """Generate comprehensive coverage report."""
        command = [
            'python', '-m', 'coverage',
            'combine'
        ]
        
        # Combine coverage data
        combine_result = self.run_command(command, "Combining Coverage Data")
        
        # Generate HTML report
        html_command = [
            'python', '-m', 'coverage',
            'html',
            '-d', 'htmlcov/combined'
        ]
        
        html_result = self.run_command(html_command, "Generating HTML Coverage Report")
        
        # Generate XML report
        xml_command = [
            'python', '-m', 'coverage',
            'xml',
            '-o', 'test-results/coverage-combined.xml'
        ]
        
        xml_result = self.run_command(xml_command, "Generating XML Coverage Report")
        
        # Generate text report
        text_command = [
            'python', '-m', 'coverage',
            'report',
            '--show-missing'
        ]
        
        text_result = self.run_command(text_command, "Generating Text Coverage Report")
        
        result = {
            'success': all([r['success'] for r in [combine_result, html_result, xml_result, text_result]]),
            'combine': combine_result,
            'html': html_result,
            'xml': xml_result,
            'text': text_result
        }
        
        self.test_results['coverage_report'] = result
        
        if result['success']:
            self.log("✅ Coverage report generated", "SUCCESS")
            if text_result['success']:
                self.log("Coverage Summary:")
                self.log(text_result['stdout'])
        else:
            self.log("❌ Coverage report generation failed", "ERROR")
        
        return result
    
    def run_load_tests(self, users: int = 10, duration: str = "30s") -> Dict:
        """Run load tests with Locust."""
        command = [
            'python', '-m', 'locust',
            '-f', 'tests/performance/locustfile.py',
            '--headless',
            '--users', str(users),
            '--spawn-rate', '2',
            '--run-time', duration,
            '--host', 'http://localhost:5000',
            '--html', 'test-results/load-test-report.html',
            '--csv', 'test-results/load-test'
        ]
        
        result = self.run_command(command, f"Load Tests ({users} users, {duration})")
        self.test_results['load_tests'] = result
        
        if result['success']:
            self.log("✅ Load tests completed", "SUCCESS")
        else:
            self.log("❌ Load tests failed", "ERROR")
            if self.verbose:
                self.log(f"STDOUT: {result['stdout']}")
                self.log(f"STDERR: {result['stderr']}")
        
        return result
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        total_duration = time.time() - self.start_time
        
        summary = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_duration': round(total_duration, 2),
            'results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results.values() if r.get('success', False)),
                'failed': sum(1 for r in self.test_results.values() if not r.get('success', False))
            }
        }
        
        # Save JSON report
        with open(self.project_root / 'test-results' / 'summary-report.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate text summary
        self.log("\n" + "="*60)
        self.log("TEST EXECUTION SUMMARY")
        self.log("="*60)
        self.log(f"Total Duration: {total_duration:.2f} seconds")
        self.log(f"Tests Run: {summary['summary']['total_tests']}")
        self.log(f"Passed: {summary['summary']['passed']}")
        self.log(f"Failed: {summary['summary']['failed']}")
        self.log("\nDetailed Results:")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            duration = result.get('duration', 0)
            self.log(f"  {test_name}: {status} ({duration:.2f}s)")
        
        self.log("\nReports Generated:")
        self.log(f"  - HTML Coverage: htmlcov/combined/index.html")
        self.log(f"  - XML Coverage: test-results/coverage-combined.xml")
        self.log(f"  - Test Results: test-results/")
        self.log(f"  - Summary: test-results/summary-report.json")
        
        if 'load_tests' in self.test_results:
            self.log(f"  - Load Test Report: test-results/load-test-report.html")
        
        self.log("="*60)
        
        return summary


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for trading bot platform")
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--load', action='store_true', help='Run load tests')
    parser.add_argument('--lint', action='store_true', help='Run linting only')
    parser.add_argument('--type-check', action='store_true', help='Run type checking only')
    parser.add_argument('--security-scan', action='store_true', help='Run security scan only')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report only')
    parser.add_argument('--all', action='store_true', help='Run all tests and checks')
    parser.add_argument('--load-users', type=int, default=10, help='Number of users for load testing')
    parser.add_argument('--load-duration', default='30s', help='Duration for load testing')
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    runner.setup_environment()
    
    # Determine what to run
    run_all = args.all or not any([
        args.unit, args.integration, args.e2e, args.security, args.performance,
        args.load, args.lint, args.type_check, args.security_scan, args.coverage
    ])
    
    try:
        if run_all or args.unit:
            runner.run_unit_tests()
        
        if run_all or args.integration:
            runner.run_integration_tests()
        
        if run_all or args.e2e:
            runner.run_e2e_tests()
        
        if run_all or args.security:
            runner.run_security_tests()
        
        if run_all or args.performance:
            runner.run_performance_tests()
        
        if run_all or args.lint:
            runner.run_linting()
        
        if run_all or args.type_check:
            runner.run_type_checking()
        
        if run_all or args.security_scan:
            runner.run_security_scan()
        
        if args.load:
            runner.run_load_tests(args.load_users, args.load_duration)
        
        if run_all or args.coverage or any([args.unit, args.integration]):
            runner.generate_coverage_report()
        
        # Always generate summary
        summary = runner.generate_summary_report()
        
        # Exit with appropriate code
        if summary['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "WARNING")
        sys.exit(130)
    
    except Exception as e:
        runner.log(f"Test execution failed: {str(e)}", "ERROR")
        sys.exit(1)


if __name__ == '__main__':
    main()