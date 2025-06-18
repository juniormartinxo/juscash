import { afterAll, beforeAll, beforeEach, describe, expect, it } from '@jest/globals'
import request from 'supertest'
import app from '../../app.js'
import { PrismaClient } from '../../generated/prisma/index.js'

describe('Publications Integration Tests', () => {
  let prisma: PrismaClient
  let authToken: string

  beforeAll(async () => {
    prisma = new PrismaClient()

    const userData = {
      name: 'Test User',
      email: 'test.publications@exemplo.com',
      password: 'TestPass@123',
    }

    const authResponse = await request(app)
      .post('/api/auth/register')
      .send(userData)

    authToken = authResponse.body.data.tokens.accessToken
  })

  afterAll(async () => {
    await prisma.user.deleteMany({
      where: { email: 'test.publications@exemplo.com' },
    })
    await prisma.$disconnect()
  })

  beforeEach(async () => {
    await prisma.publication.deleteMany()
  })

  describe('GET /api/publications', () => {
    it('should return empty list when no publications exist', async () => {
      const response = await request(app)
        .get('/api/publications')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.success).toBe(true)
      expect(response.body.data.publications).toEqual([])
      expect(response.body.data.pagination.count).toBe(0)
    })

    it('should return publications with pagination', async () => {
      const publicationsData = Array.from({ length: 35 }, (_, i) => ({
        process_number: `${i + 1}234567-89.2024.8.26.0100`,
        availability_date: new Date('2024-03-17'),
        authors: [`Author ${i + 1}`],
        content: `Content for publication ${i + 1}`,
      }))

      await prisma.publication.createMany({
        data: publicationsData,
      })

      const firstPageResponse = await request(app)
        .get('/api/publications?page=1&limit=10')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(firstPageResponse.body.data.publications).toHaveLength(10)
      expect(firstPageResponse.body.data.pagination.current).toBe(1)
      expect(firstPageResponse.body.data.pagination.total).toBe(4) // 35 / 10 = 4 pages

      const secondPageResponse = await request(app)
        .get('/api/publications?page=2&limit=10')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(secondPageResponse.body.data.publications).toHaveLength(10)
      expect(secondPageResponse.body.data.pagination.current).toBe(2)
    })

    it('should filter publications by status', async () => {
      await prisma.publication.createMany({
        data: [
          {
            process_number: '1234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['Author 1'],
            content: 'Content 1',
            status: 'NOVA',
          },
          {
            process_number: '2234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['Author 2'],
            content: 'Content 2',
            status: 'LIDA',
          },
        ],
      })

      const response = await request(app)
        .get('/api/publications?status=NOVA')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.data.publications).toHaveLength(1)
      expect(response.body.data.publications[0].status).toBe('NOVA')
    })

    it('should filter publications by date range', async () => {
      await prisma.publication.createMany({
        data: [
          {
            process_number: '1234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-15'),
            authors: ['Author 1'],
            content: 'Content 1',
          },
          {
            process_number: '2234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-20'),
            authors: ['Author 2'],
            content: 'Content 2',
          },
        ],
      })

      const response = await request(app)
        .get('/api/publications?startDate=2024-03-16T00:00:00Z&endDate=2024-03-21T00:00:00Z')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.data.publications).toHaveLength(1)
      expect(response.body.data.publications[0].process_number).toBe('2234567-89.2024.8.26.0100')
    })

    it('should search publications by content', async () => {
      await prisma.publication.createMany({
        data: [
          {
            process_number: '1234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['João Silva'],
            content: 'This is about pension benefits',
          },
          {
            process_number: '2234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['Maria Santos'],
            content: 'This is about disability insurance',
          },
        ],
      })

      const response = await request(app)
        .get('/api/publications?search=pension')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.data.publications).toHaveLength(1)
      expect(response.body.data.publications[0].content).toContain('pension')
    })
  })

  describe('GET /api/publications/:id', () => {
    it('should return specific publication', async () => {
      const publication = await prisma.publication.create({
        data: {
          process_number: '1234567-89.2024.8.26.0100',
          availability_date: new Date('2024-03-17'),
          authors: ['João Silva'],
          content: 'Test content',
          gross_value: 150000,
          net_value: 135000,
        },
      })

      const response = await request(app)
        .get(`/api/publications/${publication.id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.success).toBe(true)
      expect(response.body.data.publication.id).toBe(publication.id)
      expect(response.body.data.publication.process_number).toBe('1234567-89.2024.8.26.0100')
      expect(response.body.data.publication.gross_value).toBe(150000)
    })

    it('should return 404 for non-existent publication', async () => {
      const fakeId = '12345678-1234-1234-1234-123456789012'

      const response = await request(app)
        .get(`/api/publications/${fakeId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404)

      expect(response.body.success).toBe(false)
    })
  })

  describe('PUT /api/publications/:id/status', () => {
    it('should update publication status', async () => {
      const publication = await prisma.publication.create({
        data: {
          process_number: '1234567-89.2024.8.26.0100',
          availability_date: new Date('2024-03-17'),
          authors: ['João Silva'],
          content: 'Test content',
          status: 'NOVA',
        },
      })

      const response = await request(app)
        .put(`/api/publications/${publication.id}/status`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ status: 'LIDA' })
        .expect(200)

      expect(response.body.success).toBe(true)
      expect(response.body.data.status).toBe('LIDA')

      // Verify in database
      const updatedPublication = await prisma.publication.findUnique({
        where: { id: publication.id },
      })
      expect(updatedPublication?.status).toBe('LIDA')
    })

    it('should reject invalid status transitions', async () => {
      const publication = await prisma.publication.create({
        data: {
          process_number: '1234567-89.2024.8.26.0100',
          availability_date: new Date('2024-03-17'),
          authors: ['João Silva'],
          content: 'Test content',
          status: 'NOVA',
        },
      })

      const response = await request(app)
        .put(`/api/publications/${publication.id}/status`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ status: 'CONCLUIDA' })
        .expect(400)

      expect(response.body.success).toBe(false)
      expect(response.body.error).toContain('Invalid status transition')
    })
  })

  describe('GET /api/publications/search', () => {
    it('should search publications by query', async () => {
      await prisma.publication.createMany({
        data: [
          {
            process_number: '1234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['João Silva Santos'],
            content: 'Processo sobre aposentadoria',
          },
          {
            process_number: '2234567-89.2024.8.26.0100',
            availability_date: new Date('2024-03-17'),
            authors: ['Maria Oliveira'],
            content: 'Processo sobre auxílio doença',
          },
        ],
      })

      const response = await request(app)
        .get('/api/publications/search?q=João')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.success).toBe(true)
      expect(response.body.data.publications).toHaveLength(1)
      expect(response.body.data.publications[0].authors).toContain('João Silva Santos')
    })

    it('should require minimum query length', async () => {
      const response = await request(app)
        .get('/api/publications/search?q=a')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(400)

      expect(response.body.success).toBe(false)
    })
  })

  describe('Authentication', () => {
    it('should reject requests without token', async () => {
      const response = await request(app)
        .get('/api/publications')
        .expect(401)

      expect(response.body.success).toBe(false)
      expect(response.body.error).toContain('Authorization token required')
    })

    it('should reject requests with invalid token', async () => {
      const response = await request(app)
        .get('/api/publications')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401)

      expect(response.body.success).toBe(false)
      expect(response.body.error).toContain('Invalid or expired token')
    })
  })
})
