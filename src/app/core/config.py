"""
Configuration service for environment-based configuration management.
Provides environment variable validation and application configuration.
"""
import os
from typing import Optional
from dataclasses import dataclass


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


@dataclass
class AppConfig:
    """Application configuration data class."""
    debug_mode: bool
    environment: str
    port: int
    log_level: str
    netanya_endpoint: str


class ConfigService:
    """Service for managing environment-based configuration."""
    
    def __init__(self):
        """Initialize configuration service."""
        self._config: Optional[AppConfig] = None
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from environment variables."""
        # Parse environment variables with defaults
        debug_mode = self._parse_boolean(os.getenv('DEBUG_MODE', 'true'))
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # Parse port with validation
        try:
            port = self._parse_int(os.getenv('PORT', '8000'))
        except ConfigurationError:
            raise  # Re-raise for immediate failure
        
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        netanya_endpoint = os.getenv('NETANYA_ENDPOINT', self._get_default_netanya_endpoint())
        
        self._config = AppConfig(
            debug_mode=debug_mode,
            environment=environment,
            port=port,
            log_level=log_level,
            netanya_endpoint=netanya_endpoint
        )
    
    def _parse_boolean(self, value: str) -> bool:
        """Parse string to boolean."""
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _parse_int(self, value: str) -> int:
        """Parse string to integer."""
        try:
            return int(value)
        except ValueError:
            raise ConfigurationError(f"Invalid integer value: {value}")
    
    def _get_default_netanya_endpoint(self) -> str:
        """Get default Netanya SharePoint endpoint."""
        return "https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident"
    
    def get_config(self) -> AppConfig:
        """Get application configuration."""
        if self._config is None:
            self._load_configuration()
        return self._config
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get_config().debug_mode
    
    def get_sharepoint_endpoint(self) -> str:
        """Get SharePoint endpoint URL."""
        return self.get_config().netanya_endpoint
    
    def validate_environment(self) -> None:
        """Validate environment configuration and fail fast if invalid."""
        config = self.get_config()
        
        # Validate environment values
        valid_environments = ['development', 'staging', 'production']
        if config.environment not in valid_environments:
            raise ConfigurationError(
                f"Invalid ENVIRONMENT '{config.environment}'. "
                f"Must be one of: {', '.join(valid_environments)}"
            )
        
        # Validate port range
        if not (1 <= config.port <= 65535):
            raise ConfigurationError(
                f"Invalid PORT '{config.port}'. Must be between 1 and 65535."
            )
        
        # Validate HTTPS in production
        if config.environment == 'production' and not config.debug_mode:
            if not config.netanya_endpoint.startswith('https://'):
                raise ConfigurationError(
                    "Production mode requires HTTPS endpoints. "
                    f"NETANYA_ENDPOINT must start with 'https://': {config.netanya_endpoint}"
                )
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level.upper() not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid LOG_LEVEL '{config.log_level}'. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
