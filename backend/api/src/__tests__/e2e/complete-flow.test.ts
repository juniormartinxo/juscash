import { afterAll, beforeAll, describe, expect, it } from '@jest/globals'
import request from 'supertest'
import app from '../../app.js'
import { PrismaClient } from '../../generated/prisma/index.js'

describe('Complete User Flow E2E', () => {
  let prisma: PrismaClient
  let userTokens: { accessToken: string; refreshToken: string }

  beforeAll(async () => {
    prisma = new PrismaClient()
  })

  afterAll(async () => {
    await prisma.$disconnect()
  })

  it('should complete full user journey', async () => {
    const registerResponse = await request(app)
      .post('/api/auth/register')
      .send({
        name: 'E2E Test User',
        email: 'e2e.user@exemplo.com',
        password: 'E2ETest@123',
      })
      .expect(201)

    expect(registerResponse.body.success).toBe(true)
    expect(registerResponse.body.data.tokens).toBeDefined()
    userTokens = registerResponse.body.data.tokens

    await prisma.publication.create({
      data: {
        process_number: '1234567-89.2024.8.26.0100',
        availability_date: new Date('2024-03-17'),
        authors: ['João Silva'],
        content: 'Test publication for E2E',
        status: 'NOVA',
        gross_value: 150000,
        net_value: 135000,
      },
    })

    const listResponse = await request(app)
      .get('/api/publications')
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(200)

    expect(listResponse.body.data.publications).toHaveLength(1)
    const publicationId = listResponse.body.data.publications[0].id

    const detailResponse = await request(app)
      .get(`/api/publications/${publicationId}`)
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(200)

    expect(detailResponse.body.data.publication.process_number).toBe('1234567-89.2024.8.26.0100')

    const updateResponse = await request(app)
      .put(`/api/publications/${publicationId}/status`)
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .send({ status: 'LIDA' })
      .expect(200)

    expect(updateResponse.body.data.status).toBe('LIDA')

    const searchResponse = await request(app)
      .get('/api/publications/search?q=João')
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(200)

    expect(searchResponse.body.data.publications).toHaveLength(1)

    const filterResponse = await request(app)
      .get('/api/publications?status=LIDA')
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(200)

    expect(filterResponse.body.data.publications).toHaveLength(1)
    expect(filterResponse.body.data.publications[0].status).toBe('LIDA')

    const logoutResponse = await request(app)
      .post('/api/auth/logout')
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(200)

    expect(logoutResponse.body.success).toBe(true)

    await request(app)
      .get('/api/publications')
      .set('Authorization', `Bearer ${userTokens.accessToken}`)
      .expect(401)

    await prisma.publication.deleteMany()
    await prisma.user.deleteMany({
      where: { email: 'e2e.user@exemplo.com' },
    })
  })
})
