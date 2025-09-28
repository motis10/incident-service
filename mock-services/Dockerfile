# Mock SharePoint Service for Development
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Create app user for security
RUN groupadd -r mockapp && useradd -r -g mockapp mockapp

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir flask flask-cors requests

# Copy mock service code
COPY mock_sharepoint.py .

# Change ownership to app user
RUN chown -R mockapp:mockapp /app

# Switch to app user
USER mockapp

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the mock service
CMD ["python", "mock_sharepoint.py"]
