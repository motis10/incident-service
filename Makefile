# Netanya Incident Service - Development Makefile

.PHONY: help build up down restart logs test lint clean dev prod

# Default target
help:
	@echo "Netanya Incident Service - Available Commands:"
	@echo ""
	@echo "Development Commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make up           - Start all services with Docker Compose"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - Show logs from all services"
	@echo "  make logs-app     - Show logs from main app only"
	@echo "  make logs-mock    - Show logs from mock SharePoint only"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run all tests"
	@echo "  make test-watch   - Run tests in watch mode"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code with black"
	@echo "  make coverage     - Run tests with coverage report"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod         - Start production environment"
	@echo "  make build        - Build all Docker images"
	@echo "  make push         - Push images to registry"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make shell        - Open shell in main container"
	@echo "  make mock-admin   - Open mock SharePoint admin interface"
	@echo "  make health       - Check service health"

# Development environment
dev: build up
	@echo "🚀 Development environment started!"
	@echo "🌐 Main API: http://localhost:8000"
	@echo "📖 API Docs: http://localhost:8000/docs"
	@echo "🏥 Health Check: http://localhost:8000/health"
	@echo "🎭 Mock SharePoint: http://localhost:8080"
	@echo "📊 Mock Admin: http://localhost/mock-admin"

# Docker Compose commands
up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f incident-service

logs-mock:
	docker-compose logs -f mock-sharepoint

# Build images
build:
	docker-compose build

# Testing commands
test:
	docker-compose exec incident-service python -m pytest tests/ -v

test-watch:
	docker-compose exec incident-service python -m pytest tests/ -v --tb=short -f

test-coverage:
	docker-compose exec incident-service python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Code quality
lint:
	docker-compose exec incident-service flake8 src/app
	docker-compose exec incident-service black --check src/app

format:
	docker-compose exec incident-service black src/app

# Production environment
prod:
	docker-compose -f docker-compose.prod.yml up -d
	@echo "🚀 Production environment started!"
	@echo "🌐 API: https://localhost"
	@echo "🏥 Health: https://localhost/health"

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Utility commands
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

shell:
	docker-compose exec incident-service /bin/bash

shell-mock:
	docker-compose exec mock-sharepoint /bin/bash

mock-admin:
	@echo "🎭 Mock SharePoint Admin Interface:"
	@echo "📊 Incidents: http://localhost/mock-admin/incidents"
	@echo "📝 Requests: http://localhost/mock-admin/requests"
	@echo "🔄 Reset: http://localhost/mock-admin/reset"

health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/health | jq .
	@echo ""
	@curl -s http://localhost:8080/health | jq .

# Status checks
status:
	docker-compose ps

# Push to registry (for production)
push:
	docker tag netanya-incident-service_incident-service:latest registry.example.com/netanya-incident-service:latest
	docker push registry.example.com/netanya-incident-service:latest

# Development quick start
quick-start: clean build dev
	@echo "🎉 Quick start complete!"

# Full development setup
setup:
	@echo "🔧 Setting up development environment..."
	cp env.example .env
	docker-compose build
	docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 10
	make health
	@echo "✅ Setup complete!"
