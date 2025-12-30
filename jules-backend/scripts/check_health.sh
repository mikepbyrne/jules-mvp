#!/bin/bash
# Health check script for monitoring

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "Checking health of Jules API at $API_URL..."

response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 200 ]; then
    echo "✓ API is healthy"
    echo "$body" | python -m json.tool
    exit 0
else
    echo "✗ API is unhealthy (HTTP $http_code)"
    echo "$body"
    exit 1
fi
