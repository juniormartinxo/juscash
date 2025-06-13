#!/bin/bash

echo "🔥 Starting stress test..."

API_URL="${API_URL:-http://localhost:3001}"
CONCURRENT_USERS="${CONCURRENT_USERS:-50}"
DURATION="${DURATION:-5m}"

# Register test user
echo "👤 Registering test user..."
TEST_EMAIL="stresstest$(date +%s)@exemplo.com"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Stress Test User\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"StressTest@123\"
  }")

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.data.tokens.accessToken')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Failed to get access token"
  exit 1
fi

echo "✅ Got access token: ${ACCESS_TOKEN:0:20}..."

# Run stress test with k6
cat > /tmp/stress-test.js << EOF
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: $((CONCURRENT_USERS / 2)) },
    { duration: '$DURATION', target: $CONCURRENT_USERS },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    errors: ['rate<0.05'],
  },
};

const BASE_URL = '$API_URL';
const ACCESS_TOKEN = '$ACCESS_TOKEN';

export default function() {
  const headers = {
    'Authorization': \`Bearer \${ACCESS_TOKEN}\`,
    'Content-Type': 'application/json',
  };

  // Test health endpoint
  const healthResponse = http.get(\`\${BASE_URL}/health\`);
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(0.5);

  // Test publications endpoint
  const publicationsResponse = http.get(\`\${BASE_URL}/api/publications?page=1&limit=10\`, { headers });
  check(publicationsResponse, {
    'publications status is 200': (r) => r.status === 200,
    'publications response time < 2s': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(1);
}
EOF

# Run the stress test
echo "🚀 Running stress test with $CONCURRENT_USERS concurrent users for $DURATION..."
k6 run /tmp/stress-test.js

# Cleanup
echo "🧹 Cleaning up..."
rm -f /tmp/stress-test.js

echo "✅ Stress test completed!"