"""
Main FastAPI application for the Netanya Incident Service.
Provides REST API for municipality incident submission to SharePoint.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import setup_logging, get_logger

# Initialize logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_json=os.getenv("ENVIRONMENT", "development") == "production"
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Netanya Incident Service...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Debug Mode: {os.getenv('DEBUG_MODE', 'true')}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Netanya Incident Service...")


# Create FastAPI application
app = FastAPI(
    title="Netanya Incident Service",
    description="Municipality incident submission service for Netanya SharePoint integration",
    version="0.1.0",
    docs_url=None,  # Will be conditionally enabled based on debug mode
    redoc_url=None,  # Will be conditionally enabled based on debug mode
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint for basic service information."""
    return {
        "service": "Netanya Incident Service",
        "version": "0.1.0",
        "status": "running"
    }
