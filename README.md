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
   # Start with development environment
   docker-compose --env-file env.development up --build
   ```

3. **Access the services**
   - Main API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs (development mode only)
   - Mock SharePoint: http://localhost:8080

### Local Development (Alternative)

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export PYTHONPATH=$(pwd)/src:$PYTHONPATH
   export DEBUG_MODE=true
   export ENVIRONMENT=development
   export LOG_LEVEL=DEBUG
   ```

3. **Run the service**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Environment name | `development` | No |
| `BUILD_TARGET` | Docker build target | `development` | Docker only |
| `DEBUG_MODE` | Enable mock responses | `true` | No |
| `LOG_LEVEL` | Logging level | `DEBUG` | No |
| `PORT` | Service port | `8000` | No |
| `SHAREPOINT_ENDPOINT` | SharePoint endpoint URL | Mock endpoint | Yes |
| `CONTAINER_SUFFIX` | Docker container name suffix | - | Docker only |
| `MAX_FILE_SIZE_MB` | Maximum file upload size | `10` | No |

### Environment Configuration

The service supports multiple environments through `.env` files:

- **Development**: Use `env.development` for local development with mock services
- **Production**: Use `prod.env` for production deployment with real SharePoint
- **Custom**: Copy `env.example` to `.env` and customize

**Development setup:**
```bash
# Use pre-configured development environment
docker-compose --env-file env.development up --build

# Or create custom environment
cp env.example .env
# Edit .env as needed
docker-compose up --build
```

**Production setup:**
```bash
docker-compose --env-file prod.env up --build
```

## API Endpoints

- `POST /incidents/submit` - Submit incident with optional file attachment
- `GET /health` - Health check endpoint
- `GET /docs` - API documentation (debug mode only)

## Testing

### Docker Environment
```bash
# Start development environment first
docker-compose --env-file env.development up -d

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

The service uses a single multi-stage Dockerfile with environment-specific configuration:

```bash
# Build production image
docker-compose --env-file prod.env up --build

# Or build manually
docker build --target production -t netanya-incident-service:prod .

# Run production container with environment file
docker run -p 8000:8000 --env-file prod.env netanya-incident-service:prod
```

### Google Cloud Run

1. **Build and push Docker image**
2. **Deploy to Cloud Run with environment variables**
3. **Configure health checks and scaling**

See `docs/DEPLOYMENT.md` for detailed deployment instructions.

## Development Status

**✅ Completed Features:**
- [x] Project foundation and FastAPI setup
- [x] Environment-based configuration management
- [x] Data models and validation
- [x] SharePoint integration with mock service
- [x] File upload support with validation
- [x] Docker containerization
- [x] Comprehensive testing suite
- [x] Health monitoring endpoints
- [x] Production-ready deployment configuration

**🔄 Current State:**
The service is production-ready with a simplified, clean architecture. All redundant files and dependencies have been removed, creating a focused microservice for incident submission.

## License

MIT License - see LICENSE file for details.
# Force deployment
