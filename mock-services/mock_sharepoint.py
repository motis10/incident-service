#!/usr/bin/env python3
"""
Mock SharePoint Service for Development Testing
Simulates NetanyaMuni SharePoint API behavior for local development.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mock_sharepoint')

app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.getenv('PORT', 8080))
MOCK_MODE = os.getenv('MOCK_MODE', 'development')

# Mock data storage
incident_storage = {}
request_log = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "Mock SharePoint Service",
        "version": "1.0.0",
        "mode": MOCK_MODE,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/incidents', methods=['POST', 'OPTIONS'])
def submit_incident():
    """
    Mock SharePoint incident submission endpoint.
    Mimics the NetanyaMuni SharePoint API behavior.
    """
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response
    
    try:
        # Log incoming request
        logger.info(f"Received incident submission: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        # Parse multipart form data
        if 'multipart/form-data' in request.content_type:
            # Extract JSON payload
            json_data = None
            file_data = None
            
            if 'json' in request.form:
                json_data = json.loads(request.form['json'])
                logger.info(f"Parsed JSON payload: {json_data}")
            
            # Check for file attachment
            if 'attachment' in request.files:
                file_data = request.files['attachment']
                logger.info(f"Received file attachment: {file_data.filename} ({len(file_data.read())} bytes)")
                file_data.seek(0)  # Reset file pointer
        else:
            # Regular JSON request
            json_data = request.get_json()
            logger.info(f"Received JSON payload: {json_data}")
        
        if not json_data:
            return jsonify({
                "ResultCode": 400,
                "ErrorDescription": "Missing incident data",
                "ResultStatus": "ERROR",
                "data": ""
            }), 400
        
        # Validate required fields
        required_fields = ['eventCallDesc', 'callerFirstName', 'callerLastName']
        missing_fields = [field for field in required_fields if not json_data.get(field)]
        
        if missing_fields:
            return jsonify({
                "ResultCode": 422,
                "ErrorDescription": f"Missing required fields: {', '.join(missing_fields)}",
                "ResultStatus": "ERROR", 
                "data": ""
            }), 422
        
        # Generate mock ticket ID
        ticket_id = f"NETANYA-{datetime.now().year}-{str(uuid.uuid4().int)[:6]}"
        
        # Store incident data
        incident_data = {
            "ticket_id": ticket_id,
            "payload": json_data,
            "has_file": 'attachment' in request.files if 'multipart/form-data' in request.content_type else False,
            "timestamp": datetime.now().isoformat(),
            "status": "submitted"
        }
        incident_storage[ticket_id] = incident_data
        
        # Log request for debugging
        request_log.append({
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "method": request.method,
            "headers": dict(request.headers),
            "payload_summary": {
                "caller": f"{json_data.get('callerFirstName')} {json_data.get('callerLastName')}",
                "description": json_data.get('eventCallDesc', '')[:50] + "...",
                "has_file": incident_data["has_file"]
            }
        })
        
        # Simulate processing delay
        import time
        time.sleep(0.1)
        
        # Return successful SharePoint response format
        response_data = {
            "ResultCode": 200,
            "ErrorDescription": "",
            "ResultStatus": "SUCCESS CREATE",
            "data": ticket_id
        }
        
        logger.info(f"Mock incident created successfully: {ticket_id}")
        return jsonify(response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return jsonify({
            "ResultCode": 400,
            "ErrorDescription": f"Invalid JSON format: {str(e)}",
            "ResultStatus": "ERROR",
            "data": ""
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "ResultCode": 500,
            "ErrorDescription": f"Internal server error: {str(e)}",
            "ResultStatus": "ERROR",
            "data": ""
        }), 500

@app.route('/api/incidents/<ticket_id>', methods=['GET'])
def get_incident(ticket_id):
    """Get incident details by ticket ID."""
    if ticket_id in incident_storage:
        return jsonify(incident_storage[ticket_id])
    else:
        return jsonify({
            "ResultCode": 404,
            "ErrorDescription": "Incident not found",
            "ResultStatus": "ERROR",
            "data": ""
        }), 404

@app.route('/admin/incidents', methods=['GET'])
def list_incidents():
    """List all submitted incidents (for debugging)."""
    return jsonify({
        "total_incidents": len(incident_storage),
        "incidents": list(incident_storage.values())
    })

@app.route('/admin/requests', methods=['GET'])
def list_requests():
    """List all API requests (for debugging)."""
    return jsonify({
        "total_requests": len(request_log),
        "requests": request_log[-10:]  # Last 10 requests
    })

@app.route('/admin/reset', methods=['POST'])
def reset_data():
    """Reset all mock data."""
    global incident_storage, request_log
    incident_storage.clear()
    request_log.clear()
    logger.info("Mock data reset")
    return jsonify({"message": "Mock data reset successfully"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "ResultCode": 404,
        "ErrorDescription": "Endpoint not found",
        "ResultStatus": "ERROR",
        "data": ""
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "ResultCode": 500,
        "ErrorDescription": "Internal server error",
        "ResultStatus": "ERROR",
        "data": ""
    }), 500

if __name__ == '__main__':
    logger.info(f"Starting Mock SharePoint Service on port {PORT} in {MOCK_MODE} mode")
    app.run(host='0.0.0.0', port=PORT, debug=(MOCK_MODE == 'development'))
