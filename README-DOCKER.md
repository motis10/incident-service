# 🐳 Docker Development Guide - Netanya Incident Service

This guide covers the Docker-based development environment for the Netanya Incident Service.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)

### Start Development Environment

```bash
# Quick setup (recommended for first time)
make setup

# Or manually:
cp env.example .env
make dev
```

## 🏗️ Architecture

The development environment consists of:

- **Main Service** (`incident-service`): FastAPI application on port 8000
- **Mock SharePoint** (`mock-sharepoint`): Flask-based SharePoint API simulator on port 8080  
- **Nginx** (`nginx`): Reverse proxy and load balancer on port 80
- **Redis** (`redis`): Caching layer on port 6379 (optional)

## 🌐 Service Endpoints

| Service | Development URL | Description |
|---------|----------------|-------------|
| Main API | http://localhost:8000 | Direct access to FastAPI service |
| API via Nginx | http://localhost | Load-balanced access |
| API Documentation | http://localhost:8000/docs | Swagger UI (debug mode only) |
| Health Checks | http://localhost:8000/health | Service health monitoring |
| Mock SharePoint | http://localhost:8080 | Development SharePoint simulator |
| Mock Admin | http://localhost/mock-admin | Mock service administration |

## 📋 Available Commands

### Development
```bash
make dev           # Start development environment
make up            # Start all services
make down          # Stop all services
make restart       # Restart all services
make logs          # View all logs
make logs-app      # View main service logs only
```

### Testing
```bash
make test          # Run all tests
make test-watch    # Run tests in watch mode
make test-coverage # Run tests with coverage report
make lint          # Code linting
make format        # Code formatting
```

### Production
```bash
make prod          # Start production environment
make prod-down     # Stop production environment
```

### Utilities
```bash
make health        # Check service health
make status        # Show container status
make shell         # Open shell in main container
make clean         # Clean up containers and volumes
```

## 🔧 Configuration

### Environment Variables

The service uses environment variables for configuration. Copy `env.example` to `.env` and modify as needed:

```bash
cp env.example .env
```

Key configuration options:

```env
# Application
DEBUG_MODE=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
PORT=8000

# SharePoint Integration
SHAREPOINT_ENDPOINT=http://mock-sharepoint:8080/api/incidents
```

### Docker Compose Profiles

- **Development** (`docker-compose.yml`): Full development stack with hot reload
- **Production** (`docker-compose.prod.yml`): Production-ready configuration

## 🧪 Mock SharePoint Service

The development environment includes a complete mock SharePoint service that simulates the NetanyaMuni API.

### Features
- Realistic API response format
- File upload handling
- Request logging and debugging
- Admin interface for inspection

### Mock Admin Interface
- **Incidents**: http://localhost/mock-admin/incidents
- **Requests**: http://localhost/mock-admin/requests  
- **Reset Data**: http://localhost/mock-admin/reset

### Example Mock Usage

```bash
# Submit test incident
curl -X POST http://localhost:8080/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "eventCallDesc": "Test incident",
    "callerFirstName": "John",
    "callerLastName": "Doe"
  }'

# View submitted incidents
curl http://localhost/mock-admin/incidents
```

## 🏥 Health Monitoring

The service includes comprehensive health monitoring:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with dependencies
curl http://localhost:8000/health/detailed

# Readiness probe (for load balancers)
curl http://localhost:8000/health/ready

# Liveness probe (for container orchestrators)
curl http://localhost:8000/health/live
```

## 🔒 Security Features

### Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| API Documentation | ✅ Available | ❌ Disabled |
| Debug Logs | ✅ Verbose | ❌ Minimal |
| HTTPS | ❌ Optional | ✅ Required |
| Rate Limiting | 🟡 Relaxed | ✅ Strict |
| CORS | ✅ Permissive | ✅ Restricted |

### Production Security
- HTTPS-only access
- Strict rate limiting
- Security headers (HSTS, CSP, etc.)
- Documentation endpoints disabled
- Minimal error exposure

## 🐛 Development Workflow

### 1. Code Changes
Files are mounted as volumes, so changes are reflected immediately:
- `./src:/app/src:ro` - Application source code
- `./tests:/app/tests:ro` - Test files

### 2. Testing
```bash
# Run all tests
make test

# Run specific test file
docker-compose exec incident-service python -m pytest tests/test_api_endpoints.py -v

# Watch mode for continuous testing
make test-watch
```

### 3. Debugging
```bash
# View application logs
make logs-app

# Access container shell
make shell

# Check service health
make health
```

### 4. Mock Service Debugging
```bash
# View mock service logs
make logs-mock

# Check submitted incidents
curl http://localhost/mock-admin/incidents

# Reset mock data
curl -X POST http://localhost/mock-admin/reset
```

## 📊 Performance Testing

Test the service under load:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Basic load test
ab -n 1000 -c 10 http://localhost:8000/health

# API endpoint test
ab -n 100 -c 5 -p test-payload.json -T application/json http://localhost:8000/incidents/submit
```

## 🚀 Production Deployment

### Build Production Images
```bash
make build
```

### Deploy to Production
```bash
# Start production environment
make prod

# Or with custom configuration
docker-compose -f docker-compose.prod.yml up -d
```

### Push to Registry
```bash
# Tag and push images
make push
```

## 🆘 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check container status
make status

# View logs for errors
make logs

# Clean and rebuild
make clean
make build
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8080

# Modify ports in docker-compose.yml if needed
```

**Mock service not responding:**
```bash
# Check mock service health
curl http://localhost:8080/health

# View mock service logs
make logs-mock

# Reset mock service
docker-compose restart mock-sharepoint
```

**Tests failing:**
```bash
# Run tests with verbose output
make test

# Check test environment
docker-compose exec incident-service python -c "import sys; print(sys.path)"

# Run specific failing test
docker-compose exec incident-service python -m pytest tests/test_specific.py::test_function -v
```

### Debug Mode

Enable additional debugging in `.env`:
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

Then restart services:
```bash
make restart
```

## 📝 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [pytest Testing Guide](https://docs.pytest.org/)

For more information, see the main project README.md.
