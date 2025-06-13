import { PrismaClient } from '../generated/prisma/index.js'

declare global {
  var testPrisma: PrismaClient
}

// Global test setup
let prisma: PrismaClient = new PrismaClient()

beforeAll(async () => {
  // Configurar banco de teste
  prisma = new PrismaClient({
    datasources: {
      db: {
        url: process.env.DATABASE_URL || 'postgresql://test_user:test_password@localhost:5432/test_db',
      },
    },
  })

  // Executar migrações
  await prisma.$executeRaw`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`
})

afterAll(async () => {
  // Limpar banco e fechar conexão
  await prisma.$disconnect()
})

beforeEach(async () => {
  // Limpar tabelas antes de cada teste
  await prisma.publicationLog.deleteMany()
  await prisma.publication.deleteMany()
  await prisma.userRefreshToken.deleteMany()
  await prisma.userSession.deleteMany()
  await prisma.authLog.deleteMany()
  await prisma.user.deleteMany()
})

// Disponibilizar prisma globalmente para os testes
global.testPrisma = prisma