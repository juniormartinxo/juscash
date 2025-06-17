import { Router } from 'express'
import { createPublicationSchema, updatePublicationStatusSchema } from '@/shared/validation/schemas'
import { PublicationController } from '@/infrastructure/web/controllers/publication.controller'
import { ApiKeyMiddleware } from '@/infrastructure/web/middleware/api-key.middleware'
import { ValidationMiddleware } from '@/infrastructure/web/middleware/validation.middleware'
import { RateLimitMiddleware } from '@/infrastructure/web/middleware/rate-limit.middleware'

/**
 * Cria as rotas específicas para o scraper
 * Estas rotas usam autenticação via API Key em vez de JWT
 */
export function createScraperRoutes(
  publicationController: PublicationController
): Router {
  const router = Router()

  // Rate limiting específico para scraper (mais permissivo que usuários normais)
  const scraperRateLimit = new RateLimitMiddleware(
    15 * 60 * 1000, // 15 minutos
    1000 // 1000 requests por 15 minutos (mais permissivo para scraper)
  )

  // Aplicar rate limiting específico para scraper
  router.use(scraperRateLimit.middleware)

  // Aplicar validação de API Key a todas as rotas do scraper
  router.use(ApiKeyMiddleware.validateScraperApiKey)

  /**
   * POST /api/scraper/publications
   * Endpoint específico para o scraper inserir publicações
   *
   * Headers obrigatórios:
   * - Content-Type: application/json
   * - X-API-Key: <SCRAPER_API_KEY>
   *
   * Body: Mesmo formato do endpoint normal de publicações
   */
  router.post('/publications',
    ValidationMiddleware.validateBody(createPublicationSchema),
    publicationController.createPublicationFromScraper
  )

  router.put('/publications/:id/status',
    ValidationMiddleware.validateBody(updatePublicationStatusSchema),
    publicationController.updateStatus
  )

  return router
}
