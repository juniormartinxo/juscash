import { afterAll, beforeAll, describe, expect, it } from '@jest/globals'
import request from 'supertest'
import app from '../../app.js'
import { PrismaClient } from '../../generated/prisma/index.js'

describe('Auth Integration Tests', () => {
  let prisma: PrismaClient

  beforeAll(async () => {
    prisma = new PrismaClient()
  })

  afterAll(async () => {
    await prisma.$disconnect()
  })

  describe('POST /api/auth/register', () => {
    it('should register a new user', async () => {
      const userData = {
        name: 'João Silva',
        email: 'joao.test@exemplo.com',
        password: 'MinhaSenh@123',
      }

      const response = await request(app)
        .post('/api/auth/register')
        .send(userData)
        .expect(201)

      expect(response.body).toHaveProperty('success', true)
      expect(response.body.data).toHaveProperty('user')
      expect(response.body.data).toHaveProperty('tokens')
      expect(response.body.data.user.email).toBe(userData.email)
      expect(response.body.data.user.name).toBe(userData.name)
    })

    it('should return 400 for invalid email', async () => {
      const userData = {
        name: 'João Silva',
        email: 'invalid-email',
        password: 'MinhaSenh@123',
      }

      const response = await request(app)
        .post('/api/auth/register')
        .send(userData)
        .expect(400)

      expect(response.body).toHaveProperty('success', false)
      expect(response.body).toHaveProperty('error')
    })

    it('should return 400 for weak password', async () => {
      const userData = {
        name: 'João Silva',
        email: 'joao2@exemplo.com',
        password: 'weak',
      }

      const response = await request(app)
        .post('/api/auth/register')
        .send(userData)
        .expect(400)

      expect(response.body).toHaveProperty('success', false)
    })
  })

  describe('POST /api/auth/login', () => {
    beforeAll(async () => {
      await request(app)
        .post('/api/auth/register')
        .send({
          name: 'Login Test User',
          email: 'login.test@exemplo.com',
          password: 'MinhaSenh@123',
        })
    })

    it('should login with valid credentials', async () => {
      const credentials = {
        email: 'login.test@exemplo.com',
        password: 'MinhaSenh@123',
      }

      const response = await request(app)
        .post('/api/auth/login')
        .send(credentials)
        .expect(200)

      expect(response.body).toHaveProperty('success', true)
      expect(response.body.data).toHaveProperty('user')
      expect(response.body.data).toHaveProperty('tokens')
    })

    it('should return 401 for invalid credentials', async () => {
      const credentials = {
        email: 'login.test@exemplo.com',
        password: 'wrong-password',
      }

      const response = await request(app)
        .post('/api/auth/login')
        .send(credentials)
        .expect(401)

      expect(response.body).toHaveProperty('success', false)
    })
  })
})
