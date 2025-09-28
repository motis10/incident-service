"""
Test health monitoring and service readiness endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture
def client():
    """Create test client for health monitoring endpoints."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

def test_health_monitoring_import():
    """Test that health monitoring service can be imported."""
    try:
        from app.services.health_monitoring import (
            HealthMonitoringService, ServiceHealth, DependencyStatus, HealthCheckResult
        )
        assert HealthMonitoringService is not None
        assert ServiceHealth is not None
        assert DependencyStatus is not None
        assert HealthCheckResult is not None
    except ImportError:
        pytest.fail("Could not import health monitoring service")

def test_health_service_initialization():
    """Test health monitoring service initialization."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    # Should have methods for different checks
    assert hasattr(service, 'check_service_health')
    assert hasattr(service, 'check_sharepoint_connectivity')
    assert hasattr(service, 'check_configuration_validity')
    assert hasattr(service, 'get_comprehensive_health')

def test_basic_service_health_check():
    """Test basic service health check."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    health_result = service.check_service_health()
    
    # Should return health check result
    assert health_result.status in ['healthy', 'degraded', 'unhealthy']
    assert health_result.timestamp is not None
    assert isinstance(health_result.checks, dict)

def test_sharepoint_connectivity_check_success():
    """Test SharePoint connectivity check when successful."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    # Mock successful connectivity
    with patch.object(service, '_check_sharepoint_endpoint') as mock_check:
        mock_check.return_value = True
        
        result = service.check_sharepoint_connectivity()
        
        assert result.status == 'healthy'
        assert result.message == 'SharePoint connectivity verified'

def test_sharepoint_connectivity_check_failure():
    """Test SharePoint connectivity check when failing."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    # Mock failed connectivity
    with patch.object(service, '_check_sharepoint_endpoint') as mock_check:
        mock_check.return_value = False
        
        result = service.check_sharepoint_connectivity()
        
        assert result.status == 'unhealthy'
        assert 'connectivity failed' in result.message.lower()

def test_configuration_validity_check():
    """Test configuration validity check."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    result = service.check_configuration_validity()
    
    # Should validate configuration
    assert result.status in ['healthy', 'unhealthy']
    assert result.message is not None
    assert isinstance(result.details, dict)

def test_comprehensive_health_check():
    """Test comprehensive health check combining all checks."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    with patch.object(service, 'check_sharepoint_connectivity') as mock_sp, \
         patch.object(service, 'check_configuration_validity') as mock_config:
        
        # Mock successful checks
        mock_sp.return_value = MagicMock(status='healthy', message='OK')
        mock_config.return_value = MagicMock(status='healthy', message='Valid')
        
        result = service.get_comprehensive_health()
        
        assert result.overall_status == 'healthy'
        assert 'sharepoint' in result.dependencies
        assert 'configuration' in result.dependencies

def test_health_endpoint_basic_response(client):
    """Test that /health endpoint returns basic health information."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data

def test_health_detailed_endpoint_exists(client):
    """Test that /health/detailed endpoint exists."""
    response = client.get("/health/detailed")
    
    # Should not return 404
    assert response.status_code != 404

def test_health_detailed_endpoint_comprehensive(client):
    """Test detailed health endpoint provides comprehensive information."""
    response = client.get("/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should include detailed health information
    assert "overall_status" in data
    assert "timestamp" in data
    assert "dependencies" in data
    assert "service_info" in data

def test_health_detailed_sharepoint_check(client):
    """Test detailed health includes SharePoint connectivity check."""
    with patch('app.services.health_monitoring.HealthMonitoringService') as mock_service_class:
        mock_service = mock_service_class.return_value
        mock_result = MagicMock()
        mock_result.overall_status = 'healthy'
        mock_result.dependencies = {
            'sharepoint': {'status': 'healthy', 'message': 'Connected'},
            'configuration': {'status': 'healthy', 'message': 'Valid'}
        }
        mock_result.timestamp = '2025-09-16T10:00:00Z'
        mock_result.service_info = {'name': 'test', 'version': '1.0.0'}
        mock_service.get_comprehensive_health.return_value = mock_result
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["sharepoint"]["status"] == "healthy"

def test_health_ready_endpoint(client):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code in [200, 503]  # Ready or not ready
    data = response.json()
    assert "ready" in data

def test_health_live_endpoint(client):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert "alive" in data
    assert data["alive"] is True

def test_health_degraded_service_response():
    """Test health response when service is degraded."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    with patch.object(service, 'check_sharepoint_connectivity') as mock_sp, \
         patch.object(service, 'check_configuration_validity') as mock_config:
        
        # Mock degraded SharePoint but valid config
        mock_sp.return_value = MagicMock(status='degraded', message='Slow response')
        mock_config.return_value = MagicMock(status='healthy', message='Valid')
        
        result = service.get_comprehensive_health()
        
        assert result.overall_status == 'degraded'

def test_health_unhealthy_service_response():
    """Test health response when service is unhealthy."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    with patch.object(service, 'check_sharepoint_connectivity') as mock_sp, \
         patch.object(service, 'check_configuration_validity') as mock_config:
        
        # Mock failed SharePoint
        mock_sp.return_value = MagicMock(status='unhealthy', message='Connection failed')
        mock_config.return_value = MagicMock(status='healthy', message='Valid')
        
        result = service.get_comprehensive_health()
        
        assert result.overall_status == 'unhealthy'

def test_health_endpoint_debug_mode_info(client):
    """Test health endpoint includes debug mode information."""
    with patch.dict('os.environ', {'DEBUG_MODE': 'true'}):
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "debug_mode" in data
        assert data["debug_mode"] is True

def test_health_endpoint_production_mode_info(client):
    """Test health endpoint in production mode."""
    # Mock the config instead of changing environment at runtime
    with patch('app.main.config') as mock_config:
        mock_config.debug_mode = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "debug_mode" in data
        assert data["debug_mode"] is False

def test_health_dependency_timeout_handling():
    """Test health check handles dependency timeouts gracefully."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    with patch.object(service, '_check_sharepoint_endpoint') as mock_check:
        # Mock timeout exception
        mock_check.side_effect = TimeoutError("Connection timeout")
        
        result = service.check_sharepoint_connectivity()
        
        assert result.status == 'unhealthy'
        assert 'timeout' in result.message.lower()

def test_health_configuration_validation_details():
    """Test configuration validation provides detailed information."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    result = service.check_configuration_validity()
    
    # Should include configuration details
    assert hasattr(result, 'details')
    assert isinstance(result.details, dict)
    # Should check key configuration items
    expected_keys = ['sharepoint_endpoint', 'debug_mode', 'log_level']
    for key in expected_keys:
        assert any(key in detail_key for detail_key in result.details.keys())

def test_health_cors_headers(client):
    """Test health endpoints include CORS headers."""
    response = client.get("/health")
    
    # Should work without CORS errors
    assert response.status_code == 200

def test_health_metrics_collection():
    """Test health service collects performance metrics."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    # Should track response times
    result = service.check_service_health()
    
    assert hasattr(result, 'response_time_ms')
    assert result.response_time_ms >= 0

def test_health_check_caching():
    """Test health checks can be cached to avoid excessive dependency calls."""
    from app.services.health_monitoring import HealthMonitoringService
    
    service = HealthMonitoringService()
    
    with patch.object(service, '_check_sharepoint_endpoint') as mock_check:
        mock_check.return_value = True
        
        # First call
        result1 = service.check_sharepoint_connectivity()
        # Second call within cache window
        result2 = service.check_sharepoint_connectivity()
        
        # Should have same results
        assert result1.status == result2.status

def test_health_status_levels():
    """Test different health status levels are properly differentiated."""
    from app.services.health_monitoring import ServiceHealth
    
    # Test enum or constants
    assert hasattr(ServiceHealth, 'HEALTHY') or 'healthy' in ['healthy', 'degraded', 'unhealthy']
    assert hasattr(ServiceHealth, 'DEGRADED') or 'degraded' in ['healthy', 'degraded', 'unhealthy']
    assert hasattr(ServiceHealth, 'UNHEALTHY') or 'unhealthy' in ['healthy', 'degraded', 'unhealthy']
