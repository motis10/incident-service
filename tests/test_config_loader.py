"""
Test configuration loader functionality.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
import sys

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_config_loader_import():
    """Test that configuration loader can be imported."""
    try:
        from app.core.config_loader import ConfigurationLoader, EnvironmentConfig
        assert ConfigurationLoader is not None
        assert EnvironmentConfig is not None
    except ImportError as e:
        pytest.skip(f"PyYAML not available: {e}")

def test_environment_detection():
    """Test automatic environment detection."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    # Test default detection
    with patch.dict(os.environ, {}, clear=True):
        env = loader._detect_environment()
        assert env == "development"
    
    # Test ENVIRONMENT variable
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        env = loader._detect_environment()
        assert env == "production"
    
    # Test ENV variable (fallback)
    with patch.dict(os.environ, {"ENV": "testing"}):
        env = loader._detect_environment()
        assert env == "testing"
    
    # Test environment mapping
    with patch.dict(os.environ, {"ENVIRONMENT": "prod"}):
        env = loader._detect_environment()
        assert env == "production"

def test_environment_value_conversion():
    """Test environment variable value conversion."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    # Test boolean conversion
    assert loader._convert_env_value("true", "debug_mode") is True
    assert loader._convert_env_value("false", "debug_mode") is False
    assert loader._convert_env_value("1", "debug_mode") is True
    assert loader._convert_env_value("0", "debug_mode") is False
    
    # Test integer conversion
    assert loader._convert_env_value("8000", "port") == 8000
    assert loader._convert_env_value("30", "timeout") == 30
    
    # Test string values
    assert loader._convert_env_value("INFO", "log_level") == "INFO"

def test_config_object_building():
    """Test building configuration object from data."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    config_data = {
        "app": {
            "name": "Test Service",
            "debug_mode": True,
            "port": 9000
        },
        "sharepoint": {
            "endpoint": "http://test.example.com",
            "timeout": 45
        }
    }
    
    config = loader._build_config_object(config_data)
    
    assert config.app.name == "Test Service"
    assert config.app.debug_mode is True
    assert config.app.port == 9000
    assert config.sharepoint.endpoint == "http://test.example.com"
    assert config.sharepoint.timeout == 45

def test_configuration_validation():
    """Test configuration validation."""
    from app.core.config_loader import ConfigurationLoader, EnvironmentConfig, AppSettings, SharePointSettings
    
    loader = ConfigurationLoader()
    
    # Test valid configuration
    valid_config = EnvironmentConfig()
    valid_config.app = AppSettings(port=8000, environment="development")
    valid_config.sharepoint = SharePointSettings(endpoint="http://test.com", timeout=30)
    
    # Should not raise
    loader._validate_config(valid_config)
    
    # Test invalid port
    invalid_config = EnvironmentConfig()
    invalid_config.app = AppSettings(port=99999, environment="development")
    invalid_config.sharepoint = SharePointSettings(endpoint="http://test.com", timeout=30)
    
    with pytest.raises(ValueError, match="Invalid port number"):
        loader._validate_config(invalid_config)
    
    # Test missing SharePoint endpoint
    invalid_config2 = EnvironmentConfig()
    invalid_config2.app = AppSettings(port=8000, environment="development")
    invalid_config2.sharepoint = SharePointSettings(endpoint="", timeout=30)
    
    with pytest.raises(ValueError, match="SharePoint endpoint is required"):
        loader._validate_config(invalid_config2)

def test_production_validation():
    """Test production-specific validation rules."""
    from app.core.config_loader import ConfigurationLoader, EnvironmentConfig, AppSettings, SecuritySettings
    
    loader = ConfigurationLoader()
    
    # Production config with debug mode enabled (should fail)
    prod_config = EnvironmentConfig()
    prod_config.app = AppSettings(environment="production", debug_mode=True)
    prod_config.sharepoint.endpoint = "http://test.com"
    prod_config.security = SecuritySettings(include_docs=True)
    
    with pytest.raises(ValueError, match="Debug mode should be disabled"):
        loader._validate_config(prod_config)

def test_config_summary():
    """Test configuration summary generation."""
    from app.core.config_loader import ConfigurationLoader, EnvironmentConfig
    
    loader = ConfigurationLoader()
    config = EnvironmentConfig()
    
    summary = loader.get_config_summary(config)
    
    assert "environment" in summary
    assert "debug_mode" in summary
    assert "port" in summary
    assert "features_enabled" in summary
    assert isinstance(summary["features_enabled"], dict)

def test_yaml_config_loading():
    """Test loading YAML configuration files."""
    from app.core.config_loader import ConfigurationLoader
    
    # Create temporary YAML config
    config_data = {
        "app": {
            "name": "Test Service",
            "debug_mode": True
        },
        "sharepoint": {
            "endpoint": "http://test.com"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_file = f.name
    
    try:
        loader = ConfigurationLoader()
        
        # Mock the config file path
        with patch.object(loader, 'config_dir', Path(temp_file).parent):
            with patch.object(Path, 'exists', return_value=True):
                with patch('builtins.open', open):
                    result = loader._load_yaml_config(Path(temp_file).stem)
        
        assert result["app"]["name"] == "Test Service"
        assert result["sharepoint"]["endpoint"] == "http://test.com"
    
    finally:
        # Clean up
        os.unlink(temp_file)

def test_environment_overrides():
    """Test environment variable overrides."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    base_config = {
        "app": {
            "debug_mode": False,
            "port": 8000
        },
        "sharepoint": {
            "endpoint": "http://default.com"
        }
    }
    
    with patch.dict(os.environ, {
        "DEBUG_MODE": "true",
        "PORT": "9000",
        "SHAREPOINT_ENDPOINT": "http://override.com"
    }):
        result = loader._apply_env_overrides(base_config.copy())
    
    assert result["app"]["debug_mode"] is True
    assert result["app"]["port"] == 9000
    assert result["sharepoint"]["endpoint"] == "http://override.com"

def test_project_root_detection():
    """Test project root directory detection."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    project_root = loader._find_project_root()
    
    # Should find a reasonable project root
    assert isinstance(project_root, Path)
    assert project_root.exists()

def test_missing_config_file_handling():
    """Test handling of missing configuration files."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    # Mock a non-existent config directory
    with patch.object(loader, 'config_dir', Path("/nonexistent")):
        result = loader._load_yaml_config("nonexistent")
        assert result == {}  # Should return empty dict for missing files

def test_invalid_yaml_handling():
    """Test handling of invalid YAML files."""
    from app.core.config_loader import ConfigurationLoader
    
    # Create temporary invalid YAML file
    invalid_yaml = "invalid: yaml: content: ["
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(invalid_yaml)
        temp_file = f.name
    
    try:
        loader = ConfigurationLoader()
        
        with patch.object(loader, 'config_dir', Path(temp_file).parent):
            with pytest.raises(ValueError, match="Invalid YAML configuration"):
                loader._load_yaml_config(Path(temp_file).stem)
    
    finally:
        os.unlink(temp_file)

def test_full_config_loading_workflow():
    """Test the complete configuration loading workflow."""
    from app.core.config_loader import ConfigurationLoader
    
    # Create a temporary config file
    config_data = {
        "app": {
            "name": "Integration Test Service",
            "environment": "testing",
            "debug_mode": True,
            "port": 8000
        },
        "sharepoint": {
            "endpoint": "http://test-sharepoint.com",
            "timeout": 30,
            "mock_mode": True
        },
        "features": {
            "health_monitoring": True,
            "request_logging": False
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "testing.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        loader = ConfigurationLoader()
        
        # Mock the config directory
        with patch.object(loader, 'config_dir', Path(temp_dir)):
            config = loader.load_environment_config("testing")
        
        # Verify the loaded configuration
        assert config.app.name == "Integration Test Service"
        assert config.app.environment == "testing"
        assert config.sharepoint.endpoint == "http://test-sharepoint.com"
        assert config.features.health_monitoring is True
        assert config.features.request_logging is False

def test_unknown_config_keys_handling():
    """Test handling of unknown configuration keys."""
    from app.core.config_loader import ConfigurationLoader
    
    loader = ConfigurationLoader()
    
    config_data = {
        "app": {
            "name": "Test Service",
            "unknown_key": "unknown_value"  # Unknown key
        }
    }
    
    # Should not raise error, but should log warning
    config = loader._build_config_object(config_data)
    assert config.app.name == "Test Service"
    # Unknown key should be ignored

def test_config_dataclass_defaults():
    """Test that configuration dataclasses have proper defaults."""
    from app.core.config_loader import (
        AppSettings, SharePointSettings, LoggingSettings, 
        CorsSettings, SecuritySettings, FeatureSettings
    )
    
    # Test default values
    app_settings = AppSettings()
    assert app_settings.name == "Netanya Incident Service"
    assert app_settings.debug_mode is True
    assert app_settings.port == 8000
    
    sharepoint_settings = SharePointSettings()
    assert sharepoint_settings.timeout == 30
    assert sharepoint_settings.mock_mode is True
    
    cors_settings = CorsSettings()
    assert isinstance(cors_settings.allow_origins, list)
    assert cors_settings.allow_credentials is True
