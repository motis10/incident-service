# Netanya Incident Service

A standalone FastAPI microservice for submitting municipal incidents to the Netanya municipality SharePoint system.

## Overview

This service extracts the municipality API integration functionality from the client application, providing a clean REST API interface for incident submission. It maintains 100% compatibility with the existing NetanyaMuni SharePoint endpoint while offering modern API development patterns.

## Features

- **FastAPI REST Interface**: Modern async API with automatic OpenAPI documentation
- **SharePoint Integration**: Direct integration with NetanyaMuni incidents.ashx endpoint
- **Docker-First Development**: Full containerization with Docker Compose for local development
- **Cloud Run Ready**: Optimized for Google Cloud Run deployment
- **Debug/Production Modes**: Safe development with mock responses and production SharePoint integration
- **File Upload Support**: Single image attachment capability with validation
- **Comprehensive Testing**: Unit, integration, and E2E test coverage

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd netanya-incident-service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export DEBUG_MODE=true
   export ENVIRONMENT=development
   export LOG_LEVEL=INFO
   ```

4. **Run the service**
   ```bash
   uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**
   - Service: http://localhost:8000
   - Documentation: http://localhost:8000/docs (debug mode only)

### Docker Development

```bash
docker-compose up --build
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG_MODE` | Enable mock responses | `true` | No |
| `ENVIRONMENT` | Environment name | `development` | No |
| `NETANYA_ENDPOINT` | SharePoint endpoint URL | - | Production only |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `PORT` | Service port | `8000` | No |

## API Endpoints

- `POST /incidents/submit` - Submit incident with optional file attachment
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation (debug mode only)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run specific test file
pytest tests/test_basic_structure.py
```

## Deployment

### Google Cloud Run

1. **Build and push Docker image**
2. **Deploy to Cloud Run with environment variables**
3. **Configure health checks and scaling**

See deployment documentation for detailed instructions.

## Development Status

This is the initial implementation focusing on:
- [x] Project foundation and FastAPI setup
- [ ] Configuration management
- [ ] Data models and validation
- [ ] SharePoint integration
- [ ] File upload support
- [ ] Production deployment

## License

MIT License - see LICENSE file for details.
