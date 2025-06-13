import { Router } from 'express'
import { MetricsController } from '@/infrastructure/web/controllers/metrics.controller'
import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'

export function createMetricsRoutes(
  metricsController: MetricsController,
  authMiddleware: AuthMiddleware
): Router {
  const router = Router()

  // Admin-only routes (in a real app, you'd have role-based auth)
  router.use(authMiddleware.authenticate)

  router.get('/', metricsController.getMetrics)
  router.get('/system', metricsController.getSystemMetrics)
  router.get('/endpoints', metricsController.getEndpointMetrics)

  return router
}
