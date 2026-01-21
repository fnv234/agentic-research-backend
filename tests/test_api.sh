#!/bin/bash

# API Testing Script
# Test all endpoints of the Agentic Research Backend

API_URL="${1:-http://localhost:5000}"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Agentic Research Backend API${NC}"
echo -e "${BLUE}API URL: $API_URL${NC}"
echo -e "${BLUE}========================================${NC}\n"

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "${BLUE}Test:${NC} $description"
    echo -e "Request: ${method} ${endpoint}"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    echo -e "Response Code: $http_code"
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi

    echo -e "Response:\n$body\n"
}

test_endpoint "GET" "/health" "" "Health Check"

test_endpoint "GET" "/api/info" "" "Get Service Info"

test_endpoint "GET" "/api/bots" "" "Get Agents/Bots"

test_endpoint "GET" "/api/runs" "" "Get Bot Simulation Runs"

test_endpoint "GET" "/api/runs/real" "" "Get Real Data from CSV"

run_data='{"run": {"accumulated_profit": 1500000, "compromised_systems": 8, "systems_availability": 0.94}}'
test_endpoint "POST" "/api/evaluate" "$run_data" "Evaluate a Run with Agents"

test_endpoint "GET" "/api/runs/compare" "" "Compare Real vs Bot Data"

test_endpoint "GET" "/api/statistics" "" "Get Statistical Summary"

test_endpoint "GET" "/api/invalid" "" "Test 404 Error Handling"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}API Testing Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo "Summary:"
echo "- All endpoints tested"
echo "- Check responses above for any errors"
echo "- 2xx status codes indicate success"
echo "- 4xx/5xx status codes indicate errors"
