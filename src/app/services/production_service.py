"""
Production-specific services for real SharePoint integration.
"""
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import ssl
import certifi
from urllib.parse import urlparse

from app.core.logging import get_logger
from app.core.config import ConfigService
from app.models.sharepoint import APIPayload
from app.models.response import APIResponse
from app.services.file_validation import MultipartFile
from app.clients.sharepoint import SharePointClient, SharePointError

logger = get_logger("production_service")


class ProductionSharePointClient(SharePointClient):
    """
    Production SharePoint client with enhanced security and monitoring.
    Extends the base SharePointClient with production-specific features.
    """
    
    def __init__(self, endpoint: Optional[str] = None, max_retries: int = 5, backoff_factor: float = 1.0):
        """
        Initialize production SharePoint client.
        
        Args:
            endpoint: SharePoint endpoint URL
            max_retries: Maximum retry attempts for failed requests
            backoff_factor: Backoff factor for retries
        """
        super().__init__(endpoint, max_retries, backoff_factor)
        
        # Production-specific configuration
        self.config_service = ConfigService()
        self.config = self.config_service.get_config()
        
        # Validate production requirements
        self._validate_production_config()
        
        # Enhanced session configuration for production
        self._configure_production_session()
        
        logger.info("ProductionSharePointClient initialized with enhanced security")
    
    def _validate_production_config(self) -> None:
        """Validate production configuration requirements."""
        if self.config.debug_mode:
            raise ValueError("Production SharePoint client cannot run in debug mode")
        
        # Get SharePoint endpoint (set by parent class)
        endpoint = getattr(self, 'sharepoint_endpoint', None) or self.config_service.get_sharepoint_endpoint()
        if not endpoint:
            raise ValueError("SharePoint endpoint is required for production mode")
        
        # Validate HTTPS endpoint
        parsed_url = urlparse(endpoint)
        if parsed_url.scheme != 'https':
            if self.config.environment == 'production':
                raise ValueError("Production mode requires HTTPS SharePoint endpoint")
            else:
                logger.warning("Non-HTTPS endpoint detected in production client")
        
        logger.info("Production configuration validation passed")
    
    def _configure_production_session(self) -> None:
        """Configure session with production-specific settings."""
        # SSL/TLS configuration
        self.session.verify = certifi.where()  # Use certifi CA bundle
        
        # Enhanced headers for production
        self.session.headers.update({
            'User-Agent': 'NetanyaIncidentService/1.0.0 (Production)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        # Production timeout settings
        self.session.timeout = 60  # Longer timeout for production
        
        logger.debug("Production session configuration applied")
    
    def submit_to_sharepoint(
        self,
        payload: APIPayload,
        file: Optional[MultipartFile] = None,
        timeout: int = 60
    ) -> APIResponse:
        """
        Submit incident to SharePoint with production logging and monitoring.
        
        Args:
            payload: The APIPayload object containing incident data
            file: Optional MultipartFile object for attachment
            timeout: Request timeout in seconds (production default: 60s)
            
        Returns:
            APIResponse: The parsed response from SharePoint API
            
        Raises:
            SharePointError: If the API call fails or returns an error
        """
        start_time = datetime.now(timezone.utc)
        correlation_id = f"prod-{start_time.strftime('%Y%m%d%H%M%S')}-{id(payload)}"
        
        # Production logging (limited detail)
        logger.info(
            f"SharePoint submission initiated [correlation_id: {correlation_id}]: "
            f"caller={payload.callerFirstName} {payload.callerLastName}, "
            f"description_length={len(payload.eventCallDesc)}, "
            f"has_file={file is not None}"
        )
        
        try:
            # Call parent implementation (parent method doesn't accept timeout parameter)
            response = super().submit_to_sharepoint(payload, file)
            
            # Production success logging
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"SharePoint submission successful [correlation_id: {correlation_id}]: "
                f"ticket_id={response.data}, duration={duration:.2f}s"
            )
            
            # Production metrics (if monitoring is enabled)
            self._record_metrics("sharepoint_submission_success", duration, {
                "has_file": file is not None,
                "response_code": response.ResultCode
            })
            
            return response
            
        except SharePointError as e:
            # Production error logging (sanitized)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(
                f"SharePoint submission failed [correlation_id: {correlation_id}]: "
                f"error_type={type(e).__name__}, duration={duration:.2f}s, "
                f"status_code={getattr(e, 'status_code', 'unknown')}"
            )
            
            # Record error metrics
            self._record_metrics("sharepoint_submission_error", duration, {
                "error_type": type(e).__name__,
                "status_code": getattr(e, 'status_code', 0)
            })
            
            # Re-raise with production-safe error message
            if self.config.environment == 'production':
                # Sanitize error message for production
                sanitized_message = self._sanitize_error_message(str(e))
                raise SharePointError(sanitized_message)
            else:
                raise
    
    def _sanitize_error_message(self, error_message: str) -> str:
        """Sanitize error messages for production to avoid leaking sensitive data."""
        # Remove potential sensitive information
        sensitive_patterns = [
            r'https?://[^\s]+',  # URLs
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
            r'password[=:\s]\S+',  # Passwords
            r'token[=:\s]\S+',  # Tokens
            r'key[=:\s]\S+',  # Keys
        ]
        
        import re
        sanitized = error_message
        for pattern in sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Generic error categories
        if 'connection' in sanitized.lower():
            return "SharePoint service connection error"
        elif 'timeout' in sanitized.lower():
            return "SharePoint service timeout"
        elif 'authentication' in sanitized.lower() or 'unauthorized' in sanitized.lower():
            return "SharePoint service authentication error"
        elif 'validation' in sanitized.lower():
            return "SharePoint service validation error"
        else:
            return "SharePoint service error"
    
    def _record_metrics(self, metric_name: str, duration: float, labels: Dict[str, Any]) -> None:
        """Record metrics for monitoring (placeholder for actual monitoring system)."""
        try:
            # This would integrate with actual monitoring systems like:
            # - Prometheus metrics
            # - New Relic
            # - DataDog
            # - Google Cloud Monitoring
            
            logger.debug(
                f"Metric recorded: {metric_name}, duration={duration:.2f}s, labels={labels}"
            )
            
            # Example integration points:
            # prometheus_client.Counter(metric_name).inc()
            # newrelic.agent.record_custom_metric(metric_name, duration)
            # statsd.timing(metric_name, duration * 1000)
            
        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check against SharePoint endpoint.
        
        Returns:
            Dict with health check results
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Simple connectivity test
            response = self.session.head(
                self.sharepoint_endpoint,
                timeout=10
            )
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_ms": duration * 1000,
                "status_code": response.status_code,
                "timestamp": start_time.isoformat(),
                "endpoint": self.sharepoint_endpoint
            }
            
        except requests.exceptions.Timeout:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return {
                "status": "unhealthy",
                "error": "Connection timeout",
                "response_time_ms": duration * 1000,
                "timestamp": start_time.isoformat(),
                "endpoint": self.sharepoint_endpoint
            }
            
        except requests.exceptions.ConnectionError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return {
                "status": "unhealthy",
                "error": "Connection failed",
                "response_time_ms": duration * 1000,
                "timestamp": start_time.isoformat(),
                "endpoint": self.sharepoint_endpoint
            }
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"SharePoint health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": "Health check failed",
                "response_time_ms": duration * 1000,
                "timestamp": start_time.isoformat(),
                "endpoint": self.sharepoint_endpoint
            }


class ProductionIncidentService:
    """
    Production incident service with enhanced monitoring and error handling.
    """
    
    def __init__(self):
        """Initialize production incident service."""
        self.config_service = ConfigService()
        self.config = self.config_service.get_config()
        
        # Use production SharePoint client
        self.sharepoint_client = ProductionSharePointClient()
        
        logger.info("ProductionIncidentService initialized")
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get production service metrics."""
        return {
            "service_name": "Netanya Incident Service",
            "version": "1.0.0",
            "environment": self.config.environment,
            "uptime": self._get_uptime(),
            "sharepoint_health": self.sharepoint_client.health_check(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_uptime(self) -> str:
        """Get service uptime (placeholder)."""
        # This would track actual service start time
        return "running"


def create_production_client() -> ProductionSharePointClient:
    """Factory function to create production SharePoint client."""
    config_service = ConfigService()
    config = config_service.get_config()
    
    if config.debug_mode:
        raise ValueError("Cannot create production client in debug mode")
    
    return ProductionSharePointClient()
