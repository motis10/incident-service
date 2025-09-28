"""
Test configuration service for environment-based configuration management.
"""
import os
import pytest
from unittest.mock import patch
from pathlib import Path
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_config_service_import():
    """Test that config service can be imported."""
    try:
        from app.core.config import ConfigService, AppConfig
        assert ConfigService is not None
        assert AppConfig is not None
    except ImportError:
        pytest.fail("Could not import ConfigService and AppConfig")

def test_config_service_initialization():
    """Test that ConfigService can be initialized."""
    from app.core.config import ConfigService
    
    config_service = ConfigService()
    assert config_service is not None

def test_default_configuration_values():
    """Test that configuration service provides sensible defaults."""
    from app.core.config import ConfigService
    
    with patch.dict(os.environ, {}, clear=True):
        config_service = ConfigService()
        config = config_service.get_config()
        
        assert config.debug_mode is True  # Default to debug mode
        assert config.environment == "development"  # Default environment
        assert config.port == 8000  # Default port
        assert config.log_level == "INFO"  # Default log level

def test_environment_variable_override():
    """Test that environment variables override defaults."""
    from app.core.config import ConfigService
    
    test_env = {
        'DEBUG_MODE': 'false',
        'ENVIRONMENT': 'production',
        'PORT': '9000',
        'LOG_LEVEL': 'WARNING',
        'NETANYA_ENDPOINT': 'https://custom.endpoint.com'
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        config_service = ConfigService()
        config = config_service.get_config()
        
        assert config.debug_mode is False
        assert config.environment == "production"
        assert config.port == 9000
        assert config.log_level == "WARNING"
        assert config.netanya_endpoint == "https://custom.endpoint.com"

def test_debug_mode_detection():
    """Test debug mode detection logic."""
    from app.core.config import ConfigService
    
    # Test debug mode true
    with patch.dict(os.environ, {'DEBUG_MODE': 'true'}, clear=True):
        config_service = ConfigService()
        assert config_service.is_debug_mode() is True
    
    # Test debug mode false
    with patch.dict(os.environ, {'DEBUG_MODE': 'false'}, clear=True):
        config_service = ConfigService()
        assert config_service.is_debug_mode() is False
    
    # Test default (should be true for development)
    with patch.dict(os.environ, {}, clear=True):
        config_service = ConfigService()
        assert config_service.is_debug_mode() is True

def test_sharepoint_endpoint_configuration():
    """Test SharePoint endpoint configuration logic."""
    from app.core.config import ConfigService
    
    # Test custom endpoint
    with patch.dict(os.environ, {'NETANYA_ENDPOINT': 'https://custom.sharepoint.com'}, clear=True):
        config_service = ConfigService()
        assert config_service.get_sharepoint_endpoint() == "https://custom.sharepoint.com"
    
    # Test default endpoint
    with patch.dict(os.environ, {}, clear=True):
        config_service = ConfigService()
        endpoint = config_service.get_sharepoint_endpoint()
        assert "netanya.muni.il" in endpoint
        assert "incidents.ashx" in endpoint

def test_configuration_validation():
    """Test configuration validation for required parameters."""
    from app.core.config import ConfigService, ConfigurationError
    
    # Test valid configuration
    valid_env = {
        'ENVIRONMENT': 'production',
        'DEBUG_MODE': 'false'
    }
    
    with patch.dict(os.environ, valid_env, clear=True):
        config_service = ConfigService()
        # Should not raise exception
        config_service.validate_environment()

def test_fail_fast_validation():
    """Test fail-fast startup validation with clear error messages."""
    from app.core.config import ConfigService, ConfigurationError
    
    # Test invalid port during initialization (fail-fast)
    invalid_env = {
        'PORT': 'not_a_number'
    }
    
    with patch.dict(os.environ, invalid_env, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            config_service = ConfigService()
        
        # Check that error message is clear and helpful
        error_message = str(exc_info.value)
        assert "not_a_number" in error_message
    
    # Test invalid environment through validation method
    invalid_env2 = {
        'ENVIRONMENT': 'invalid_env'
    }
    
    with patch.dict(os.environ, invalid_env2, clear=True):
        config_service = ConfigService()
        with pytest.raises(ConfigurationError) as exc_info:
            config_service.validate_environment()
        
        # Check that error message is clear and helpful
        error_message = str(exc_info.value)
        assert "invalid_env" in error_message

def test_production_mode_https_enforcement():
    """Test that production mode enforces HTTPS endpoints."""
    from app.core.config import ConfigService, ConfigurationError
    
    # Test production mode with HTTP endpoint (should fail)
    prod_env = {
        'ENVIRONMENT': 'production',
        'DEBUG_MODE': 'false',
        'NETANYA_ENDPOINT': 'http://insecure.endpoint.com'
    }
    
    with patch.dict(os.environ, prod_env, clear=True):
        config_service = ConfigService()
        with pytest.raises(ConfigurationError) as exc_info:
            config_service.validate_environment()
        
        assert "HTTPS" in str(exc_info.value) or "secure" in str(exc_info.value)

def test_config_immutability():
    """Test that configuration is immutable during runtime."""
    from app.core.config import ConfigService
    
    config_service = ConfigService()
    config1 = config_service.get_config()
    config2 = config_service.get_config()
    
    # Should return the same configuration object (cached within instance)
    assert config1 is config2
    
    # Different instances should have same values but different objects
    config_service2 = ConfigService()
    config3 = config_service2.get_config()
    assert config1.debug_mode == config3.debug_mode
    assert config1.environment == config3.environment
