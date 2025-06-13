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

  return router
}