import {
  getPublicationsQuerySchema,
  updatePublicationStatusSchema,
  createPublicationSchema
} from '@/shared/validation/schemas'
import { PublicationController } from '@/infrastructure/web/controllers/publication.controller'
import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'
import { z } from 'zod'
import { Router } from 'express'
import { ValidationMiddleware } from '@/infrastructure/web/middleware/validation.middleware'

const uuidSchema = z.object({
  id: z.string().uuid('ID inválido'),
})

const searchQuerySchema = z.object({
  q: z.string().min(2, 'Query must be at least 2 characters'),
})

export function createPublicationRoutes(
  publicationController: PublicationController,
  authMiddleware: AuthMiddleware
): Router {
  const router = Router()

  // Aplicar autenticação a todas as rotas
  router.use(authMiddleware.authenticate)

  router.post('/',
    ValidationMiddleware.validateBody(createPublicationSchema),
    publicationController.createPublication
  )

  router.get('/',
    ValidationMiddleware.validateQuery(getPublicationsQuerySchema),
    publicationController.getPublications
  )

  router.get('/search',
    ValidationMiddleware.validateQuery(searchQuerySchema),
    publicationController.search
  )

  router.get('/:id',
    ValidationMiddleware.validateParams(uuidSchema),
    publicationController.getPublicationById
  )

  router.put('/:id/status',
    ValidationMiddleware.validateParams(uuidSchema),
    ValidationMiddleware.validateBody(updatePublicationStatusSchema),
    publicationController.updateStatus
  )

  return router
}
