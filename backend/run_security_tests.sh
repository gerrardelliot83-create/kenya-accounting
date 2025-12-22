#!/bin/bash
###############################################################################
# Security Test Suite Runner
#
# This script runs the comprehensive security test suite for the Kenya SMB
# Accounting MVP backend application.
#
# Usage:
#   ./run_security_tests.sh [options]
#
# Options:
#   --all           Run all 27 security tests (default)
#   --access        Run access control tests only
#   --crypto        Run cryptographic failures tests only
#   --injection     Run injection tests only
#   --auth          Run authentication tests only
#   --quick         Run quick validation (collect tests only)
#   --coverage      Run with coverage report
#   --verbose       Run with verbose output
#   --help          Show this help message
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please create virtual environment first:"
    echo "  python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if server is running
echo -e "${BLUE}Checking if server is running...${NC}"
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Server does not appear to be running on http://localhost:8000${NC}"
    echo "Tests will fail without a running server."
    echo ""
    echo "To start the server in another terminal:"
    echo "  cd $SCRIPT_DIR"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Parse command line arguments
TEST_CATEGORY="all"
VERBOSE=""
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            TEST_CATEGORY="all"
            shift
            ;;
        --access)
            TEST_CATEGORY="TestBrokenAccessControl"
            shift
            ;;
        --crypto)
            TEST_CATEGORY="TestCryptographicFailures"
            shift
            ;;
        --injection)
            TEST_CATEGORY="TestInjection"
            shift
            ;;
        --auth)
            TEST_CATEGORY="TestAuthenticationFailures"
            shift
            ;;
        --quick)
            echo -e "${BLUE}Running quick validation...${NC}"
            python -m pytest tests/test_security.py --collect-only -q
            exit $?
            ;;
        --coverage)
            COVERAGE="--cov=app --cov-report=html --cov-report=term"
            shift
            ;;
        --verbose)
            VERBOSE="-vv -s"
            shift
            ;;
        --help)
            head -n 25 "$0" | tail -n 23
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
if [ "$TEST_CATEGORY" = "all" ]; then
    PYTEST_CMD="python -m pytest tests/test_security.py -v --tb=short $VERBOSE $COVERAGE"
    echo -e "${GREEN}Running all 27 security tests...${NC}"
else
    PYTEST_CMD="python -m pytest tests/test_security.py::$TEST_CATEGORY -v --tb=short $VERBOSE $COVERAGE"
    echo -e "${GREEN}Running $TEST_CATEGORY tests...${NC}"
fi

# Run tests
echo -e "${BLUE}Command: $PYTEST_CMD${NC}"
echo ""

eval $PYTEST_CMD
TEST_RESULT=$?

# Display results
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  All security tests passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Security tests failed! ✗${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Review failures and fix security issues before deployment.${NC}"
fi

# Coverage report location
if [ -n "$COVERAGE" ]; then
    echo ""
    echo -e "${BLUE}Coverage report generated: htmlcov/index.html${NC}"
fi

exit $TEST_RESULT
