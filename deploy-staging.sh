#!/bin/bash
# Deploy to Google Cloud Run for staging/production testing

echo "🚀 DEPLOYING TO CLOUD RUN STAGING"
echo "================================="

# Set your project details
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="netanya-incident-staging"

# Build and deploy
echo "1. Building image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .

echo "2. Pushing to registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "3. Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=staging,DEBUG_MODE=false,LOG_LEVEL=INFO" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10

echo "4. Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test with:"
echo "python test-production.py $SERVICE_URL"
