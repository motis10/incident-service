# Deployment Guide

## Overview

This guide covers deploying the Netanya Incident Service to Google Cloud Run using multiple deployment methods including CI/CD automation, manual deployment, and infrastructure as code.

## Prerequisites

### Required Tools
- Docker Desktop
- Google Cloud SDK (`gcloud`)
- GitHub account with repository access
- Terraform (for infrastructure as code - optional)

### Required Accounts & Permissions
- Google Cloud Project with billing enabled
- Cloud Run API enabled
- Container Registry or Artifact Registry access
- Secret Manager API enabled (for production secrets)
- GitHub repository with Actions enabled (for CI/CD)

## Environment Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Deployment environment | Yes | `development` |
| `BUILD_TARGET` | Docker build target | No | `development` |
| `DEBUG_MODE` | Enable debug features | No | `true` |
| `LOG_LEVEL` | Logging verbosity | No | `DEBUG` |
| `PORT` | Service port | No | `8000` |
| `SHAREPOINT_ENDPOINT` | SharePoint API URL | Yes | - |
| `MAX_FILE_SIZE_MB` | Maximum file upload size | No | `10` |
| `CONTAINER_SUFFIX` | Container name suffix | No | - |

### Secret Management

**Production Secrets** (stored in Google Secret Manager):
- `sharepoint-endpoint`: SharePoint API endpoint URL
- `api-credentials`: SharePoint authentication credentials (future)

## Deployment Methods

### 1. Automated CI/CD Deployment (Recommended)

#### Setup GitHub Secrets

Configure the following secrets in your GitHub repository:

```bash
# Production
GCP_SA_KEY_PRODUCTION=<base64-encoded-service-account-key>
GCP_PROJECT_ID_PRODUCTION=<your-production-project-id>

# Staging  
GCP_SA_KEY_STAGING=<base64-encoded-service-account-key>
GCP_PROJECT_ID_STAGING=<your-staging-project-id>
```

#### Service Account Setup

Create service accounts with required permissions:

```bash
# Create service account
gcloud iam service-accounts create netanya-deployer \
  --display-name="Netanya Service Deployer"

# Grant required roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:netanya-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:netanya-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:netanya-deployer@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=netanya-deployer@PROJECT_ID.iam.gserviceaccount.com
```

#### Deployment Triggers

- **Staging**: Automatic deployment on push to `develop` branch
- **Production**: Automatic deployment on push to `main` branch
- **Manual**: Can be triggered via GitHub Actions workflow dispatch

### 2. Manual Deployment

#### Build and Push Image

```bash
# Build Docker image with production target
docker build --target production -t netanya-incident-service .

# Tag for registry
docker tag netanya-incident-service gcr.io/PROJECT_ID/netanya-incident-service:latest

# Push to registry
docker push gcr.io/PROJECT_ID/netanya-incident-service:latest
```

#### Deploy to Cloud Run

```bash
# Deploy to staging
gcloud run deploy netanya-incident-service-staging \
  --image gcr.io/PROJECT_ID/netanya-incident-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=staging,DEBUG_MODE=true" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10

# Deploy to production
gcloud run deploy netanya-incident-service \
  --image gcr.io/PROJECT_ID/netanya-incident-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production,DEBUG_MODE=false" \
  --set-secrets="SHAREPOINT_ENDPOINT=sharepoint-endpoint:latest" \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=100
```

### 3. CI/CD Workflow

The project uses GitHub Actions for automated builds and deployments. The workflow is defined in `.github/workflows/build-and-deploy.yml` and automatically:
- Builds Docker images on push
- Pushes to Google Artifact Registry
- Deploys to Cloud Run (production) when pushing to main branch

## Configuration Management

### Environment-Specific Configuration

Configuration is now managed through `.env` files rather than YAML:

#### Staging Configuration
```bash
# Copy and modify env.example for staging
ENVIRONMENT=staging
BUILD_TARGET=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
PORT=8000
SHAREPOINT_ENDPOINT=https://staging-sharepoint.netanya.muni.il/api
CONTAINER_SUFFIX=-staging
```

#### Production Configuration
```bash
# Use prod.env for production deployment
ENVIRONMENT=production
BUILD_TARGET=production
DEBUG_MODE=false
LOG_LEVEL=INFO
PORT=8000
SHAREPOINT_ENDPOINT=https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident
MAX_FILE_SIZE_MB=10
CONTAINER_SUFFIX=-prod
```

### Secret Management

#### Create Secrets

```bash
# Create SharePoint endpoint secret
gcloud secrets create sharepoint-endpoint \
  --data-file=- <<< "https://production-sharepoint.netanya.muni.il/api"

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding sharepoint-endpoint \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Health Checks and Monitoring

### Health Check Configuration

Cloud Run automatically configures health checks using the service's health endpoint:

- **Health Endpoint**: `/health` - Comprehensive health status with dependency checks
  - Returns overall status (healthy/degraded/unhealthy)
  - Includes SharePoint connectivity status
  - Includes configuration validation status
  - Provides response time metrics

### Monitoring Setup

#### Google Cloud Monitoring

```bash
# Enable monitoring APIs
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Create notification channels (optional)
gcloud alpha monitoring channels create \
  --channel-content-from-file=monitoring/alerts.yaml
```

#### Log Aggregation

```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=netanya-incident-service" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"

# Create log-based metrics
gcloud logging metrics create incident_submission_errors \
  --description="Count of incident submission errors" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="netanya-incident-service" AND severity="ERROR"'
```

## Scaling Configuration

### Auto-scaling Settings

| Environment | Min Instances | Max Instances | CPU | Memory | Concurrency |
|-------------|---------------|---------------|-----|---------|-------------|
| Staging | 0 | 10 | 1 | 512Mi | 80 |
| Production | 1 | 100 | 2 | 1Gi | 80 |

### Performance Tuning

#### CPU and Memory Optimization
```bash
# Monitor resource usage
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"

# Adjust resources based on metrics
gcloud run services update netanya-incident-service \
  --memory=2Gi \
  --cpu=2
```

#### Connection Management
```bash
# Configure VPC connector for private resources
gcloud compute networks vpc-access connectors create netanya-connector \
  --region=us-central1 \
  --subnet=default \
  --subnet-project=PROJECT_ID \
  --min-instances=2 \
  --max-instances=10
```

## Security Configuration

### Network Security

```bash
# Create firewall rules for VPC
gcloud compute firewall-rules create allow-netanya-service \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:8000 \
  --source-ranges=10.0.0.0/8 \
  --target-tags=netanya-service
```

### IAM Configuration

```bash
# Create custom role for service
gcloud iam roles create netanyaIncidentService \
  --project=PROJECT_ID \
  --title="Netanya Incident Service" \
  --description="Custom role for Netanya incident service" \
  --permissions="secretmanager.versions.access,logging.logEntries.create"

# Bind role to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:netanya-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="projects/PROJECT_ID/roles/netanyaIncidentService"
```

## Rollback Procedures

### Automatic Rollback

```bash
# List revisions
gcloud run revisions list --service=netanya-incident-service

# Rollback to previous revision
gcloud run services update-traffic netanya-incident-service \
  --to-revisions=REVISION_NAME=100
```

### Manual Rollback

```bash
# Deploy specific image version
gcloud run deploy netanya-incident-service \
  --image gcr.io/PROJECT_ID/netanya-incident-service:PREVIOUS_TAG \
  --platform managed \
  --region us-central1
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Check configuration
gcloud run services describe netanya-incident-service
```

#### Health Check Failures
```bash
# Test health endpoint manually
curl https://YOUR-SERVICE-URL.run.app/health

# Expected response includes:
# - overall_status: "healthy", "degraded", or "unhealthy"
# - dependencies: SharePoint connectivity status
# - service_info: Version and environment info
# - response_time_ms: Health check response time
```

#### Secret Access Issues
```bash
# Verify secret permissions
gcloud secrets versions access latest --secret="sharepoint-endpoint"

# Check IAM bindings
gcloud secrets get-iam-policy sharepoint-endpoint
```

### Emergency Procedures

#### Service Down
1. Check Cloud Run service status
2. Review recent deployments
3. Check health endpoints
4. Review application logs
5. Consider rollback if recent deployment

#### High Error Rate
1. Check application logs for error patterns
2. Monitor resource usage
3. Review SharePoint connectivity
4. Check rate limiting
5. Scale up resources if needed

## Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review error logs and metrics
- Check resource utilization
- Verify health check status
- Update dependency vulnerabilities

#### Monthly  
- Review and rotate secrets
- Update base Docker images
- Performance optimization review
- Disaster recovery testing

#### Quarterly
- Security audit and compliance review
- Cost optimization analysis
- Capacity planning review
- Infrastructure updates

### Backup and Recovery

#### Configuration Backup
```bash
# Export service configuration
gcloud run services describe netanya-incident-service \
  --format="export" > backup/service-config-$(date +%Y%m%d).yaml

# Export secrets
gcloud secrets versions access latest --secret="sharepoint-endpoint" > backup/secrets-$(date +%Y%m%d).txt
```

#### Disaster Recovery
1. **RTO**: 15 minutes (Recovery Time Objective)
2. **RPO**: 1 hour (Recovery Point Objective)  
3. **Recovery Steps**:
   - Deploy to backup region
   - Update DNS if needed
   - Verify service functionality
   - Monitor for issues

## Support Contacts

- **Technical Issues**: Cloud Run Support
- **Security Issues**: Security Team
- **Infrastructure**: DevOps Team
- **Application Issues**: Development Team
