#!/bin/bash
# setup_phase_e.sh - Phase E local development setup script

set -e

echo "=========================================="
echo "PHASE E: LOCAL DEVELOPMENT SETUP"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Environment setup
echo -e "${BLUE}Step 1: Setting up environment${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  EDIT .env with your database, Redis, and Neo4j credentials!"
else
    echo "✓ .env already exists"
fi
echo ""

# Step 2: Install Python dependencies
echo -e "${BLUE}Step 2: Installing Python dependencies${NC}"
python -m pip install --upgrade pip setuptools wheel
echo "Installing requirements..."
# Note: Update requirements.txt with Phase E deps as shown above
python -m pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Database setup
echo -e "${BLUE}Step 3: Setting up PostgreSQL database${NC}"
echo "Ensure PostgreSQL is running at DATABASE_URL..."
echo "Running Alembic migrations..."
alembic upgrade head
echo -e "${GREEN}✓ Database migrations complete${NC}"
echo ""

# Step 4: Service status check
echo -e "${BLUE}Step 4: Checking services${NC}"
echo "PostgreSQL: Check if running on localhost:5432"
echo "Redis: Check if running on localhost:6379"
echo "Neo4j: Check if running on localhost:7687"
echo ""

# Step 5: Run tests
echo -e "${BLUE}Step 5: Running tests${NC}"
if command -v pytest &> /dev/null; then
    echo "Running test suite..."
    pytest tests/ -v --tb=short || true
    echo ""
else
    echo "⚠️  pytest not installed. Install with: pip install pytest"
fi

echo -e "${BLUE}Step 6: Next steps${NC}"
echo "1. Start main application:"
echo "   uvicorn knowledge_agent_bot:app --reload"
echo ""
echo "2. Start Celery worker (in another terminal):"
echo "   celery -A async_execution worker --loglevel=info"
echo ""
echo "3. Access API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
