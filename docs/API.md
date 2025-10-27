# Netanya Incident Service API Documentation

## Overview

The Netanya Incident Service provides a REST API for submitting municipal incidents to the Netanya SharePoint system. This service handles incident submissions, file uploads, and provides comprehensive health monitoring.

## Base URL

- **Development**: `http://localhost:8000` (when running locally or with Docker)
- **Production**: `https://netanya-incident-service-[hash].run.app`
- **Staging**: `https://netanya-incident-service-staging-[hash].run.app`

## Authentication

The service currently accepts public requests. Future versions may implement API key authentication.

## Endpoints

### Submit Incident

Submit a new incident to the Netanya municipal system.

**Endpoint**: `POST /incidents/submit`

**Request Body**:
```json
{
  "user_data": {
    "first_name": "יוסי",
    "last_name": "כהן", 
    "phone": "0501234567",
    "email": "yossi@example.com"
  },
  "category": {
    "id": 1,
    "name": "תאורה",
    "text": "Street lighting issues",
    "image_url": "https://example.com/lighting.jpg",
    "event_call_desc": "פנס רחוב לא עובד"
  },
  "street": {
    "id": 123,
    "name": "הרצל",
    "image_url": "https://example.com/street.jpg",
    "house_number": "15"
  },
  "custom_text": "פנס רחוב לא עובד ברחוב הרצל 15",
  "extra_files": {
    "filename": "evidence.jpg",
    "content_type": "image/jpeg",
    "size": 1024,
    "data": "base64_encoded_image_data"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "ticket_id": "NETANYA-2025-123456",
  "correlation_id": "abc123-def456-ghi789",
  "has_file": true,
  "file_info": {
    "filename": "evidence.jpg",
    "size": 1024,
    "type": "image/jpeg"
  },
  "metadata": {
    "processing_time": 1.5
  }
}
```

### Health Check

Check service health status.

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-01-02T10:30:00Z",
  "service": "Netanya Incident Service"
}
```

### Detailed Health Check

Get comprehensive health information including dependencies.

**Endpoint**: `GET /health/detailed`

**Response** (200 OK):
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-01-02T10:30:00Z",
  "response_time_ms": 45.2,
  "service_info": {
    "name": "Netanya Incident Service",
    "version": "1.0.0",
    "environment": "production",
    "debug_mode": false
  },
  "dependencies": {
    "sharepoint": {
      "name": "sharepoint",
      "status": "healthy",
      "message": "SharePoint connectivity verified",
      "response_time_ms": 120.5
    },
    "configuration": {
      "name": "configuration", 
      "status": "healthy",
      "message": "Configuration is valid and complete",
      "response_time_ms": 5.1
    }
  }
}
```

### Readiness Probe

Check if service is ready to accept requests (for Kubernetes/Cloud Run).

**Endpoint**: `GET /health/ready`

### Liveness Probe 

Check if service is alive (for Kubernetes/Cloud Run).

**Endpoint**: `GET /health/live`

### Service Information

Get basic service information.

**Endpoint**: `GET /`

**Response** (200 OK):
```json
{
  "service": "Netanya Incident Service",
  "version": "1.0.0",
  "environment": "production",
  "debug_mode": false,
  "status": "operational"
}
```

## Error Responses

### Validation Error (422)

```json
{
  "error": true,
  "message": "Validation failed",
  "correlation_id": "error-123",
  "errors": [
    {
      "field": "user_data.phone",
      "message": "Invalid phone format",
      "invalid_value": "123"
    }
  ]
}
```

### Internal Server Error (500)

```json
{
  "error": true,
  "message": "Internal server error",
  "correlation_id": "error-456",
  "details": "Service temporarily unavailable"
}
```

## File Upload Requirements

### Supported Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

### File Size Limits
- Maximum file size: 10MB (configurable via `MAX_FILE_SIZE_MB`)
- Minimum file size: 1KB

### Security Requirements
- Files must have valid image signatures
- No executable content allowed
- Malicious content detection enabled

## Rate Limiting

- **Standard users**: 100 requests per minute
- **File uploads**: 10 requests per minute

## CORS Policy

The service supports CORS for web applications with the following configuration:
- **Allowed Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Allowed Methods**: GET, POST, OPTIONS
- **Allowed Headers**: Content-Type, Authorization, X-Requested-With
- **Default**: Open CORS in development, restricted in production

## Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 400  | Bad Request |
| 413  | Payload Too Large |
| 422  | Unprocessable Entity (Validation Error) |
| 429  | Too Many Requests |
| 500  | Internal Server Error |
| 503  | Service Unavailable |

## Integration Examples

### JavaScript/Fetch

```javascript
const submitIncident = async (incidentData) => {
  try {
    const response = await fetch('/incidents/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(incidentData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Incident submitted:', result.ticket_id);
      return result;
    } else {
      console.error('Submission failed:', result);
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
};
```

### Python/Requests

```python
import requests
import base64

def submit_incident(incident_data, image_file=None):
    url = "https://your-service-url.run.app/incidents/submit"
    
    if image_file:
        with open(image_file, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            incident_data['extra_files'] = {
                'filename': image_file.name,
                'content_type': 'image/jpeg',
                'size': len(image_data),
                'data': image_data
            }
    
    response = requests.post(url, json=incident_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Incident submitted: {result['ticket_id']}")
        return result
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise requests.HTTPError(response=response)
```

## Environment-Specific Behavior

### Debug Mode (Development/Staging)
- API documentation available at `/docs` and `/redoc`
- Detailed error messages in responses
- Mock SharePoint integration (no external calls)
- Enhanced logging enabled
- Uses mock-sharepoint service for testing

### Production Mode
- API documentation disabled for security
- Sanitized error messages
- Real SharePoint integration
- Optimized logging level (INFO)
- Direct integration with Netanya municipality system

## Monitoring and Observability

### Health Check Endpoint
Monitor service health using the health check endpoint:
- `/health` - Comprehensive health status with:
  - Overall service status (healthy/degraded/unhealthy)
  - SharePoint connectivity status
  - Configuration validation status
  - Service version and environment information
  - Response time metrics
  - Dependencies health checks

### Correlation IDs
Every request receives a unique correlation ID for tracing and debugging. Include this ID when reporting issues.

### Metrics
The service exposes metrics for:
- Request rate and response times
- Error rates by type
- File upload sizes and processing times
- SharePoint API response times

## Support

For technical support or API questions:
- **Documentation**: This document
- **Health Status**: Check `/health` endpoint
- **Error Correlation**: Include correlation ID in support requests
