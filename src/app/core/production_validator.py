"""
Production configuration validator and security checker.
"""
import os
import ssl
import requests
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.logging import get_logger
from app.core.config import ConfigService

logger = get_logger("production_validator")


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'security', 'configuration', 'connectivity'


class ProductionValidator:
    """
    Validates production configuration and security requirements.
    """
    
    def __init__(self):
        """Initialize production validator."""
        self.config_service = ConfigService()
        self.config = self.config_service.get_config()
        logger.info("ProductionValidator initialized")
    
    def validate_all(self) -> List[ValidationResult]:
        """
        Run all production validation checks.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Configuration validation
        results.extend(self._validate_environment_config())
        results.extend(self._validate_security_config())
        results.extend(self._validate_sharepoint_config())
        
        # Security validation
        results.extend(self._validate_https_requirements())
        results.extend(self._validate_debug_settings())
        results.extend(self._validate_logging_config())
        
        # Connectivity validation
        results.extend(self._validate_sharepoint_connectivity())
        
        logger.info(f"Production validation completed: {len(results)} checks performed")
        return results
    
    def _validate_environment_config(self) -> List[ValidationResult]:
        """Validate basic environment configuration."""
        results = []
        
        # Check environment setting
        if self.config.environment != 'production':
            results.append(ValidationResult(
                is_valid=False,
                message=f"Environment is set to '{self.config.environment}', should be 'production'",
                severity='warning',
                category='configuration'
            ))
        
        # Check debug mode
        if self.config.debug_mode:
            results.append(ValidationResult(
                is_valid=False,
                message="Debug mode is enabled in production environment",
                severity='error',
                category='security'
            ))
        
        # Check log level
        if self.config.log_level in ['DEBUG', 'TRACE']:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Log level '{self.config.log_level}' may expose sensitive information",
                severity='warning',
                category='security'
            ))
        
        return results
    
    def _validate_security_config(self) -> List[ValidationResult]:
        """Validate security configuration."""
        results = []
        
        # Check for sensitive environment variables
        sensitive_vars = [
            'SECRET_KEY', 'PASSWORD', 'TOKEN', 'PRIVATE_KEY',
            'API_KEY', 'DATABASE_URL', 'REDIS_URL'
        ]
        
        for var in sensitive_vars:
            if var in os.environ:
                value = os.environ[var]
                if len(value) < 16:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Environment variable '{var}' appears to have a weak value",
                        severity='warning',
                        category='security'
                    ))
        
        # Check file permissions (if applicable)
        config_files = ['/etc/netanya-incident/', './config/']
        for config_path in config_files:
            if os.path.exists(config_path):
                stat_info = os.stat(config_path)
                if stat_info.st_mode & 0o077:  # Check if group/other have any permissions
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Configuration directory '{config_path}' has overly permissive permissions",
                        severity='warning',
                        category='security'
                    ))
        
        return results
    
    def _validate_sharepoint_config(self) -> List[ValidationResult]:
        """Validate SharePoint configuration."""
        results = []
        
        sharepoint_endpoint = self.config_service.get_sharepoint_endpoint()
        
        if not sharepoint_endpoint:
            results.append(ValidationResult(
                is_valid=False,
                message="SharePoint endpoint is not configured",
                severity='error',
                category='configuration'
            ))
            return results
        
        # Validate URL format
        try:
            parsed_url = urlparse(sharepoint_endpoint)
            if not parsed_url.scheme or not parsed_url.netloc:
                results.append(ValidationResult(
                    is_valid=False,
                    message="SharePoint endpoint is not a valid URL",
                    severity='error',
                    category='configuration'
                ))
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"Failed to parse SharePoint endpoint: {e}",
                severity='error',
                category='configuration'
            ))
        
        return results
    
    def _validate_https_requirements(self) -> List[ValidationResult]:
        """Validate HTTPS and SSL/TLS configuration."""
        results = []
        
        sharepoint_endpoint = self.config_service.get_sharepoint_endpoint()
        if sharepoint_endpoint:
            parsed_url = urlparse(sharepoint_endpoint)
            
            if parsed_url.scheme != 'https':
                results.append(ValidationResult(
                    is_valid=False,
                    message="SharePoint endpoint is not using HTTPS",
                    severity='error',
                    category='security'
                ))
            
            # Check SSL certificate validity
            if parsed_url.scheme == 'https':
                try:
                    hostname = parsed_url.hostname
                    port = parsed_url.port or 443
                    
                    context = ssl.create_default_context()
                    with context.wrap_socket(
                        ssl.socket(),
                        server_hostname=hostname
                    ) as ssock:
                        ssock.settimeout(10)
                        ssock.connect((hostname, port))
                        
                    results.append(ValidationResult(
                        is_valid=True,
                        message="SSL certificate validation passed",
                        severity='info',
                        category='security'
                    ))
                    
                except ssl.SSLError as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"SSL certificate validation failed: {e}",
                        severity='error',
                        category='security'
                    ))
                except Exception as e:
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"SSL validation error: {e}",
                        severity='warning',
                        category='security'
                    ))
        
        return results
    
    def _validate_debug_settings(self) -> List[ValidationResult]:
        """Validate debug-related settings."""
        results = []
        
        # Check for debug artifacts
        debug_indicators = [
            ('DEBUG', 'Environment variable DEBUG is set'),
            ('FLASK_DEBUG', 'Flask debug mode environment variable is set'),
            ('DJANGO_DEBUG', 'Django debug mode environment variable is set'),
        ]
        
        for var_name, message in debug_indicators:
            if os.environ.get(var_name, '').lower() in ['true', '1', 'yes']:
                results.append(ValidationResult(
                    is_valid=False,
                    message=message,
                    severity='warning',
                    category='security'
                ))
        
        return results
    
    def _validate_logging_config(self) -> List[ValidationResult]:
        """Validate logging configuration for production."""
        results = []
        
        # Check if logs might contain sensitive data
        if self.config.log_level in ['DEBUG', 'TRACE']:
            results.append(ValidationResult(
                is_valid=False,
                message="Debug logging may expose sensitive information in production",
                severity='warning',
                category='security'
            ))
        
        # Check log file permissions
        log_files = ['/var/log/netanya-incident-service.log', './logs/']
        for log_path in log_files:
            if os.path.exists(log_path):
                stat_info = os.stat(log_path)
                if stat_info.st_mode & 0o044:  # Check if group/other can read
                    results.append(ValidationResult(
                        is_valid=False,
                        message=f"Log file '{log_path}' is readable by group/other",
                        severity='warning',
                        category='security'
                    ))
        
        return results
    
    def _validate_sharepoint_connectivity(self) -> List[ValidationResult]:
        """Validate SharePoint connectivity."""
        results = []
        
        sharepoint_endpoint = self.config_service.get_sharepoint_endpoint()
        if not sharepoint_endpoint:
            return results
        
        try:
            # Simple connectivity test
            response = requests.head(
                sharepoint_endpoint,
                timeout=10,
                verify=True,
                headers={'User-Agent': 'NetanyaIncidentService/1.0.0 (Health Check)'}
            )
            
            if response.status_code < 500:
                results.append(ValidationResult(
                    is_valid=True,
                    message=f"SharePoint endpoint is reachable (HTTP {response.status_code})",
                    severity='info',
                    category='connectivity'
                ))
            else:
                results.append(ValidationResult(
                    is_valid=False,
                    message=f"SharePoint endpoint returned HTTP {response.status_code}",
                    severity='warning',
                    category='connectivity'
                ))
            
        except requests.exceptions.Timeout:
            results.append(ValidationResult(
                is_valid=False,
                message="SharePoint endpoint connection timeout",
                severity='error',
                category='connectivity'
            ))
        except requests.exceptions.ConnectionError:
            results.append(ValidationResult(
                is_valid=False,
                message="SharePoint endpoint connection failed",
                severity='error',
                category='connectivity'
            ))
        except Exception as e:
            results.append(ValidationResult(
                is_valid=False,
                message=f"SharePoint connectivity check failed: {e}",
                severity='warning',
                category='connectivity'
            ))
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get a summary of validation results."""
        total_checks = len(results)
        errors = [r for r in results if r.severity == 'error']
        warnings = [r for r in results if r.severity == 'warning']
        passed = [r for r in results if r.is_valid and r.severity == 'info']
        
        return {
            "total_checks": total_checks,
            "errors": len(errors),
            "warnings": len(warnings),
            "passed": len(passed),
            "is_production_ready": len(errors) == 0,
            "error_details": [{"message": r.message, "category": r.category} for r in errors],
            "warning_details": [{"message": r.message, "category": r.category} for r in warnings]
        }
