# Changelog

## Recent Updates

### Selenium Removal
- Removed all Selenium code and dependencies
- Simplified authentication to use direct HTTP requests only
- Removed selenium from requirements.txt
- Cleaned up browser automation packages from Dockerfile

### Dependencies Cleanup
Removed unused dependencies from requirements.txt:
- selenium
- requests-html
- setuptools
- brotli (already commented out)
- python-magic
- Pillow
- PyYAML
- gunicorn (using uvicorn instead)
- python-dotenv (not used)
- black & flake8 (moved to Dockerfile only)

Reduced requirements.txt from 31 lines to 12 lines.

### Health API Simplification
- Unified all health checks to use single `/health` endpoint
- Updated Dockerfile healthcheck paths
- Removed separate `/health/live` and `/health/ready` endpoints
- Health endpoint now provides comprehensive status including:
  - Overall service status
  - SharePoint connectivity
  - Configuration validation
  - Response time metrics

### Deployment Configuration Cleanup
- Removed unused deployment YAML files:
  - `deployment/production.yaml`
  - `deployment/staging.yaml`
  - `deployment/terraform/main.tf`
- Deployment now uses GitHub Actions workflow only
- Simplified infrastructure management

## Dependencies (Current)

```
fastapi==0.116.1
pydantic==2.11.9
uvicorn[standard]==0.35.0
requests==2.32.5
pytest==8.4.2
pytest-asyncio==0.21.1
httpx==0.28.1
```

## Health Endpoint

Single comprehensive health endpoint at `/health`:
- Overall status (healthy/degraded/unhealthy)
- SharePoint connectivity check
- Configuration validation
- Service information (version, environment)
- Response time metrics

## Deployment

- Deployment is managed via GitHub Actions
- No manual deployment files required
- Simplified CI/CD pipeline

