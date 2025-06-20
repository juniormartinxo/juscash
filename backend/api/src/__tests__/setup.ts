import { PrismaClient } from '../generated/prisma/index.js'

declare global {
  var testPrisma: PrismaClient
}

let prisma: PrismaClient | undefined

// Only setup database for integration tests
const isIntegrationTest = process.argv.some(arg =>
  arg.includes('integration') ||
  arg.includes('e2e') ||
  process.env.TEST_TYPE === 'integration'
)

if (isIntegrationTest) {
  beforeAll(async () => {
    // Integration tests are currently skipped - they require database setup
    console.log('Integration test setup: database tests skipped (use npm run test:unit for unit tests)')
  })

  afterAll(async () => {
    // No cleanup needed for skipped tests
  })

  beforeEach(async () => {
    // No database operations for skipped tests
  })
}

// For unit tests, we don't need database connection
// Unit tests should use mocked repositories and services
