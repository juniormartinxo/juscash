import { Router } from 'express'
import { z } from 'zod'
import { loginSchema, registerSchema } from '@/shared/validation/schemas'
import { AuthController } from '@/infrastructure/web/controllers/auth.controller'
import { ValidationMiddleware } from '@/infrastructure/web/middleware/validation.middleware'

const refreshTokenSchema = z.object({
  refreshToken: z.string().min(1, 'Refresh token is required'),
})

export function createAuthRoutes(authController: AuthController): Router {
  const router = Router()

  router.post('/register',
    ValidationMiddleware.validateBody(registerSchema),
    authController.register
  )

  router.post('/login',
    ValidationMiddleware.validateBody(loginSchema),
    authController.login
  )

  router.post('/refresh',
    ValidationMiddleware.validateBody(refreshTokenSchema),
    authController.refresh
  )

  router.post('/logout',
    authController.logout
  )

  router.post('/test-controller', async (req, res) => {
    try {
      res.json({ success: true, message: 'Controller test', data: 'OK' })
    } catch (error) {
      res.status(500).json({ success: false, error: error instanceof Error ? error.message : 'Unknown error' })
    }
  })

  router.post('/test-register', (req, res) => {
    res.json({ success: true, message: 'Auth test working', body: req.body })
  })

  router.post('/test-usecase', async (req, res) => {
    try {
      const { name, email, password } = req.body

      // Testar o use case diretamente
      const result = await authController['registerUserUseCase'].execute({
        name,
        email,
        password,
      })

      res.status(201).json({
        success: true,
        message: 'UseCase test',
        data: result
      })
    } catch (error) {
      res.status(500).json({ success: false, error: error instanceof Error ? error.message : 'Unknown error' })
    }
  })

  router.post('/test-register-direct', async (req, res) => {
    try {
      const { name, email, password } = req.body

      // Teste simples sem usar o use case ainda
      res.status(201).json({
        success: true,
        message: 'Direct register test',
        data: { name, email, hasPassword: !!password }
      })
    } catch (error) {
      res.status(500).json({ success: false, error: error instanceof Error ? error.message : 'Unknown error' })
    }
  })

  return router
}
