#!/bin/bash
# Pre-commit verification script
# Run this to validate all Phase E components before committing

set -e

echo "=========================================="
echo "PHASE E PRE-COMMIT VERIFICATION"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
PASS=0
FAIL=0

# Test function
test_item() {
    local name=$1
    local command=$2
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $name"
        ((FAIL++))
    fi
}

echo "STEP 1: Checking Python & Dependencies"
echo "----------------------------------------"
test_item "Python installed" "python --version"
test_item "pip installed" "pip --version"
test_item "requirements.txt exists" "[ -f requirements.txt ]"

echo ""
echo "STEP 2: Checking Database Configuration"
echo "----------------------------------------"
test_item ".env.example exists" "[ -f .env.example ]"
test_item "PostgreSQL driver (psycopg2)" "python -c 'import psycopg2'"
test_item "SQLAlchemy" "python -c 'import sqlalchemy'"
test_item "Alembic migrations folder" "[ -d alembic ]"

echo ""
echo "STEP 3: Checking Code Files"
echo "----------------------------------------"
test_item "Main application" "[ -f knowledge_agent_bot.py ]"
test_item "Infra models" "[ -f infra/models.py ]"
test_item "Async execution module" "[ -d async_execution ]"
test_item "Analytics module" "[ -d analytics ]"
test_item "Knowledge graph module" "[ -d knowledge_graph ]"

echo ""
echo "STEP 4: Checking Test Files"
echo "----------------------------------------"
test_item "E1 Database tests" "[ -f tests/test_e1_database.py ]"
test_item "E1 Authentication tests" "[ -f tests/test_e1_authentication.py ]"
test_item "E2 Async tests" "[ -f tests/test_e2_async.py ]"
test_item "E3 Analytics tests" "[ -f tests/test_e3_analytics.py ]"
test_item "E4 Knowledge graph tests" "[ -f tests/test_e4_knowledge_graph.py ]"
test_item "E1-E4 Integration tests" "[ -f tests/test_integration_e1_e4.py ]"

echo ""
echo "STEP 5: Checking Documentation"
echo "----------------------------------------"
test_item "README.md updated" "grep -q 'Phase E' README.md"
test_item "PHASE_E_COMPLETION.md exists" "[ -f PHASE_E_COMPLETION.md ]"
test_item "PHASE_E_SUMMARY.md exists" "[ -f PHASE_E_SUMMARY.md ]"
test_item "DEPLOYMENT_CHECKLIST.md exists" "[ -f DEPLOYMENT_CHECKLIST.md ]"
test_item "PRE_COMMIT_CHECKLIST.md exists" "[ -f PRE_COMMIT_CHECKLIST.md ]"

echo ""
echo "STEP 6: Checking Deployment Files"
echo "----------------------------------------"
test_item "docker-compose.yml exists" "[ -f docker-compose.yml ]"
test_item "API examples" "[ -f examples/phase_e_api_examples.py ]"

echo ""
echo "STEP 7: Python Syntax Check"
echo "----------------------------------------"
test_item "Knowledge agent bot" "python -m py_compile knowledge_agent_bot.py"
test_item "Async execution" "python -m py_compile async_execution/__init__.py"
test_item "Analytics" "python -m py_compile analytics/__init__.py"
test_item "Knowledge graph" "python -m py_compile knowledge_graph/__init__.py"

echo ""
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for commit.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review and fix.${NC}"
    exit 1
fi
