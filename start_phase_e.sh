#!/bin/bash
# start_phase_e.sh - Start Phase E services for local development

set -e

echo "=========================================="
echo "PHASE E: STARTING SERVICES"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
command -v python &> /dev/null || { echo "Python not found"; exit 1; }
command -v pip &> /dev/null || { echo "pip not found"; exit 1; }

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env not found. Running setup first...${NC}"
    bash setup_phase_e.sh
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Parse arguments
MODE="${1:-development}"

if [ "$MODE" == "production" ]; then
    echo -e "${BLUE}Starting in PRODUCTION mode${NC}"
    export ENVIRONMENT=production
    export DEBUG=false
else
    echo -e "${BLUE}Starting in DEVELOPMENT mode${NC}"
    export ENVIRONMENT=development
    export DEBUG=true
fi

echo ""
echo "=========================================="
echo "Service Startup Instructions"
echo "=========================================="
echo ""
echo -e "${GREEN}Main Application (FastAPI)${NC}"
echo "Terminal 1:"
echo "  uvicorn knowledge_agent_bot:app --reload --port 8000"
echo ""
echo -e "${GREEN}Celery Worker${NC}"
echo "Terminal 2:"
echo "  celery -A async_execution worker --loglevel=info --concurrency=4"
echo ""
echo -e "${GREEN}Celery Beat (Scheduler)${NC}"
echo "Terminal 3:"
echo "  celery -A async_execution beat --loglevel=info"
echo ""
echo "=========================================="
echo ""

# Helper function to check service
check_service() {
    local name=$1
    local url=$2
    local port=$3
    
    echo -n "Checking $name... "
    if timeout 2 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${YELLOW}✗ Not responding${NC}"
    fi
}

echo -e "${BLUE}Service Status${NC}"
check_service "PostgreSQL" "localhost" 5432 || true
check_service "Redis" "localhost" 6379 || true
check_service "Neo4j" "localhost" 7687 || true
echo ""

echo -e "${BLUE}API Documentation${NC}"
echo "Once application is running:"
echo "  Swagger UI: http://localhost:8000/docs"
echo "  ReDoc: http://localhost:8000/redoc"
echo ""

echo -e "${YELLOW}Quick Test Commands${NC}"
echo ""
echo "Health Check:"
echo "  curl http://localhost:8000/api/health"
echo ""
echo "Get Metrics:"
echo "  curl http://localhost:8000/api/metrics"
echo ""
echo -e "${GREEN}Ready to start services!${NC}"
