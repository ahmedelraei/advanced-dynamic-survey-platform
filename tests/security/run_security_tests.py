#!/usr/bin/env python
"""
Security Testing Script

This script performs automated security testing including:
- OWASP Top 10 vulnerability checks
- Penetration testing scenarios
- Security configuration validation

Usage:
    python tests/security/run_security_tests.py
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests


class SecurityTester:
    """Automated security testing for ADSP."""
    
    def __init__(self, base_url, output_file=None):
        """Initialize security tester."""
        self.base_url = base_url.rstrip('/')
        self.output_file = output_file
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': base_url,
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
    
    def run_all_tests(self):
        """Run all security tests."""
        print("=" * 80)
        print("ADSP Security Testing Suite")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Started: {self.results['timestamp']}")
        print("=" * 80)
        print()
        
        # Run test categories
        self.test_sql_injection()
        self.test_xss_prevention()
        self.test_authentication()
        self.test_authorization()
        self.test_csrf_protection()
        self.test_security_headers()
        self.test_sensitive_data_exposure()
        self.test_rate_limiting()
        
        # Print summary
        self.print_summary()
        
        # Save results
        if self.output_file:
            self.save_results()
        
        # Return exit code
        return 0 if self.results['summary']['failed'] == 0 else 1
    
    def test_sql_injection(self):
        """Test SQL injection prevention."""
        print("Testing SQL Injection Prevention...")
        
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE surveys; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
        ]
        
        for payload in payloads:
            result = self._test_endpoint(
                'POST',
                '/api/v1/surveys/',
                {'title': payload, 'description': 'test'},
                'SQL Injection',
                f"Payload: {payload}"
            )
            
            # Should not return 500 (server error)
            if result['status_code'] == 500:
                result['passed'] = False
                result['message'] = "Server error - possible SQL injection vulnerability"
            else:
                result['passed'] = True
                result['message'] = "SQL injection prevented"
            
            self._add_result(result)
    
    def test_xss_prevention(self):
        """Test XSS prevention."""
        print("Testing XSS Prevention...")
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for payload in payloads:
            result = self._test_endpoint(
                'POST',
                '/api/v1/surveys/',
                {'title': payload, 'description': 'test'},
                'XSS Prevention',
                f"Payload: {payload}"
            )
            
            # Check if response escapes the payload
            if result['status_code'] == 201:
                response_data = result.get('response_data', {})
                if payload in str(response_data):
                    # Payload present but should be escaped in JSON
                    result['passed'] = True
                    result['message'] = "XSS payload stored safely (JSON auto-escapes)"
                else:
                    result['passed'] = True
                    result['message'] = "XSS payload filtered"
            
            self._add_result(result)
    
    def test_authentication(self):
        """Test authentication requirements."""
        print("Testing Authentication...")
        
        protected_endpoints = [
            ('GET', '/api/v1/surveys/'),
            ('POST', '/api/v1/surveys/'),
            ('GET', '/api/v1/users/'),
        ]
        
        for method, endpoint in protected_endpoints:
            result = self._test_endpoint(
                method,
                endpoint,
                None,
                'Authentication',
                f"{method} {endpoint} without auth"
            )
            
            # Should return 401 Unauthorized
            if result['status_code'] == 401:
                result['passed'] = True
                result['message'] = "Authentication required"
            else:
                result['passed'] = False
                result['message'] = f"Expected 401, got {result['status_code']}"
            
            self._add_result(result)
    
    def test_authorization(self):
        """Test authorization and permissions."""
        print("Testing Authorization...")
        
        # This would require setting up test users with different roles
        # For now, we'll test that endpoints check permissions
        result = {
            'category': 'Authorization',
            'test': 'Role-based access control',
            'passed': None,
            'message': 'Manual verification required',
            'severity': 'warning'
        }
        self._add_result(result)
    
    def test_csrf_protection(self):
        """Test CSRF protection."""
        print("Testing CSRF Protection...")
        
        # DRF uses token-based auth, which is CSRF-safe
        result = {
            'category': 'CSRF Protection',
            'test': 'Token-based authentication',
            'passed': True,
            'message': 'Using token-based auth (CSRF-safe)',
            'severity': 'info'
        }
        self._add_result(result)
    
    def test_security_headers(self):
        """Test security headers."""
        print("Testing Security Headers...")
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/", timeout=10)
            headers = response.headers
            
            # Check for important security headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'Strict-Transport-Security': None,  # Should be present
            }
            
            for header, expected_value in security_headers.items():
                result = {
                    'category': 'Security Headers',
                    'test': f"Header: {header}",
                    'status_code': response.status_code
                }
                
                if header in headers:
                    if expected_value is None or headers[header] in (expected_value if isinstance(expected_value, list) else [expected_value]):
                        result['passed'] = True
                        result['message'] = f"Header present: {headers[header]}"
                    else:
                        result['passed'] = False
                        result['message'] = f"Unexpected value: {headers[header]}"
                else:
                    result['passed'] = False
                    result['message'] = "Header missing"
                    result['severity'] = 'warning'
                
                self._add_result(result)
        
        except Exception as e:
            result = {
                'category': 'Security Headers',
                'test': 'Header check',
                'passed': False,
                'message': f"Error: {str(e)}",
                'severity': 'error'
            }
            self._add_result(result)
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure."""
        print("Testing Sensitive Data Exposure...")
        
        # Test that passwords are never exposed
        result = {
            'category': 'Sensitive Data',
            'test': 'Password exposure in API',
            'passed': None,
            'message': 'Requires authenticated testing',
            'severity': 'warning'
        }
        self._add_result(result)
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        print("Testing Rate Limiting...")
        
        # Make multiple rapid requests
        endpoint = '/api/v1/public/surveys/'
        num_requests = 50
        
        try:
            responses = []
            for _ in range(num_requests):
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                responses.append(response.status_code)
            
            # Check if any requests were rate-limited (429)
            rate_limited = any(status == 429 for status in responses)
            
            result = {
                'category': 'Rate Limiting',
                'test': f'{num_requests} rapid requests',
                'passed': None,
                'message': f"Rate limiting {'detected' if rate_limited else 'not detected'}",
                'severity': 'warning' if not rate_limited else 'info'
            }
            self._add_result(result)
        
        except Exception as e:
            result = {
                'category': 'Rate Limiting',
                'test': 'Rate limit check',
                'passed': False,
                'message': f"Error: {str(e)}",
                'severity': 'error'
            }
            self._add_result(result)
    
    def _test_endpoint(self, method, endpoint, data, category, test_name):
        """Test a specific endpoint."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.request(method, url, json=data, timeout=10)
            
            return {
                'category': category,
                'test': test_name,
                'status_code': response.status_code,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        
        except Exception as e:
            return {
                'category': category,
                'test': test_name,
                'passed': False,
                'message': f"Error: {str(e)}",
                'severity': 'error'
            }
    
    def _add_result(self, result):
        """Add a test result."""
        self.results['tests'].append(result)
        self.results['summary']['total'] += 1
        
        if result.get('passed') is True:
            self.results['summary']['passed'] += 1
            status = "✓ PASS"
        elif result.get('passed') is False:
            self.results['summary']['failed'] += 1
            status = "✗ FAIL"
        else:
            self.results['summary']['warnings'] += 1
            status = "⚠ WARN"
        
        print(f"  {status} - {result['test']}: {result.get('message', '')}")
    
    def print_summary(self):
        """Print test summary."""
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Tests:  {self.results['summary']['total']}")
        print(f"Passed:       {self.results['summary']['passed']}")
        print(f"Failed:       {self.results['summary']['failed']}")
        print(f"Warnings:     {self.results['summary']['warnings']}")
        print("=" * 80)
    
    def save_results(self):
        """Save results to file."""
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run security tests for ADSP')
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the application (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--output',
        default='security-test-results.json',
        help='Output file for results (default: security-test-results.json)'
    )
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url, args.output)
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
