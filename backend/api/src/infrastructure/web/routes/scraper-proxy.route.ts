import { Router, Request, Response } from 'express'
import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'
import { RateLimitMiddleware } from '@/infrastructure/web/middleware/rate-limit.middleware'
import { ApiResponseBuilder } from '@/shared/utils/api-response'
import { asyncHandler } from '@/shared/utils/async-handler'

/**
 * Proxy seguro para a API do Scraper
 * Frontend → API Principal (JWT) → API Scraper (API Key)
 */
export function createScraperProxyRoutes(authMiddleware: AuthMiddleware): Router {
  const router = Router()

  // Rate limiting específico para operações do scraper
  const scraperRateLimit = new RateLimitMiddleware(
    5 * 60 * 1000, // 5 minutos
    10 // 10 requests por 5 minutos (mais restritivo)
  )

  router.use(scraperRateLimit.middleware)
  router.use(authMiddleware.authenticate) // Requer autenticação JWT

  const SCRAPER_API_URL = process.env.SCRAPER_API_URL || 'http://localhost:5000'
  const SCRAPER_API_KEY = process.env.SCRAPER_API_KEY

  if (!SCRAPER_API_KEY) {
    console.warn('⚠️ SCRAPER_API_KEY não configurada para proxy')
  }

  /**
   * GET /api/scraper-proxy/status
   * Verifica status do scraper via proxy seguro
   */
  router.get('/status', asyncHandler(async (req: Request, res: Response) => {
    try {
      const response = await fetch(`${SCRAPER_API_URL}/status`, {
        headers: {
          'X-API-Key': SCRAPER_API_KEY || ''
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      res.json(ApiResponseBuilder.success(data))
    } catch (error: any) {
      console.error('Erro ao consultar status do scraper:', error.message)

      if (error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch')) {
        res.status(503).json(ApiResponseBuilder.error('Serviço do scraper indisponível'))
      } else if (error.message?.includes('401') || error.message?.includes('403')) {
        res.status(502).json(ApiResponseBuilder.error('Erro de autenticação com o scraper'))
      } else {
        res.status(502).json(ApiResponseBuilder.error('Erro ao comunicar com o scraper'))
      }
    }
  }))

  /**
   * POST /api/scraper-proxy/run
   * Inicia scraping via proxy seguro
   */
  router.post('/run', asyncHandler(async (req: Request, res: Response) => {
    try {
      const { start_date, end_date, headless = true } = req.body

      // Validação básica
      if (!start_date || !end_date) {
        return res.status(400).json(
          ApiResponseBuilder.error('start_date e end_date são obrigatórios')
        )
      }

      const response = await fetch(`${SCRAPER_API_URL}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': SCRAPER_API_KEY || ''
        },
        body: JSON.stringify({
          start_date,
          end_date,
          headless
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' })) as { detail?: string }
        throw new Error(`HTTP ${response.status}: ${errorData.detail || response.statusText}`)
      }

      const data = await response.json()
      res.json(ApiResponseBuilder.success(data))
    } catch (error: any) {
      console.error('Erro ao iniciar scraping:', error.message)

      if (error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch')) {
        res.status(503).json(ApiResponseBuilder.error('Serviço do scraper indisponível'))
      } else if (error.message?.includes('401') || error.message?.includes('403')) {
        res.status(502).json(ApiResponseBuilder.error('Erro de autenticação com o scraper'))
      } else if (error.message?.includes('400')) {
        res.status(400).json(ApiResponseBuilder.error(error.message))
      } else {
        res.status(502).json(ApiResponseBuilder.error('Erro ao comunicar com o scraper'))
      }
    }
  }))

  /**
   * POST /api/scraper-proxy/force-stop
   * Força parada do scraping via proxy seguro
   */
  router.post('/force-stop', asyncHandler(async (req: Request, res: Response) => {
    try {
      const response = await fetch(`${SCRAPER_API_URL}/force-stop-scraping`, {
        method: 'POST',
        headers: {
          'X-API-Key': SCRAPER_API_KEY || ''
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      res.json(ApiResponseBuilder.success(data))
    } catch (error: any) {
      console.error('Erro ao forçar parada do scraping:', error.message)

      if (error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch')) {
        res.status(503).json(ApiResponseBuilder.error('Serviço do scraper indisponível'))
      } else if (error.message?.includes('401') || error.message?.includes('403')) {
        res.status(502).json(ApiResponseBuilder.error('Erro de autenticação com o scraper'))
      } else {
        res.status(502).json(ApiResponseBuilder.error('Erro ao comunicar com o scraper'))
      }
    }
  }))

  /**
   * POST /api/scraper-proxy/today
   * Executa scraping do dia atual via proxy seguro
   */
  router.post('/today', asyncHandler(async (req, res) => {
    try {
      const { headless = true } = req.body

      const response = await fetch(`${SCRAPER_API_URL}/scraping/today`, {
        method: 'POST',
        headers: {
          'X-API-Key': SCRAPER_API_KEY || ''
        },
        body: JSON.stringify({ headless })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      res.json(ApiResponseBuilder.success(data))
    } catch (error: any) {
      console.error('Erro ao iniciar scraping de hoje:', error.message)

      if (error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch')) {
        res.status(503).json(ApiResponseBuilder.error('Serviço do scraper indisponível'))
      } else if (error.message?.includes('401') || error.message?.includes('403')) {
        res.status(502).json(ApiResponseBuilder.error('Erro de autenticação com o scraper'))
      } else {
        res.status(502).json(ApiResponseBuilder.error('Erro ao comunicar com o scraper'))
      }
    }
  }))

  return router
}
