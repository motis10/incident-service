# GitHub Actions Setup for Google Cloud

## Prerequisites

1. **Google Cloud Project**: `muni-incident-service`
2. **Artifact Registry**: `netanya-incident-service` repository in `europe-west1`
3. **Cloud Run**: Service will be deployed automatically

## Setup Steps

### 1. Create Service Account

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions CI/CD"

# Grant necessary permissions
gcloud projects add-iam-policy-binding muni-incident-service \
  --member="serviceAccount:github-actions@muni-incident-service.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding muni-incident-service \
  --member="serviceAccount:github-actions@muni-incident-service.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding muni-incident-service \
  --member="serviceAccount:github-actions@muni-incident-service.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 2. Create and Download Service Account Key

```bash
# Create service account key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@muni-incident-service.iam.gserviceaccount.com

# Display the key content (copy this to GitHub Secrets)
cat github-actions-key.json
```

### 3. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `GCP_SA_KEY`
   - **Value**: Paste the entire content of `github-actions-key.json`

### 4. Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Workflow Features

### Automatic Triggers
- **Push to main**: Builds, pushes to Artifact Registry, and deploys to Cloud Run
- **Push to develop**: Builds and pushes to Artifact Registry (no deployment)
- **Pull Requests**: Builds and pushes to Artifact Registry for testing

### Image Tagging Strategy
- **main branch**: `latest`, `main-<sha>`
- **develop branch**: `develop-<sha>`
- **PR branches**: `pr-<number>`

### Security Features
- Uses Google Cloud Workload Identity (recommended)
- Service account with minimal required permissions
- No hardcoded credentials in workflow files

## Manual Deployment

If you want to deploy manually without GitHub Actions:

```bash
# Build and push manually
docker build --target production -t europe-west1-docker.pkg.dev/muni-incident-service/netanya-incident-service/incident-service:latest .
docker push europe-west1-docker.pkg.dev/muni-incident-service/netanya-incident-service/incident-service:latest

# Deploy to Cloud Run
gcloud run deploy incident-service \
  --image europe-west1-docker.pkg.dev/muni-incident-service/netanya-incident-service/incident-service:latest \
  --platform managed \
  --region europe-west1 \
  --port 8080 \
  --set-env-vars="PORT=8080,DEBUG_MODE=false,ENVIRONMENT=production,SHAREPOINT_ENDPOINT=https://www.netanya.muni.il/_layouts/15/NetanyaMuni/incidents.ashx?method=CreateNewIncident" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure service account has correct roles
2. **Artifact Registry Access**: Verify repository exists and permissions are set
3. **Cloud Run Deployment**: Check if service account has Cloud Run admin role
4. **Image Not Found**: Ensure image is pushed before deployment

### Debug Commands

```bash
# Check service account permissions
gcloud projects get-iam-policy muni-incident-service \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:github-actions@muni-incident-service.iam.gserviceaccount.com"

# List Artifact Registry repositories
gcloud artifacts repositories list --location=europe-west1

# Check Cloud Run services
gcloud run services list --region=europe-west1
```

## Security Best Practices

1. **Rotate Keys**: Regularly rotate service account keys
2. **Minimal Permissions**: Only grant necessary roles
3. **Monitor Usage**: Review service account usage in Cloud Console
4. **Secrets Management**: Use GitHub Secrets for sensitive data
5. **Branch Protection**: Protect main branch with required reviews
