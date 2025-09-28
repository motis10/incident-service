"""
Enhanced configuration loader with environment-specific YAML support.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger("config_loader")


@dataclass
class AppSettings:
    """Application-level settings."""
    name: str = "Netanya Incident Service"
    version: str = "1.0.0"
    environment: str = "development"
    debug_mode: bool = True
    log_level: str = "INFO"
    port: int = 8000


@dataclass
class SharePointSettings:
    """SharePoint integration settings."""
    endpoint: str = "http://localhost:8080/api/incidents"
    timeout: int = 30
    retry_attempts: int = 3
    mock_mode: bool = True


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True


@dataclass
class CorsSettings:
    """CORS configuration settings."""
    allow_origins: list = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: list = field(default_factory=lambda: ["GET", "POST", "OPTIONS"])
    allow_headers: list = field(default_factory=lambda: ["*"])


@dataclass
class RateLimitingSettings:
    """Rate limiting configuration."""
    api_requests_per_minute: int = 60
    health_requests_per_minute: int = 120


@dataclass
class SecuritySettings:
    """Security configuration settings."""
    enforce_https: bool = False
    include_docs: bool = True
    cors_permissive: bool = True


@dataclass
class FeatureSettings:
    """Feature flags configuration."""
    health_monitoring: bool = True
    request_logging: bool = True
    error_tracking: bool = True
    metrics_collection: bool = False


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""
    app: AppSettings = field(default_factory=AppSettings)
    sharepoint: SharePointSettings = field(default_factory=SharePointSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    cors: CorsSettings = field(default_factory=CorsSettings)
    rate_limiting: RateLimitingSettings = field(default_factory=RateLimitingSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    features: FeatureSettings = field(default_factory=FeatureSettings)
    _raw_config: Dict[str, Any] = field(default_factory=dict)


class ConfigurationLoader:
    """
    Enhanced configuration loader that supports:
    - Environment-specific YAML files
    - Environment variable overrides
    - Configuration validation
    - Automatic environment detection
    """
    
    def __init__(self):
        """Initialize configuration loader."""
        self.project_root = self._find_project_root()
        self.config_dir = self.project_root / "config"
        logger.info(f"Configuration loader initialized. Config dir: {self.config_dir}")
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path(__file__).parent
        
        # Look for project markers (requirements.txt, docker-compose.yml, etc.)
        while current != current.parent:
            markers = ["requirements.txt", "docker-compose.yml", "Dockerfile", ".git"]
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        
        # Fallback to a reasonable default
        return Path(__file__).parent.parent.parent.parent
    
    def load_environment_config(self, environment: Optional[str] = None) -> EnvironmentConfig:
        """
        Load configuration for the specified environment.
        
        Args:
            environment: Environment name (development, production, testing)
                        If None, will auto-detect from ENVIRONMENT variable
        
        Returns:
            EnvironmentConfig object with all settings
        """
        if environment is None:
            environment = self._detect_environment()
        
        logger.info(f"Loading configuration for environment: {environment}")
        
        # Load base configuration
        config_data = self._load_yaml_config(environment)
        
        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)
        
        # Build configuration object
        env_config = self._build_config_object(config_data)
        
        # Validate configuration
        self._validate_config(env_config)
        
        logger.info(f"Configuration loaded successfully for {environment}")
        return env_config
    
    def _detect_environment(self) -> str:
        """Auto-detect the current environment."""
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
        
        # Map common variations
        env_map = {
            "dev": "development",
            "prod": "production", 
            "test": "testing",
            "stage": "staging",
            "staging": "staging"
        }
        
        return env_map.get(env, env)
    
    def _load_yaml_config(self, environment: str) -> Dict[str, Any]:
        """Load YAML configuration file for the environment."""
        config_file = self.config_dir / f"{environment}.yml"
        
        if not config_file.exists():
            logger.warning(f"Configuration file not found: {config_file}")
            logger.info("Using default configuration")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            logger.debug(f"Loaded configuration from {config_file}")
            return config_data
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
            raise
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Environment variable mapping
        env_mappings = {
            "DEBUG_MODE": ("app", "debug_mode"),
            "LOG_LEVEL": ("app", "log_level"),
            "PORT": ("app", "port"),
            "SHAREPOINT_ENDPOINT": ("sharepoint", "endpoint"),
            "SHAREPOINT_TIMEOUT": ("sharepoint", "timeout"),
            "ENVIRONMENT": ("app", "environment"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Ensure the section exists
                if section not in config_data:
                    config_data[section] = {}
                
                # Convert value to appropriate type
                config_data[section][key] = self._convert_env_value(value, key)
                logger.debug(f"Applied environment override: {env_var}={value}")
        
        return config_data
    
    def _convert_env_value(self, value: str, key: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversions
        if key in ["debug_mode", "mock_mode", "enforce_https", "include_docs", "cors_permissive"]:
            return value.lower() in ("true", "1", "yes", "on")
        
        # Integer conversions
        if key in ["port", "timeout", "retry_attempts", "api_requests_per_minute", "health_requests_per_minute"]:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Invalid integer value for {key}: {value}")
                return value
        
        # String value (default)
        return value
    
    def _build_config_object(self, config_data: Dict[str, Any]) -> EnvironmentConfig:
        """Build EnvironmentConfig object from configuration data."""
        config = EnvironmentConfig()
        config._raw_config = config_data.copy()
        
        # Map configuration sections to dataclass fields
        section_mappings = {
            "app": AppSettings,
            "sharepoint": SharePointSettings,
            "logging": LoggingSettings,
            "cors": CorsSettings,
            "rate_limiting": RateLimitingSettings,
            "security": SecuritySettings,
            "features": FeatureSettings,
        }
        
        for section_name, settings_class in section_mappings.items():
            section_data = config_data.get(section_name, {})
            
            # Create settings object with defaults
            settings_obj = settings_class()
            
            # Update with configuration data
            for key, value in section_data.items():
                if hasattr(settings_obj, key):
                    setattr(settings_obj, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {section_name}.{key}")
            
            # Set the section on the config object
            setattr(config, section_name, settings_obj)
        
        return config
    
    def _validate_config(self, config: EnvironmentConfig) -> None:
        """Validate the loaded configuration."""
        errors = []
        
        # Validate required fields
        if not config.sharepoint.endpoint:
            errors.append("SharePoint endpoint is required")
        
        if config.app.port < 1 or config.app.port > 65535:
            errors.append(f"Invalid port number: {config.app.port}")
        
        if config.sharepoint.timeout < 1:
            errors.append(f"Invalid SharePoint timeout: {config.sharepoint.timeout}")
        
        # Validate environment-specific requirements
        if config.app.environment == "production":
            if config.app.debug_mode:
                errors.append("Debug mode should be disabled in production")
            
            if not config.security.enforce_https:
                logger.warning("HTTPS enforcement is recommended in production")
            
            if config.security.include_docs:
                errors.append("API documentation should be disabled in production")
        
        if errors:
            error_msg = "Configuration validation failed: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get_config_summary(self, config: EnvironmentConfig) -> Dict[str, Any]:
        """Get a summary of the configuration for logging/debugging."""
        return {
            "environment": config.app.environment,
            "debug_mode": config.app.debug_mode,
            "port": config.app.port,
            "sharepoint_endpoint": config.sharepoint.endpoint,
            "mock_mode": config.sharepoint.mock_mode,
            "log_level": config.logging.level,
            "features_enabled": {
                "health_monitoring": config.features.health_monitoring,
                "request_logging": config.features.request_logging,
                "error_tracking": config.features.error_tracking,
                "metrics_collection": config.features.metrics_collection,
            }
        }
