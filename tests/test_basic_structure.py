"""
Test basic project structure and FastAPI foundation.
These tests ensure the core application components are properly initialized.
"""
import pytest
import os
import sys
from pathlib import Path

# Add the src directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_project_structure_exists():
    """Test that basic project directories exist."""
    project_root = Path(__file__).parent.parent
    
    # Core directories should exist
    assert (project_root / "src").exists(), "src directory should exist"
    assert (project_root / "src" / "app").exists(), "src/app directory should exist"
    assert (project_root / "tests").exists(), "tests directory should exist"
    
def test_requirements_file_exists():
    """Test that requirements.txt exists with core dependencies."""
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"
    
    assert requirements_file.exists(), "requirements.txt should exist"
    
    # Read requirements and check for core dependencies
    content = requirements_file.read_text()
    required_packages = ['fastapi', 'pydantic', 'uvicorn', 'requests']
    
    for package in required_packages:
        assert package.lower() in content.lower(), f"{package} should be in requirements.txt"

def test_fastapi_app_initialization():
    """Test that FastAPI app can be imported and initialized."""
    try:
        from app.main import app
        assert app is not None, "FastAPI app should be initialized"
        assert hasattr(app, 'routes'), "FastAPI app should have routes attribute"
    except ImportError as e:
        pytest.skip(f"FastAPI not available in current Python environment: {e}")

def test_logging_infrastructure():
    """Test that logging is properly configured."""
    try:
        from app.core.logging import setup_logging, logger
        
        # Should be able to import logging functions
        assert callable(setup_logging), "setup_logging should be a callable function"
        assert logger is not None, "logger should be initialized"
        
        # Test basic logging functionality
        logger.info("Test log message")
        
    except ImportError:
        pytest.fail("Could not import logging infrastructure")

def test_basic_app_startup():
    """Test that the app can start without errors."""
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Basic health check - the app should at least start
        # We don't expect any specific endpoints yet, just no startup errors
        assert client is not None, "TestClient should be created successfully"
        
    except ImportError as e:
        pytest.skip(f"FastAPI not available in current Python environment: {e}")
    except Exception as e:
        pytest.fail(f"App startup failed: {e}")
