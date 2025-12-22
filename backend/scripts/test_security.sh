#!/bin/bash
#
# Security Hardening Test Script
# Tests rate limiting, IP blocking, and security headers
#
# Usage: ./scripts/test_security.sh [base_url]
# Example: ./scripts/test_security.sh http://localhost:8000
#

set -e

# Configuration
BASE_URL="${1:-http://localhost:8000}"
API_BASE="$BASE_URL/api/v1"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="wrongpassword123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

print_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

# Test 1: Rate Limiting on Login
test_rate_limiting() {
    print_header "Test 1: Rate Limiting"
    print_test "Making 6 rapid login attempts (limit: 5/minute)"

    SUCCESS_COUNT=0
    RATE_LIMITED=false

    for i in {1..6}; do
        echo -n "  Attempt $i: "
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

        HTTP_CODE=$(echo "$RESPONSE" | tail -1)
        BODY=$(echo "$RESPONSE" | head -n -1)

        if [ "$HTTP_CODE" = "429" ]; then
            echo "429 Too Many Requests"
            RATE_LIMITED=true
        elif [ "$HTTP_CODE" = "401" ]; then
            echo "401 Unauthorized (expected for invalid credentials)"
            ((SUCCESS_COUNT++))
        else
            echo "$HTTP_CODE"
        fi

        sleep 1
    done

    if [ "$RATE_LIMITED" = true ] && [ $SUCCESS_COUNT -ge 5 ]; then
        print_pass "Rate limiting working correctly (blocked after 5 attempts)"
    else
        print_fail "Rate limiting not working as expected"
    fi

    print_info "Waiting 60 seconds for rate limit to reset..."
    sleep 60
}

# Test 2: IP Blocking
test_ip_blocking() {
    print_header "Test 2: IP Blocking"
    print_test "Making 11 failed login attempts to trigger IP block (threshold: 10)"

    IP_BLOCKED=false

    for i in {1..11}; do
        echo -n "  Attempt $i: "
        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

        HTTP_CODE=$(echo "$RESPONSE" | tail -1)
        BODY=$(echo "$RESPONSE" | head -n -1)

        if [ "$HTTP_CODE" = "403" ]; then
            echo "403 Forbidden (IP blocked)"
            IP_BLOCKED=true
            break
        elif [ "$HTTP_CODE" = "429" ]; then
            echo "429 Too Many Requests (rate limited first)"
            print_info "Waiting 60 seconds for rate limit to reset..."
            sleep 60
        elif [ "$HTTP_CODE" = "401" ]; then
            echo "401 Unauthorized"
        else
            echo "$HTTP_CODE"
        fi

        sleep 2
    done

    if [ "$IP_BLOCKED" = true ]; then
        print_pass "IP blocking working correctly (blocked after 10 failures)"
        print_info "IP will be automatically unblocked after 60 minutes"
    else
        print_fail "IP blocking not triggered after 11 attempts"
    fi
}

# Test 3: Security Headers
test_security_headers() {
    print_header "Test 3: Security Headers"
    print_test "Checking for required security headers"

    HEADERS=$(curl -s -I "$BASE_URL/")

    HEADERS_PRESENT=0
    HEADERS_MISSING=0

    # Check each header
    check_header() {
        local header=$1
        if echo "$HEADERS" | grep -qi "$header:"; then
            print_pass "$header header present"
            ((HEADERS_PRESENT++))
        else
            print_fail "$header header missing"
            ((HEADERS_MISSING++))
        fi
    }

    check_header "Strict-Transport-Security"
    check_header "X-Content-Type-Options"
    check_header "X-Frame-Options"
    check_header "X-XSS-Protection"
    check_header "Referrer-Policy"
    check_header "Permissions-Policy"
    check_header "Content-Security-Policy"

    # Check that Server header is removed
    if echo "$HEADERS" | grep -qi "server:"; then
        print_fail "Server header present (should be removed)"
        ((HEADERS_MISSING++))
    else
        print_pass "Server header removed (good)"
        ((HEADERS_PRESENT++))
    fi

    echo ""
    print_info "$HEADERS_PRESENT headers correct, $HEADERS_MISSING issues found"
}

# Test 4: Payload Size Validation
test_payload_size() {
    print_header "Test 4: Payload Size Validation"
    print_test "Testing with oversized payload (requires authentication)"

    # This test requires a valid auth token, skip if not provided
    if [ -z "$AUTH_TOKEN" ]; then
        print_info "Skipping (AUTH_TOKEN not set)"
        print_info "To test, set AUTH_TOKEN environment variable:"
        print_info "  export AUTH_TOKEN='your_jwt_token'"
        return
    fi

    print_test "Creating 11MB file to test 10MB limit..."
    dd if=/dev/urandom of=/tmp/test_large.csv bs=1M count=11 2>/dev/null

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_BASE/bank-imports" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -F "file=@/tmp/test_large.csv" \
        -F "source_bank=Test Bank")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)

    rm -f /tmp/test_large.csv

    if [ "$HTTP_CODE" = "413" ]; then
        print_pass "Payload size validation working (413 Payload Too Large)"
    else
        print_fail "Expected 413, got $HTTP_CODE"
    fi
}

# Test 5: Suspicious User Agent
test_suspicious_agent() {
    print_header "Test 5: Suspicious User Agent Detection"
    print_test "Testing with security scanner user agent"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/" \
        -H "User-Agent: sqlmap/1.0")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)

    if [ "$HTTP_CODE" = "403" ]; then
        print_pass "Suspicious user agent blocked (403 Forbidden)"
    else
        print_fail "Expected 403, got $HTTP_CODE"
    fi
}

# Test 6: Health Check (should not be rate limited)
test_health_check() {
    print_header "Test 6: Health Check"
    print_test "Testing root endpoint accessibility"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/")
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    BODY=$(echo "$RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
        print_pass "Health check endpoint accessible"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    else
        print_fail "Health check returned $HTTP_CODE"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║   Kenya SMB Accounting - Security Tests      ║"
    echo "║   Production Security Hardening              ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"

    print_info "Testing API at: $BASE_URL"
    print_info "Started at: $(date)"

    # Check if server is running
    if ! curl -s -f "$BASE_URL/" > /dev/null 2>&1; then
        print_fail "Server at $BASE_URL is not responding"
        print_info "Please start the server and try again"
        exit 1
    fi

    print_pass "Server is running"

    # Run tests
    test_health_check
    test_security_headers
    test_rate_limiting
    test_ip_blocking
    test_payload_size
    test_suspicious_agent

    # Summary
    print_header "Test Summary"
    print_info "All tests completed at: $(date)"
    print_info ""
    print_info "Note: Some tests may have failed if:"
    print_info "  - Server is not running locally"
    print_info "  - Authentication token not provided (AUTH_TOKEN)"
    print_info "  - IP already blocked from previous tests"
    print_info ""
    print_info "To reset IP blocks, restart the server (memory storage)"
    print_info "Or wait 60 minutes for automatic unblock"

    echo ""
}

# Run main function
main "$@"
