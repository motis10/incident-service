#!/usr/bin/env python3
"""
Start the service in production mode but with mock SharePoint for testing.
This allows testing production configuration without hitting real SharePoint.
"""
import os
import sys
import subprocess
import time

def start_production_with_mock():
    """Start service in production mode with mock SharePoint."""
    print("🚀 STARTING PRODUCTION MODE WITH MOCK SHAREPOINT")
    print("=" * 55)
    
    # Set environment variables for production mode with mock
    env = os.environ.copy()
    env.update({
        'ENVIRONMENT': 'production',
        'DEBUG_MODE': 'false',
        'LOG_LEVEL': 'INFO',
        'PYTHONPATH': 'src',
        # Force use of mock even in production for testing
        'USE_MOCK_SHAREPOINT': 'true'
    })
    
    print("📋 Environment Configuration:")
    print(f"   • ENVIRONMENT: {env['ENVIRONMENT']}")
    print(f"   • DEBUG_MODE: {env['DEBUG_MODE']}")
    print(f"   • LOG_LEVEL: {env['LOG_LEVEL']}")
    print(f"   • USE_MOCK_SHAREPOINT: {env['USE_MOCK_SHAREPOINT']}")
    
    # Create the startup script
    startup_script = '''
import os
os.environ['USE_MOCK_SHAREPOINT'] = 'true'
from app.main import app
import uvicorn

# Override SharePoint client selection for testing
def mock_create_sharepoint_client():
    """Force mock SharePoint even in production for testing."""
    from app.services.mock_service import MockSharePointService
    print("🔧 PRODUCTION-TESTING: Using MockSharePointService")
    return MockSharePointService()

# Patch the client creation
import app.api.incidents
app.api.incidents.create_sharepoint_client = mock_create_sharepoint_client

# Reinitialize incident service with mock
sharepoint_client = mock_create_sharepoint_client()
from app.services.incident_service import IncidentService
app.api.incidents.incident_service = IncidentService(sharepoint_client=sharepoint_client)

print("✅ Production mode with mock SharePoint initialized")
uvicorn.run(app, host='0.0.0.0', port=8000)
'''
    
    try:
        print("\n🌟 Starting server...")
        print("   Access the service at: http://localhost:8000")
        print("   Press Ctrl+C to stop")
        print("-" * 55)
        
        # Run the server
        result = subprocess.run([
            sys.executable, '-c', startup_script
        ], env=env, cwd='/Users/motistein/netanya-web/netanya-incident-service')
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = start_production_with_mock()
    sys.exit(0 if success else 1)
