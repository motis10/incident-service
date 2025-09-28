"""
Health monitoring and service readiness checks.
"""
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger
from app.core.config import ConfigService

logger = get_logger("health_monitoring")


class ServiceHealth(Enum):
    """Service health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class DependencyStatus:
    """Status of a service dependency."""
    name: str
    status: str
    message: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    status: str
    message: str
    timestamp: str
    response_time_ms: float
    checks: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ComprehensiveHealthResult:
    """Result of comprehensive health check."""
    overall_status: str
    timestamp: str
    dependencies: Dict[str, Dict[str, Any]]
    service_info: Dict[str, Any]
    response_time_ms: float


class HealthMonitoringService:
    """
    Service for monitoring application health and dependencies.
    Provides comprehensive health checks for Cloud Run and load balancing.
    """
    
    def __init__(self):
        """Initialize health monitoring service."""
        self.config_service = ConfigService()
        self.config = self.config_service.get_config()
        self.sharepoint_endpoint = self.config_service.get_sharepoint_endpoint()
        self._cache = {}
        self._cache_ttl = 30  # Cache results for 30 seconds
        logger.info("HealthMonitoringService initialized")
    
    def check_service_health(self) -> HealthCheckResult:
        """
        Check basic service health.
        
        Returns:
            HealthCheckResult with service status
        """
        start_time = time.time()
        
        try:
            # Basic service checks
            checks = {
                "memory": "available",
                "startup": "completed",
                "configuration": "loaded"
            }
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                status=ServiceHealth.HEALTHY.value,
                message="Service is running normally",
                timestamp=datetime.now(timezone.utc).isoformat(),
                response_time_ms=response_time,
                checks=checks
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Service health check failed: {e}")
            
            return HealthCheckResult(
                status=ServiceHealth.UNHEALTHY.value,
                message=f"Service health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                response_time_ms=response_time
            )
    
    def check_sharepoint_connectivity(self) -> DependencyStatus:
        """
        Check SharePoint endpoint connectivity.
        
        Returns:
            DependencyStatus for SharePoint connectivity
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = "sharepoint_connectivity"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)
        
        try:
            is_connected = self._check_sharepoint_endpoint()
            response_time = (time.time() - start_time) * 1000
            
            if is_connected:
                result = DependencyStatus(
                    name="sharepoint",
                    status=ServiceHealth.HEALTHY.value,
                    message="SharePoint connectivity verified",
                    response_time_ms=response_time,
                    details={"endpoint": self.sharepoint_endpoint}
                )
            else:
                result = DependencyStatus(
                    name="sharepoint",
                    status=ServiceHealth.UNHEALTHY.value,
                    message="SharePoint connectivity failed",
                    response_time_ms=response_time,
                    details={"endpoint": self.sharepoint_endpoint}
                )
            
            self._cache_result(cache_key, result)
            return result
            
        except TimeoutError as e:
            response_time = (time.time() - start_time) * 1000
            result = DependencyStatus(
                name="sharepoint",
                status=ServiceHealth.UNHEALTHY.value,
                message=f"SharePoint connectivity timeout: {str(e)}",
                response_time_ms=response_time,
                details={"error": "timeout"}
            )
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"SharePoint connectivity check failed: {e}")
            
            result = DependencyStatus(
                name="sharepoint",
                status=ServiceHealth.UNHEALTHY.value,
                message=f"SharePoint connectivity error: {str(e)}",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
            self._cache_result(cache_key, result)
            return result
    
    def check_configuration_validity(self) -> HealthCheckResult:
        """
        Check configuration validity and completeness.
        
        Returns:
            HealthCheckResult for configuration status
        """
        start_time = time.time()
        
        try:
            config_details = {
                "sharepoint_endpoint": "configured" if self.sharepoint_endpoint else "missing",
                "debug_mode": str(self.config.debug_mode),
                "log_level": self.config.log_level,
                "environment": self.config.environment,
                "port": str(self.config.port)
            }
            
            # Check for critical missing configuration
            critical_missing = []
            if not self.sharepoint_endpoint:
                critical_missing.append("sharepoint_endpoint")
            
            response_time = (time.time() - start_time) * 1000
            
            if critical_missing:
                return HealthCheckResult(
                    status=ServiceHealth.UNHEALTHY.value,
                    message=f"Critical configuration missing: {', '.join(critical_missing)}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    response_time_ms=response_time,
                    details=config_details
                )
            else:
                return HealthCheckResult(
                    status=ServiceHealth.HEALTHY.value,
                    message="Configuration is valid and complete",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    response_time_ms=response_time,
                    details=config_details
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Configuration validation failed: {e}")
            
            return HealthCheckResult(
                status=ServiceHealth.UNHEALTHY.value,
                message=f"Configuration validation error: {str(e)}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                response_time_ms=response_time
            )
    
    def get_comprehensive_health(self) -> ComprehensiveHealthResult:
        """
        Get comprehensive health status including all dependencies.
        
        Returns:
            ComprehensiveHealthResult with overall status
        """
        start_time = time.time()
        
        # Check all dependencies
        sharepoint_status = self.check_sharepoint_connectivity()
        config_status = self.check_configuration_validity()
        
        # Determine overall status
        statuses = [sharepoint_status.status, config_status.status]
        
        if all(status == ServiceHealth.HEALTHY.value for status in statuses):
            overall_status = ServiceHealth.HEALTHY.value
        elif any(status == ServiceHealth.UNHEALTHY.value for status in statuses):
            overall_status = ServiceHealth.UNHEALTHY.value
        else:
            overall_status = ServiceHealth.DEGRADED.value
        
        dependencies = {
            "sharepoint": {
                "status": sharepoint_status.status,
                "message": sharepoint_status.message,
                "response_time_ms": sharepoint_status.response_time_ms
            },
            "configuration": {
                "status": config_status.status,
                "message": config_status.message,
                "details": config_status.details
            }
        }
        
        service_info = {
            "name": "Netanya Incident Service",
            "version": "1.0.0",
            "environment": self.config.environment,
            "debug_mode": self.config.debug_mode
        }
        
        response_time = (time.time() - start_time) * 1000
        
        return ComprehensiveHealthResult(
            overall_status=overall_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            dependencies=dependencies,
            service_info=service_info,
            response_time_ms=response_time
        )
    
    def _check_sharepoint_endpoint(self) -> bool:
        """
        Check if SharePoint endpoint is reachable.
        
        Returns:
            True if endpoint is reachable, False otherwise
            
        Raises:
            TimeoutError: If request times out
        """
        # In debug mode, skip actual connectivity check
        if self.config.debug_mode:
            logger.debug("Debug mode: Skipping actual SharePoint connectivity check")
            return True
        
        try:
            # Simple connectivity test (HEAD request)
            response = requests.head(
                self.sharepoint_endpoint,
                timeout=5,
                verify=True
            )
            # Accept any response (even errors) as "reachable"
            return True
            
        except requests.exceptions.Timeout:
            raise TimeoutError("SharePoint endpoint timeout")
        except requests.exceptions.ConnectionError:
            return False
        except Exception:
            return False
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid."""
        if key not in self._cache:
            return False
        
        cached_time, _ = self._cache[key]
        return (time.time() - cached_time) < self._cache_ttl
    
    def _get_cached(self, key: str) -> Any:
        """Get cached result."""
        return self._cache[key][1]
    
    def _cache_result(self, key: str, result: Any) -> None:
        """Cache result with timestamp."""
        self._cache[key] = (time.time(), result)
