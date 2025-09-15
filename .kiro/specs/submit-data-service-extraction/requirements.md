# Requirements Document

## Introduction

The Netanya Incident Service is a standalone microservice that extracts the municipality API integration functionality from the current Python client application. This service will be deployed as a Docker container on Google Cloud Run and provide a single public API endpoint to handle complaint submissions to the Netanya municipality SharePoint system.

The service enables separation of concerns by isolating the complex municipality API integration logic, headers management, and payload formatting from the client application, while maintaining exact compatibility with the existing NetanyaMuni SharePoint endpoint and data models.

## Requirements

### Requirement 1: Netanya Municipality Incident Submission Service
**Objective:** As a municipality complaint system, I want to provide a specialized incident submission service for Netanya municipality, so that client applications can submit complaints through the official SharePoint-based incidents.ashx endpoint.

#### Acceptance Criteria
1. WHEN a client submits incident data with user information, category, and street details THEN the Netanya Incident Service SHALL format the data according to the SharePoint incidents.ashx API requirements
2. WHEN the service receives a submission request THEN the Netanya Incident Service SHALL validate all required fields (callerFirstName, callerLastName, callerPhone1, houseNumber) are present
3. WHEN all validation passes THEN the Netanya Incident Service SHALL construct a multipart/form-data request targeting `/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident`
4. WHEN the SharePoint API request is successful THEN the Netanya Incident Service SHALL return the municipality ticket ID and success status
5. WHEN the SharePoint API request fails THEN the Netanya Incident Service SHALL return structured error responses with municipality-specific error codes

### Requirement 2: SharePoint NetanyaMuni API Integration
**Objective:** As a technical integration layer, I want to maintain exact compatibility with Netanya's SharePoint NetanyaMuni incidents system, so that all submissions reach the municipal ticketing system correctly.

#### Acceptance Criteria
1. WHEN constructing API requests THEN the Netanya Incident Service SHALL include municipality-required headers (Origin: https://www.netanya.muni.il, Referer: PublicComplaints.aspx page, X-Requested-With: XMLHttpRequest)
2. WHEN preparing the incident payload THEN the Netanya Incident Service SHALL use the NetanyaMuni structure with fixed values (eventCallSourceId=4, cityCode="7400", cityDesc="נתניה", eventCallCenterId="3", streetCode="898", streetDesc="קרל פופר", contactUsType="3")
3. WHEN building the multipart request THEN the Netanya Incident Service SHALL use WebKit boundary format with "json" field name as required by the SharePoint handler
4. WHEN targeting the endpoint THEN the Netanya Incident Service SHALL POST to `https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident`
5. WHEN handling responses THEN the Netanya Incident Service SHALL parse the SharePoint JSON response format with ResultCode, ErrorDescription, ResultStatus, and data fields

### Requirement 3: Docker-First Development and Deployment
**Objective:** As a DevOps engineer, I want a containerized service with local development support and Cloud Run deployment, so that I can develop locally and deploy to Google Cloud seamlessly.

#### Acceptance Criteria
1. WHEN developers run the service locally THEN the Netanya Incident Service SHALL provide a docker-compose.yml that starts the service with all dependencies
2. WHEN the docker-compose environment starts THEN the Netanya Incident Service SHALL include a mock SharePoint endpoint for local testing
3. WHEN building for Cloud Run THEN the Netanya Incident Service SHALL use a multi-stage Dockerfile optimized for small container size and fast startup
4. WHEN deployed to Cloud Run THEN the Netanya Incident Service SHALL expose the service on the configured PORT environment variable
5. WHEN the container starts THEN the Netanya Incident Service SHALL perform health checks and readiness probes for Cloud Run integration

### Requirement 4: Independent Repository Structure
**Objective:** As a project maintainer, I want a completely independent repository for the incident service, so that it can be developed, versioned, and deployed separately from the client application.

#### Acceptance Criteria
1. WHEN setting up the new repository THEN the Netanya Incident Service SHALL include its own requirements.txt with only necessary dependencies (FastAPI, requests, uvicorn, pydantic)
2. WHEN organizing the codebase THEN the Netanya Incident Service SHALL include copied data models (UserData, Category, StreetNumber, APIPayload, APIResponse) as independent code
3. WHEN setting up CI/CD THEN the Netanya Incident Service SHALL include GitHub Actions workflows for building and deploying to Cloud Run
4. WHEN documenting the service THEN the Netanya Incident Service SHALL include API documentation, deployment guides, and integration examples
5. WHEN versioning releases THEN the Netanya Incident Service SHALL use semantic versioning independent of the client application

### Requirement 5: FastAPI REST Interface with OpenAPI
**Objective:** As a client developer, I want a well-documented REST API with automatic OpenAPI documentation, so that I can integrate easily and understand all available endpoints.

#### Acceptance Criteria
1. WHEN a client makes a POST request to `/incidents/submit` THEN the Netanya Incident Service SHALL accept JSON payload with user_data, category, street, custom_text, and optional extra_files for image attachments
2. WHEN accessing `/docs` AND debug mode is enabled THEN the Netanya Incident Service SHALL provide automatic Swagger/OpenAPI documentation
3. WHEN accessing `/docs` AND production mode is enabled THEN the Netanya Incident Service SHALL return HTTP 404 (endpoint not found)
4. WHEN the service starts THEN the Netanya Incident Service SHALL provide health check endpoint at `/health` for Cloud Run monitoring
5. WHEN validation fails THEN the Netanya Incident Service SHALL return HTTP 422 with detailed validation error messages using Pydantic
6. WHEN internal errors occur THEN the Netanya Incident Service SHALL return HTTP 500 with structured error responses and correlation IDs for tracking
7. WHEN extra_files contains an image attachment THEN the Netanya Incident Service SHALL validate file type (JPEG, PNG, GIF), file size (max 10MB), and include it in the multipart SharePoint request
8. WHEN file validation fails THEN the Netanya Incident Service SHALL return HTTP 422 with specific file validation error messages

### Requirement 6: File Upload and Image Attachment Support
**Objective:** As a user submitting incident reports, I want to attach images to provide visual evidence of the issue, so that municipality staff can better understand and address the problem.

#### Acceptance Criteria
1. WHEN clients provide extra_files with a single image attachment THEN the Netanya Incident Service SHALL accept common image formats (JPEG, PNG, GIF, WebP)
2. WHEN validating uploaded file THEN the Netanya Incident Service SHALL enforce maximum file size limit (10MB per file)
3. WHEN processing image attachments THEN the Netanya Incident Service SHALL include them in the multipart request to SharePoint using the existing file upload mechanism
4. WHEN SharePoint API supports file attachments THEN the Netanya Incident Service SHALL pass files with proper Content-Disposition headers and MIME types
5. WHEN file upload fails THEN the Netanya Incident Service SHALL return detailed error information including file name, size, and failure reason
6. WHEN file is too large or invalid format THEN the Netanya Incident Service SHALL reject the submission with clear guidance on acceptable formats and sizes

### Requirement 7: Environment-Based Configuration for Multi-Environment Deployment
**Objective:** As a deployment operator, I want comprehensive environment-based configuration, so that I can deploy to local, staging, and production environments with appropriate municipality endpoint settings.

#### Acceptance Criteria
1. WHEN the service starts THEN the Netanya Incident Service SHALL read configuration from environment variables with validation and defaults
2. WHEN NETANYA_ENDPOINT is provided THEN the Netanya Incident Service SHALL use it as the target SharePoint incidents.ashx endpoint
3. WHEN ENVIRONMENT is set to "development" THEN the Netanya Incident Service SHALL enable mock mode and detailed logging
4. WHEN ENVIRONMENT is set to "production" THEN the Netanya Incident Service SHALL enforce HTTPS endpoints and minimal logging
5. WHEN required environment variables are missing THEN the Netanya Incident Service SHALL fail fast with clear configuration error messages

### Requirement 8: Local Development with Mock SharePoint Service
**Objective:** As a developer, I want to develop and test without hitting the production municipality system, so that I can iterate quickly and safely.

#### Acceptance Criteria
1. WHEN running docker-compose THEN the Netanya Incident Service SHALL start alongside a mock SharePoint service container
2. WHEN the mock service receives requests THEN the Mock SharePoint Service SHALL respond with realistic NetanyaMuni API responses including ticket IDs
3. WHEN the mock service is active THEN the Mock SharePoint Service SHALL log all received payloads for debugging and validation
4. WHEN switching environments THEN the Netanya Incident Service SHALL seamlessly switch between mock and production endpoints via configuration
5. WHEN mock mode is enabled THEN the Netanya Incident Service SHALL add request/response logging for development debugging

### Requirement 9: Debug/Production Mode Configuration
**Objective:** As a developer and operator, I want clear separation between debug and production modes, so that I can safely develop with mocks and deploy with real SharePoint integration.

#### Acceptance Criteria
1. WHEN DEBUG_MODE environment variable is set to "true" THEN the Netanya Incident Service SHALL always return mock responses without making external requests
2. WHEN DEBUG_MODE is set to "false" or not provided THEN the Netanya Incident Service SHALL make real multipart requests to the configured SharePoint endpoint
3. WHEN in debug mode THEN the Netanya Incident Service SHALL return consistent mock responses (ResultCode=200, ResultStatus="SUCCESS CREATE", data="MOCK-{timestamp}")
4. WHEN in production mode THEN the Netanya Incident Service SHALL construct and send actual multipart/form-data requests to `https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident`
5. WHEN the service starts THEN the Netanya Incident Service SHALL log the current mode (DEBUG/PRODUCTION) and target endpoint clearly
