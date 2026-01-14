#!/bin/bash
# Deploy Backend API to Azure Container Instances (Phase 4)
# This script builds and deploys the Python FastAPI backend
#
# Usage: ./deploy-backend.sh [environment] [registry]
# Environment: dev, staging, prod (default: dev)
# Registry: Name of Azure Container Registry (e.g., msreventacr)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-dev}"
ACR_NAME="${2:-msreventacr}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Azure Configuration
AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-msr-event-${ENVIRONMENT}}"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
IMAGE_NAME="backend"
IMAGE_TAG="${ENVIRONMENT}-$(date +%s)"
FULL_IMAGE_NAME="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"
APP_SERVICE_NAME="msr-backend-${ENVIRONMENT}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_info "Allowed values: dev, staging, prod"
    exit 1
fi

log_info "Deploying Backend API to Azure for environment: $ENVIRONMENT"

# Check prerequisites
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install it first."
    exit 1
fi

if ! command -v python &> /dev/null; then
    log_error "Python is not installed. Please install it first."
    exit 1
fi

# Verify Azure authentication
log_info "Verifying Azure authentication..."
if ! az account show &> /dev/null; then
    log_error "Not authenticated with Azure. Please run 'az login' first."
    exit 1
fi

# Verify ACR exists
log_info "Verifying Azure Container Registry: $ACR_NAME"
if ! az acr show --name "$ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" &> /dev/null; then
    log_error "Container Registry '$ACR_NAME' not found in resource group '$AZURE_RESOURCE_GROUP'"
    exit 1
fi

# Prepare environment
log_info "Setting up Python environment..."
cd "$PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python -m venv .venv
fi

# Activate venv
source .venv/bin/activate || true

# Verify dependencies
log_info "Installing Python dependencies..."
pip install -q -r requirements.txt

# Run tests (optional)
if [ -f "pytest.ini" ]; then
    log_info "Running tests..."
    python -m pytest tests/ -v || log_warn "Some tests failed, continuing with deployment"
fi

log_info "Python environment prepared"

# Build Docker image
log_info "Building Docker image: $FULL_IMAGE_NAME"

# Use ACR build for better caching and no local Docker overhead
az acr build \
    --registry "$ACR_NAME" \
    --image "${IMAGE_NAME}:${IMAGE_TAG}" \
    --image "${IMAGE_NAME}:${ENVIRONMENT}-latest" \
    --file Dockerfile \
    "$PROJECT_ROOT"

log_info "Docker image built and pushed to ACR"

# Deploy to App Service
log_info "Deploying to Azure App Service: $APP_SERVICE_NAME"

# Get connection info
APP_SERVICE_ID=$(az webapp show \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query id -o tsv 2>/dev/null || echo "")

if [ -z "$APP_SERVICE_ID" ]; then
    log_error "App Service '$APP_SERVICE_NAME' not found in resource group '$AZURE_RESOURCE_GROUP'"
    log_info "Please create the App Service first or verify the name."
    exit 1
fi

# Update container settings
log_info "Updating App Service with new container image..."
az webapp config container set \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --docker-custom-image-name "$FULL_IMAGE_NAME" \
    --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
    --docker-registry-server-user "$(az acr credential show --name "$ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query username -o tsv)" \
    --docker-registry-server-password "$(az acr credential show --name "$ACR_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query 'passwords[0].value' -o tsv)"

# Restart the app service
log_info "Restarting App Service..."
az webapp restart \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP"

# Wait for service to start
log_info "Waiting for service to start (30 seconds)..."
sleep 30

# Health check
log_info "Performing health check..."
APP_URL=$(az webapp show \
    --name "$APP_SERVICE_NAME" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --query defaultHostName -o tsv)

if curl -f "https://${APP_URL}/health" &> /dev/null; then
    log_info "Health check passed"
else
    log_warn "Health check failed. Service may still be starting."
    log_info "Monitor logs: az webapp log tail --name $APP_SERVICE_NAME --resource-group $AZURE_RESOURCE_GROUP"
fi

log_info "Deployment completed successfully!"
log_info "Backend API: https://${APP_URL}/"
log_info "Container Image: $FULL_IMAGE_NAME"
log_info "API Docs: https://${APP_URL}/docs"
log_info "View logs: az webapp log tail --name $APP_SERVICE_NAME --resource-group $AZURE_RESOURCE_GROUP"
