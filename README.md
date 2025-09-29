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

### Docker Development (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd netanya-incident-service
   ```

2. **Start development environment**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Start all services
   docker-compose up --build
   ```

3. **Access the services**
   - Main API: http://localhost:8000
   - API via Nginx: http://localhost
   - API Documentation: http://localhost:8000/docs (development mode only)
   - Mock SharePoint: http://localhost:8080
   - Mock Admin: http://localhost/mock-admin

### Local Development (Alternative)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export DEBUG_MODE=true
   export ENVIRONMENT=development
   export LOG_LEVEL=INFO
   ```

3. **Run the service**
   ```bash
   uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG_MODE` | Enable mock responses | `true` | No |
| `ENVIRONMENT` | Environment name | `development` | No |
| `SHAREPOINT_ENDPOINT` | SharePoint endpoint URL | - | Production only |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `PORT` | Service port | `8000` | No |

### Development Environment

The development environment includes:
- **Main Service**: FastAPI application with hot reload
- **Mock SharePoint**: Simulates the NetanyaMuni API

Copy `env.example` to `.env` and modify as needed:
```bash
cp env.example .env
```

## API Endpoints

- `POST /incidents/submit` - Submit incident with optional file attachment
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation (debug mode only)

## Testing

### Docker Environment
```bash
# Run all tests in Docker
docker-compose exec incident-service python -m pytest

# Run with coverage
docker-compose exec incident-service python -m pytest --cov=src/app --cov-report=html

# Run specific test file
docker-compose exec incident-service python -m pytest tests/test_basic_structure.py -v
```

### Local Environment
```bash
# Run all tests locally
pytest

# Run with coverage
pytest --cov=src/app --cov-report=html

# Run specific test file
pytest tests/test_basic_structure.py
```

## Deployment

### Docker Production

The service uses a single multi-stage Dockerfile optimized for both development and production:

```bash
# Build production image
docker build --target production -t netanya-incident-service:prod .

# Run production container
docker run -p 8000:8000 \
  -e DEBUG_MODE=false \
  -e ENVIRONMENT=production \
  -e SHAREPOINT_ENDPOINT=https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident \
  netanya-incident-service:prod
```

### Google Cloud Run

1. **Build and push Docker image**
2. **Deploy to Cloud Run with environment variables**
3. **Configure health checks and scaling**

See `docs/DEPLOYMENT.md` for detailed deployment instructions.

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
