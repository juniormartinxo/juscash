import { check, sleep } from 'k6'
import http from 'k6/http'
import { Rate } from 'k6/metrics'


export const errorRate = new Rate('errors')

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Ramp up to 200 users
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% das requisições devem ser < 500ms
    errors: ['rate<0.1'], // Taxa de erro < 10%
  },
}

const BASE_URL = __ENV.API_URL || 'http://localhost:3001'

export function setup() {
  const registerResponse = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify({
      name: 'Load Test User',
      email: `loadtest${Date.now()}@exemplo.com`,
      password: 'LoadTest@123',
    }),
    {
      headers: { 'Content-Type': 'application/json' },
    },
  )

  if (registerResponse.status === 201) {
    const userData = registerResponse.json()
    return { token: userData.data.tokens.accessToken }
  }

  return {}
}

export default function (data) {
  const healthResponse = http.get(`${BASE_URL}/health`)
  check(healthResponse, {
    'health check status is 200': r => r.status === 200,
  }) || errorRate.add(1)

  sleep(1)

  if (data.token) {
    const headers = {
      Authorization: `Bearer ${data.token}`,
      'Content-Type': 'application/json',
    }

    const publicationsResponse = http.get(`${BASE_URL}/api/publications?page=1&limit=10`, {
      headers,
    })

    check(publicationsResponse, {
      'publications status is 200': r => r.status === 200,
      'publications response time < 500ms': r => r.timings.duration < 500,
    }) || errorRate.add(1)
  }

  sleep(1)
}

export function teardown(data) {
  console.log('Load test completed')
}
