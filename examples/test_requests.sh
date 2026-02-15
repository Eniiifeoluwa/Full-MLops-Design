#!/bin/bash

# Example API requests for the ML inference service

API_URL="${API_URL:-http://localhost:8000}"

echo "======================================"
echo "ML Inference Service - Example Requests"
echo "======================================"
echo ""

# 1. Health check
echo "1. Health Check"
echo "Request: GET $API_URL/health"
curl -s -X GET "$API_URL/health" | jq '.'
echo ""
echo ""

# 2. Readiness check
echo "2. Readiness Check"
echo "Request: GET $API_URL/ready"
curl -s -X GET "$API_URL/ready" | jq '.'
echo ""
echo ""

# 3. Single prediction - Setosa
echo "3. Prediction - Iris Setosa (class 0)"
echo "Request: POST $API_URL/predict"
echo "Body: {"
echo "  \"features\": [5.1, 3.5, 1.4, 0.2],"
echo "  \"request_id\": \"example-001\""
echo "}"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [5.1, 3.5, 1.4, 0.2],
    "request_id": "example-001"
  }' | jq '.'
echo ""
echo ""

# 4. Single prediction - Versicolor
echo "4. Prediction - Iris Versicolor (class 1)"
echo "Request: POST $API_URL/predict"
echo "Body: {"
echo "  \"features\": [6.4, 3.2, 4.5, 1.5],"
echo "  \"request_id\": \"example-002\""
echo "}"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [6.4, 3.2, 4.5, 1.5],
    "request_id": "example-002"
  }' | jq '.'
echo ""
echo ""

# 5. Single prediction - Virginica
echo "5. Prediction - Iris Virginica (class 2)"
echo "Request: POST $API_URL/predict"
echo "Body: {"
echo "  \"features\": [6.3, 3.3, 6.0, 2.5],"
echo "  \"request_id\": \"example-003\""
echo "}"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [6.3, 3.3, 6.0, 2.5],
    "request_id": "example-003"
  }' | jq '.'
echo ""
echo ""

# 6. Invalid request - wrong feature count
echo "6. Invalid Request - Wrong Feature Count (should fail)"
echo "Request: POST $API_URL/predict"
echo "Body: {"
echo "  \"features\": [5.1, 3.5]"
echo "}"
curl -s -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "features": [5.1, 3.5]
  }' | jq '.'
echo ""
echo ""

# 7. Get metrics
echo "7. Prometheus Metrics"
echo "Request: GET $API_URL/metrics"
curl -s -X GET "$API_URL/metrics" | head -n 30
echo "... (truncated)"
echo ""
echo ""

echo "======================================"
echo "All examples completed!"
echo "======================================"