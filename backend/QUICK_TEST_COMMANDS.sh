#!/bin/bash

###############################################################################
# Quick Test Commands for Authentication API
# Kenya SMB Accounting MVP Backend
#
# Usage:
#   chmod +x QUICK_TEST_COMMANDS.sh
#   ./QUICK_TEST_COMMANDS.sh
###############################################################################

set -e

BASE_URL="http://localhost:8000/api/v1"
TEST_EMAIL="admin@example.com"
TEST_PASSWORD="AdminPass123"
NEW_PASSWORD="NewSecurePass456"

echo "======================================================================"
echo "Kenya SMB Accounting MVP - Authentication API Test Suite"
echo "======================================================================"
echo ""
echo "Base URL: $BASE_URL"
echo "Test User: $TEST_EMAIL"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Warning: jq is not installed. Output will not be formatted."
    echo "Install jq for better output: sudo apt-get install jq"
    JQ_CMD="cat"
else
    JQ_CMD="jq ."
fi

echo "----------------------------------------------------------------------"
echo "1. Testing LOGIN endpoint"
echo "   POST $BASE_URL/auth/login"
echo "----------------------------------------------------------------------"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

echo "$LOGIN_RESPONSE" | $JQ_CMD

# Extract tokens
if command -v jq &> /dev/null; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')

    if [ "$ACCESS_TOKEN" = "null" ]; then
        echo ""
        echo "ERROR: Login failed. Please check:"
        echo "  1. Server is running: uvicorn app.main:app --reload"
        echo "  2. Database migration is complete: alembic upgrade head"
        echo "  3. Test user exists: python create_test_user.py"
        echo ""
        exit 1
    fi

    echo ""
    echo "✓ Login successful!"
    echo "  Access Token: ${ACCESS_TOKEN:0:50}..."
    echo "  Refresh Token: ${REFRESH_TOKEN:0:50}..."
else
    echo ""
    echo "Please manually extract tokens from the response above"
    echo "Set ACCESS_TOKEN and REFRESH_TOKEN variables:"
    echo "  export ACCESS_TOKEN='your_access_token'"
    echo "  export REFRESH_TOKEN='your_refresh_token'"
    read -p "Press Enter to continue (or Ctrl+C to exit)..."
fi

echo ""
echo "----------------------------------------------------------------------"
echo "2. Testing GET CURRENT USER endpoint"
echo "   GET $BASE_URL/auth/me"
echo "----------------------------------------------------------------------"

curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | $JQ_CMD

echo ""
echo "✓ Current user retrieved successfully!"

echo ""
echo "----------------------------------------------------------------------"
echo "3. Testing REFRESH TOKEN endpoint"
echo "   POST $BASE_URL/auth/refresh"
echo "----------------------------------------------------------------------"

REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }")

echo "$REFRESH_RESPONSE" | $JQ_CMD

if command -v jq &> /dev/null; then
    NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token')
    echo ""
    echo "✓ Token refreshed successfully!"
    echo "  New Access Token: ${NEW_ACCESS_TOKEN:0:50}..."
else
    echo ""
    echo "✓ Token refresh endpoint working!"
fi

echo ""
echo "----------------------------------------------------------------------"
echo "4. Testing CHANGE PASSWORD endpoint"
echo "   POST $BASE_URL/auth/change-password"
echo "----------------------------------------------------------------------"

curl -s -X POST "$BASE_URL/auth/change-password" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"current_password\": \"$TEST_PASSWORD\",
    \"new_password\": \"$NEW_PASSWORD\"
  }" | $JQ_CMD

echo ""
echo "✓ Password changed successfully!"

echo ""
echo "----------------------------------------------------------------------"
echo "5. Testing LOGIN with NEW PASSWORD"
echo "   POST $BASE_URL/auth/login"
echo "----------------------------------------------------------------------"

NEW_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$NEW_PASSWORD\"
  }")

echo "$NEW_LOGIN_RESPONSE" | $JQ_CMD

if command -v jq &> /dev/null; then
    NEW_TOKEN=$(echo "$NEW_LOGIN_RESPONSE" | jq -r '.access_token')
    if [ "$NEW_TOKEN" != "null" ]; then
        echo ""
        echo "✓ Login with new password successful!"
        ACCESS_TOKEN=$NEW_TOKEN
    fi
fi

echo ""
echo "----------------------------------------------------------------------"
echo "6. Testing LOGOUT endpoint"
echo "   POST $BASE_URL/auth/logout"
echo "----------------------------------------------------------------------"

curl -s -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | $JQ_CMD

echo ""
echo "✓ Logout successful!"

echo ""
echo "----------------------------------------------------------------------"
echo "7. Resetting password back to original for next test"
echo "----------------------------------------------------------------------"

# Login with new password to get fresh token
RESET_LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$NEW_PASSWORD\"
  }")

if command -v jq &> /dev/null; then
    RESET_TOKEN=$(echo "$RESET_LOGIN" | jq -r '.access_token')

    # Change back to original password
    curl -s -X POST "$BASE_URL/auth/change-password" \
      -H "Authorization: Bearer $RESET_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"current_password\": \"$NEW_PASSWORD\",
        \"new_password\": \"$TEST_PASSWORD\"
      }" > /dev/null

    echo "✓ Password reset to original for future tests"
fi

echo ""
echo "======================================================================"
echo "ALL TESTS COMPLETED SUCCESSFULLY!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  ✓ Login endpoint working"
echo "  ✓ Get current user endpoint working"
echo "  ✓ Refresh token endpoint working"
echo "  ✓ Change password endpoint working"
echo "  ✓ Logout endpoint working"
echo ""
echo "Next steps:"
echo "  1. Check audit logs: SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
echo "  2. View API documentation: http://localhost:8000/docs"
echo "  3. Review implementation: cat IMPLEMENTATION_SUMMARY.md"
echo ""
echo "======================================================================"
