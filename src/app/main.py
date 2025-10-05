"""
Main FastAPI application for the Netanya Incident Service.
Provides REST API for municipality incident submission to SharePoint.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import setup_logging, get_logger
from app.core.config import ConfigService, ConfigurationError
from app.api.incidents import router as incidents_router
from app.services.error_handling import ErrorHandlingService
from app.services.health_monitoring import HealthMonitoringService

# Initialize configuration
try:
    config_service = ConfigService()
    config_service.validate_environment()
    config = config_service.get_config()
except ConfigurationError as e:
    print(f"Configuration Error: {e}")
    exit(1)

# Initialize logging with configuration
setup_logging(
    log_level=config.log_level,
    enable_json=config.environment == "production"
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Netanya Incident Service...")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Debug Mode: {config.debug_mode}")
    logger.info(f"SharePoint Endpoint: {config_service.get_sharepoint_endpoint()}")
    logger.info(f"Port: {config.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Netanya Incident Service...")


# Initialize services
error_service = ErrorHandlingService()
health_service = HealthMonitoringService()

# Create FastAPI application
app = FastAPI(
    title="Netanya Incident Service",
    description="Municipality incident submission service for Netanya SharePoint integration",
    version="1.0.0",
    docs_url="/docs" if config.debug_mode else None,  # Conditional docs based on debug mode
    redoc_url="/redoc" if config.debug_mode else None,  # Conditional redoc based on debug mode
    openapi_url="/openapi.json" if config.debug_mode else None,  # Conditional OpenAPI JSON
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(incidents_router)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors globally."""
    correlation_id = error_service.correlation_generator.generate()
    logger.error(f"Request validation error [correlation_id: {correlation_id}]: {str(exc)}")
    
    # Convert Pydantic errors to structured format
    error_details = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_details.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = error_service.create_422_response(
        message="Request validation failed",
        field_errors=error_details,
        correlation_id=correlation_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle JSON parsing and other value errors."""
    correlation_id = error_service.correlation_generator.generate()
    logger.error(f"Value error [correlation_id: {correlation_id}]: {str(exc)}")
    
    error_response = error_service.create_400_response(
        message="Invalid request format or JSON syntax error",
        correlation_id=correlation_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    correlation_id = error_service.correlation_generator.generate()
    logger.error(f"Unexpected error [correlation_id: {correlation_id}]: {str(exc)}")
    
    error_response = error_service.create_500_response(
        message="Internal server error",
        error_details=str(exc) if config.debug_mode else "An unexpected error occurred",
        correlation_id=correlation_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


@app.get("/")
async def root():
    """Root endpoint for basic service information."""
    return {
        "service": "Netanya Incident Service",
        "version": "1.0.0",
        "status": "running",
        "debug_mode": config.debug_mode
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint for monitoring and Cloud Run probes."""
    comprehensive_health = health_service.get_comprehensive_health()
    
    # Determine if service is healthy for Cloud Run probes
    is_healthy = comprehensive_health.overall_status in ["healthy", "degraded"]
    
    return {
        "overall_status": comprehensive_health.overall_status,
        "healthy": is_healthy,
        "timestamp": comprehensive_health.timestamp,
        "service_info": comprehensive_health.service_info,
        "dependencies": comprehensive_health.dependencies,
        "response_time_ms": comprehensive_health.response_time_ms,
        "debug_mode": config.debug_mode
    }

# Custom endpoints for documentation security in production mode
if not config.debug_mode:
    @app.get("/docs", include_in_schema=False)
    async def docs_disabled():
        """Return 404 for docs in production mode."""
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_disabled():
        """Return 404 for redoc in production mode."""
        raise HTTPException(status_code=404, detail="Documentation not available in production mode")
    
    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_disabled():
        """Return 404 for OpenAPI JSON in production mode."""
        raise HTTPException(status_code=404, detail="API specification not available in production mode")
