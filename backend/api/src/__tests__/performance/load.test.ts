import { describe, it, expect } from '@jest/globals'
import request from 'supertest'
import app from '../../app'

describe('Performance Tests', () => {
  it('should handle concurrent requests', async () => {
    const concurrentRequests = 50
    const maxResponseTime = 5000 // 5 seconds

    const promises = Array.from({ length: concurrentRequests }, () =>
      request(app).get('/health').expect(200)
    )

    const startTime = Date.now()
    const responses = await Promise.all(promises)
    const endTime = Date.now()

    const totalTime = endTime - startTime
    const averageTime = totalTime / concurrentRequests

    expect(responses).toHaveLength(concurrentRequests)
    expect(totalTime).toBeLessThan(maxResponseTime)
    expect(averageTime).toBeLessThan(100) // Each request should be under 100ms on average

    console.log(`Performance Test Results:
      - Concurrent requests: ${concurrentRequests}
      - Total time: ${totalTime}ms
      - Average time per request: ${averageTime.toFixed(2)}ms
    `)
  })

  it('should handle rate limiting gracefully', async () => {
    // This test would require adjusting rate limits for testing
    // or using a separate test configuration
    const rateLimitRequests = 150 // Assuming 100 requests per 15 minutes limit

    const promises = Array.from({ length: rateLimitRequests }, () =>
      request(app).get('/health')
    )

    const responses = await Promise.allSettled(promises)

    const successful = responses.filter(r => r.status === 'fulfilled' && r.value.status === 200)
    const rateLimited = responses.filter(r => r.status === 'fulfilled' && r.value.status === 429)

    expect(successful.length).toBeGreaterThan(0)
    expect(rateLimited.length).toBeGreaterThan(0)

    console.log(`Rate Limiting Test Results:
      - Successful requests: ${successful.length}
      - Rate limited requests: ${rateLimited.length}
    `)
  })
})