"""
Comprehensive tests for configuration loading with environment variable scenarios.
"""
import pytest
import os
from pathlib import Path
import sys
from unittest.mock import patch, mock_open, MagicMock
import tempfile

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.core.config import ConfigService, AppConfig
from pydantic import ValidationError


class TestAppConfigValidation:
    """Test AppConfig model validation scenarios."""
    
    def test_valid_config_creation(self):
        """Test creating valid configuration."""
        config = AppConfig(
            environment="production",
            debug_mode=False,
            log_level="INFO",
            port=8000
        )
        
        assert config.environment == "production"
        assert config.debug_mode is False
        assert config.log_level == "INFO"
        assert config.port == 8000
    
    def test_default_values(self):
        """Test default configuration values."""
        config = AppConfig()
        
        assert config.environment == "development"
        assert config.debug_mode is True
        assert config.log_level == "DEBUG"
        assert config.port == 8000
    
    def test_invalid_environment_validation(self):
        """Test validation fails for invalid environment."""
        with pytest.raises(ValidationError):
            AppConfig(environment="invalid_env")
    
    def test_invalid_log_level_validation(self):
        """Test validation fails for invalid log level."""
        with pytest.raises(ValidationError):
            AppConfig(log_level="INVALID_LEVEL")
    
    def test_port_range_validation(self):
        """Test port number validation."""
        # Valid ports
        valid_ports = [80, 443, 8000, 8080, 9000]
        for port in valid_ports:
            config = AppConfig(port=port)
            assert config.port == port
        
        # Invalid ports
        invalid_ports = [-1, 0, 70000]
        for port in invalid_ports:
            with pytest.raises(ValidationError):
                AppConfig(port=port)
    
    def test_debug_mode_type_conversion(self):
        """Test debug mode boolean conversion."""
        # Test various boolean representations
        config1 = AppConfig(debug_mode=True)
        assert config1.debug_mode is True
        
        config2 = AppConfig(debug_mode=False)
        assert config2.debug_mode is False
    
    def test_environment_specific_defaults(self):
        """Test environment-specific default behaviors."""
        # Production environment defaults
        prod_config = AppConfig(environment="production")
        assert prod_config.debug_mode is True  # Default from model
        
        # Development environment defaults
        dev_config = AppConfig(environment="development")
        assert dev_config.debug_mode is True


class TestConfigServiceBasics:
    """Test basic ConfigService functionality."""
    
    def test_config_service_initialization(self):
        """Test ConfigService can be initialized."""
        service = ConfigService()
        assert service is not None
    
    def test_get_config_returns_app_config(self):
        """Test get_config returns AppConfig instance."""
        service = ConfigService()
        config = service.get_config()
        assert isinstance(config, AppConfig)
    
    def test_config_service_singleton_behavior(self):
        """Test ConfigService behaves like a singleton."""
        service1 = ConfigService()
        service2 = ConfigService()
        
        config1 = service1.get_config()
        config2 = service2.get_config()
        
        # Should return the same configuration
        assert config1.model_dump() == config2.model_dump()
    
    def test_sharepoint_endpoint_getter(self):
        """Test SharePoint endpoint getter method."""
        service = ConfigService()
        endpoint = service.get_sharepoint_endpoint()
        
        # Should return a string (even if default)
        assert isinstance(endpoint, str)
        assert len(endpoint) > 0


class TestEnvironmentVariableHandling:
    """Test environment variable configuration scenarios."""
    
    def test_environment_variable_override(self):
        """Test environment variables override defaults."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG_MODE': 'false',
            'LOG_LEVEL': 'ERROR',
            'PORT': '9000'
        }):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "production"
            assert config.debug_mode is False
            assert config.log_level == "ERROR"
            assert config.port == 9000
    
    def test_boolean_environment_variable_parsing(self):
        """Test boolean environment variable parsing."""
        boolean_test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
        ]
        
        for env_value, expected_bool in boolean_test_cases:
            with patch.dict(os.environ, {'DEBUG_MODE': env_value}):
                service = ConfigService()
                config = service.get_config()
                assert config.debug_mode is expected_bool
    
    def test_integer_environment_variable_parsing(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {'PORT': '3000'}):
            service = ConfigService()
            config = service.get_config()
            assert config.port == 3000
            assert isinstance(config.port, int)
    
    def test_invalid_environment_variable_handling(self):
        """Test handling of invalid environment variable values."""
        # Invalid port number
        with patch.dict(os.environ, {'PORT': 'not_a_number'}):
            with pytest.raises(ValidationError):
                service = ConfigService()
                service.get_config()
        
        # Invalid environment
        with patch.dict(os.environ, {'ENVIRONMENT': 'invalid_env'}):
            with pytest.raises(ValidationError):
                service = ConfigService()
                service.get_config()
    
    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing."""
        # Clear relevant environment variables
        env_vars_to_clear = ['ENVIRONMENT', 'DEBUG_MODE', 'LOG_LEVEL', 'PORT']
        
        with patch.dict(os.environ, {}, clear=True):
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            service = ConfigService()
            config = service.get_config()
            
            # Should use defaults
            assert config.environment == "development"
            assert config.debug_mode is True
            assert config.log_level == "DEBUG"
            assert config.port == 8000
    
    def test_sharepoint_endpoint_from_environment(self):
        """Test SharePoint endpoint configuration from environment."""
        test_endpoint = "https://test.sharepoint.com/api/incidents"
        
        with patch.dict(os.environ, {'SHAREPOINT_ENDPOINT': test_endpoint}):
            service = ConfigService()
            endpoint = service.get_sharepoint_endpoint()
            assert endpoint == test_endpoint


class TestConfigurationValidation:
    """Test configuration validation scenarios."""
    
    def test_production_environment_validation(self):
        """Test production environment configuration validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG_MODE': 'false',
            'LOG_LEVEL': 'INFO'
        }):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "production"
            assert config.debug_mode is False
            # In production, debug should be disabled
    
    def test_development_environment_validation(self):
        """Test development environment configuration validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG_MODE': 'true',
            'LOG_LEVEL': 'DEBUG'
        }):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "development"
            assert config.debug_mode is True
    
    def test_testing_environment_validation(self):
        """Test testing environment configuration validation."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'testing',
            'DEBUG_MODE': 'false',
            'LOG_LEVEL': 'WARNING'
        }):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "testing"
            assert config.log_level == "WARNING"
    
    def test_security_sensitive_configuration(self):
        """Test security-sensitive configuration scenarios."""
        # Test that sensitive values are handled appropriately
        sensitive_endpoint = "https://internal.sharepoint.company.com/api"
        
        with patch.dict(os.environ, {
            'SHAREPOINT_ENDPOINT': sensitive_endpoint,
            'ENVIRONMENT': 'production'
        }):
            service = ConfigService()
            endpoint = service.get_sharepoint_endpoint()
            
            # Endpoint should be retrievable
            assert endpoint == sensitive_endpoint
    
    def test_configuration_immutability(self):
        """Test that configuration objects are immutable."""
        service = ConfigService()
        config = service.get_config()
        
        # Attempt to modify configuration
        original_debug = config.debug_mode
        
        # Pydantic models are immutable by default in v2
        with pytest.raises(ValidationError):
            config.debug_mode = not original_debug


class TestConfigurationCaching:
    """Test configuration caching behavior."""
    
    def test_config_caching(self):
        """Test that configuration is cached properly."""
        service = ConfigService()
        
        # First call
        config1 = service.get_config()
        
        # Second call should return cached result
        config2 = service.get_config()
        
        # Should be the same object/data
        assert config1.model_dump() == config2.model_dump()
    
    def test_config_cache_with_environment_changes(self):
        """Test configuration caching with environment changes."""
        # First configuration
        with patch.dict(os.environ, {'DEBUG_MODE': 'true'}):
            service1 = ConfigService()
            config1 = service1.get_config()
            assert config1.debug_mode is True
        
        # New service instance with different environment
        with patch.dict(os.environ, {'DEBUG_MODE': 'false'}):
            service2 = ConfigService()
            config2 = service2.get_config()
            assert config2.debug_mode is False


class TestConfigurationErrorHandling:
    """Test configuration error handling scenarios."""
    
    def test_malformed_environment_variables(self):
        """Test handling of malformed environment variables."""
        malformed_cases = [
            ('LOG_LEVEL', 'INVALID_LEVEL'),
            ('PORT', 'not_a_port'),
            ('DEBUG_MODE', 'maybe'),
            ('ENVIRONMENT', ''),
        ]
        
        for var_name, var_value in malformed_cases:
            with patch.dict(os.environ, {var_name: var_value}):
                with pytest.raises(ValidationError):
                    service = ConfigService()
                    service.get_config()
    
    def test_configuration_validation_errors(self):
        """Test comprehensive validation error scenarios."""
        # Multiple invalid values
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'invalid',
            'LOG_LEVEL': 'WRONG',
            'PORT': '-1'
        }):
            with pytest.raises(ValidationError) as exc_info:
                service = ConfigService()
                service.get_config()
            
            # Should contain validation errors
            errors = exc_info.value.errors()
            assert len(errors) > 0
    
    def test_missing_required_configuration(self):
        """Test behavior when required configuration is missing."""
        # Clear all environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Should still work with defaults
            service = ConfigService()
            config = service.get_config()
            assert config is not None
    
    @patch('app.core.config.logger')
    def test_configuration_logging(self, mock_logger):
        """Test that configuration events are logged."""
        service = ConfigService()
        config = service.get_config()
        
        # Verify logging occurred
        assert mock_logger.info.called or mock_logger.debug.called
        assert config is not None


class TestMultipleEnvironmentScenarios:
    """Test complex multi-environment scenarios."""
    
    def test_environment_switching(self):
        """Test switching between different environments."""
        environments = [
            ('development', True, 'DEBUG'),
            ('testing', False, 'INFO'),
            ('production', False, 'WARNING'),
        ]
        
        for env_name, expected_debug, expected_log_level in environments:
            with patch.dict(os.environ, {
                'ENVIRONMENT': env_name,
                'DEBUG_MODE': str(expected_debug).lower(),
                'LOG_LEVEL': expected_log_level
            }):
                service = ConfigService()
                config = service.get_config()
                
                assert config.environment == env_name
                assert config.debug_mode == expected_debug
                assert config.log_level == expected_log_level
    
    def test_configuration_inheritance(self):
        """Test configuration value inheritance and overrides."""
        # Base configuration
        base_env = {
            'ENVIRONMENT': 'development',
            'PORT': '8000'
        }
        
        # Override specific values
        override_env = {
            **base_env,
            'DEBUG_MODE': 'false',
            'LOG_LEVEL': 'ERROR'
        }
        
        with patch.dict(os.environ, override_env):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "development"  # From base
            assert config.port == 8000                  # From base
            assert config.debug_mode is False           # Overridden
            assert config.log_level == "ERROR"          # Overridden
    
    def test_partial_configuration_override(self):
        """Test partial configuration override scenarios."""
        # Set only some environment variables
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'LOG_LEVEL': 'INFO'
            # DEBUG_MODE and PORT use defaults
        }):
            service = ConfigService()
            config = service.get_config()
            
            assert config.environment == "production"  # Overridden
            assert config.log_level == "INFO"          # Overridden
            assert config.debug_mode is True           # Default
            assert config.port == 8000                 # Default


class TestConfigurationIntegration:
    """Test configuration integration with other components."""
    
    def test_config_service_with_sharepoint_client(self):
        """Test ConfigService integration with SharePoint client configuration."""
        test_endpoint = "https://test.netanya.sharepoint.com/api"
        
        with patch.dict(os.environ, {
            'SHAREPOINT_ENDPOINT': test_endpoint,
            'ENVIRONMENT': 'testing'
        }):
            service = ConfigService()
            config = service.get_config()
            endpoint = service.get_sharepoint_endpoint()
            
            assert config.environment == "testing"
            assert endpoint == test_endpoint
    
    def test_config_service_thread_safety(self):
        """Test ConfigService thread safety."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def get_config_in_thread(thread_id):
            try:
                service = ConfigService()
                config = service.get_config()
                results_queue.put((thread_id, config.environment, config.debug_mode))
            except Exception as e:
                results_queue.put((thread_id, "ERROR", str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_config_in_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 5
        # All threads should get consistent configuration
        first_result = results[0]
        for result in results[1:]:
            assert result[1] == first_result[1]  # Same environment
            assert result[2] == first_result[2]  # Same debug mode
    
    def test_config_service_performance(self):
        """Test ConfigService performance with repeated calls."""
        import time
        
        service = ConfigService()
        
        # Measure time for multiple config retrievals
        start_time = time.time()
        for _ in range(100):
            config = service.get_config()
        end_time = time.time()
        
        # Should complete quickly due to caching
        total_time = end_time - start_time
        assert total_time < 1.0  # Should take less than 1 second for 100 calls
    
    def test_config_with_mock_environment(self):
        """Test configuration with completely mocked environment."""
        mock_env = {
            'ENVIRONMENT': 'testing',
            'DEBUG_MODE': 'true',
            'LOG_LEVEL': 'DEBUG',
            'PORT': '5000',
            'SHAREPOINT_ENDPOINT': 'https://mock.sharepoint.test/api'
        }
        
        with patch.dict(os.environ, mock_env, clear=True):
            service = ConfigService()
            config = service.get_config()
            endpoint = service.get_sharepoint_endpoint()
            
            assert config.environment == "testing"
            assert config.debug_mode is True
            assert config.log_level == "DEBUG"
            assert config.port == 5000
            assert endpoint == "https://mock.sharepoint.test/api"
