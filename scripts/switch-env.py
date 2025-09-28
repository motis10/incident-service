#!/usr/bin/env python3
"""
Environment Switching Utility for Netanya Incident Service

This script helps switch between different environments and validates configuration.
"""
import os
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    parser = argparse.ArgumentParser(description="Switch between service environments")
    parser.add_argument("environment", choices=["development", "production", "testing"],
                      help="Environment to switch to")
    parser.add_argument("--validate", action="store_true",
                      help="Validate configuration after switching")
    parser.add_argument("--show-config", action="store_true",
                      help="Show configuration summary")
    parser.add_argument("--set-env", action="store_true",
                      help="Set environment variables")
    
    args = parser.parse_args()
    
    print(f"🔄 Switching to {args.environment} environment...")
    
    try:
        # Try to load configuration loader (may not work without PyYAML)
        try:
            from app.core.config_loader import ConfigurationLoader
            
            loader = ConfigurationLoader()
            config = loader.load_environment_config(args.environment)
            
            print(f"✅ Configuration loaded successfully for {args.environment}")
            
            if args.show_config:
                print("\n📊 Configuration Summary:")
                summary = loader.get_config_summary(config)
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            
            if args.set_env:
                print(f"\n🔧 Setting environment variables for {args.environment}:")
                env_vars = {
                    "ENVIRONMENT": config.app.environment,
                    "DEBUG_MODE": str(config.app.debug_mode).lower(),
                    "LOG_LEVEL": config.logging.level,
                    "PORT": str(config.app.port),
                    "SHAREPOINT_ENDPOINT": config.sharepoint.endpoint
                }
                
                for var, value in env_vars.items():
                    os.environ[var] = value
                    print(f"  export {var}='{value}'")
                
                print(f"\n💡 To apply these variables in your shell, run:")
                print(f"  eval $(python scripts/switch-env.py {args.environment} --set-env | grep 'export')")
            
        except ImportError:
            # Fallback to basic environment switching
            print("⚠️  PyYAML not available, using basic environment switching")
            
            env_configs = {
                "development": {
                    "DEBUG_MODE": "true",
                    "LOG_LEVEL": "DEBUG",
                    "ENVIRONMENT": "development",
                    "SHAREPOINT_ENDPOINT": "http://mock-sharepoint:8080/api/incidents"
                },
                "production": {
                    "DEBUG_MODE": "false", 
                    "LOG_LEVEL": "INFO",
                    "ENVIRONMENT": "production",
                    "SHAREPOINT_ENDPOINT": "${SHAREPOINT_ENDPOINT}"
                },
                "testing": {
                    "DEBUG_MODE": "true",
                    "LOG_LEVEL": "DEBUG", 
                    "ENVIRONMENT": "testing",
                    "SHAREPOINT_ENDPOINT": "http://localhost:8080/api/incidents"
                }
            }
            
            config = env_configs.get(args.environment, {})
            
            if args.set_env:
                print(f"\n🔧 Environment variables for {args.environment}:")
                for var, value in config.items():
                    print(f"  export {var}='{value}'")
            
            if args.show_config:
                print(f"\n📊 Basic configuration for {args.environment}:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
        
        print(f"\n✅ Environment switched to {args.environment}")
        
        # Provide usage instructions
        print(f"\n📋 Next steps:")
        print(f"  1. Apply environment variables (see above)")
        print(f"  2. Restart your application")
        print(f"  3. Verify configuration with: make health")
        
        if args.environment == "development":
            print(f"\n🚀 Development mode enabled:")
            print(f"  - API Documentation: http://localhost:8000/docs")
            print(f"  - Mock SharePoint: http://localhost:8080")
            print(f"  - Health Check: http://localhost:8000/health")
        
        elif args.environment == "production":
            print(f"\n🔒 Production mode enabled:")
            print(f"  - API Documentation: DISABLED")
            print(f"  - HTTPS enforcement: ENABLED")
            print(f"  - Debug logging: DISABLED")
        
    except Exception as e:
        print(f"❌ Error switching environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
