import { PrismaClient } from '../generated/prisma/index.js'

declare global {
  var testPrisma: PrismaClient
}


let prisma: PrismaClient = new PrismaClient()

beforeAll(async () => {
  prisma = new PrismaClient({
    datasources: {
      db: {
        url: process.env.DATABASE_URL || 'postgresql://test_user:test_password@localhost:5432/test_db',
      },
    },
  })


  await prisma.$executeRaw`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`
})

afterAll(async () => {
  await prisma.$disconnect()
})

beforeEach(async () => {
  await prisma.publicationLog.deleteMany()
  await prisma.publication.deleteMany()
  await prisma.userRefreshToken.deleteMany()
  await prisma.userSession.deleteMany()
  await prisma.authLog.deleteMany()
  await prisma.user.deleteMany()
})


global.testPrisma = prisma
