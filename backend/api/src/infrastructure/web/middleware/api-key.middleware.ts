import { NextFunction, Request, Response } from 'express'
import { config } from '@/shared/config/environment'
import logger from '@/shared/utils/logger'

interface ApiKeyRequest extends Request {
  apiKeySource?: 'SCRAPER'
}

export class ApiKeyMiddleware {
  /**
   * Middleware para validar API Key do scraper
   * Verifica o header X-API-Key contra a variável de ambiente SCRAPER_API_KEY
   */
  static validateScraperApiKey = (
    req: ApiKeyRequest,
    res: Response,
    next: NextFunction
  ): void => {
    try {
      const apiKey = req.headers['x-api-key'] as string

      // Verificar se o header foi fornecido
      if (!apiKey) {
        logger.warn('API Key validation failed: Missing X-API-Key header', {
          ip: req.ip,
          userAgent: req.get('User-Agent'),
          url: req.url,
          method: req.method
        })

        res.status(400).json({
          success: false,
          error: 'X-API-Key header is required'
        })
        return
      }

      // Verificar se a API Key está configurada no ambiente
      if (!config.scraper.apiKey) {
        logger.error('SCRAPER_API_KEY not configured in environment variables')

        res.status(500).json({
          success: false,
          error: 'Server configuration error'
        })
        return
      }

      // Validar a API Key
      if (apiKey !== config.scraper.apiKey) {
        logger.warn('API Key validation failed: Invalid API Key', {
          ip: req.ip,
          userAgent: req.get('User-Agent'),
          url: req.url,
          method: req.method,
          providedKey: apiKey.substring(0, 8) + '...' // Log apenas os primeiros caracteres por segurança
        })

        res.status(401).json({
          success: false,
          error: 'Invalid API Key'
        })
        return
      }

      // API Key válida - adicionar informação de origem para logs
      req.apiKeySource = 'SCRAPER'

      logger.info('Scraper API Key validated successfully', {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        url: req.url,
        method: req.method,
        source: 'SCRAPER'
      })

      next()
    } catch (error) {
      logger.error('API Key validation error:', {
        error: error instanceof Error ? error.message : 'Unknown error',
        ip: req.ip,
        url: req.url,
        method: req.method
      })

      res.status(500).json({
        success: false,
        error: 'API Key validation failed'
      })
    }
  }

  /**
   * Middleware genérico para validação de API Key
   * Pode ser estendido para outros tipos de API Keys no futuro
   */
  static validateApiKey = (expectedKey: string, source: string) => {
    return (req: ApiKeyRequest, res: Response, next: NextFunction): void => {
      try {
        const apiKey = req.headers['x-api-key'] as string

        if (!apiKey) {
          res.status(400).json({
            success: false,
            error: 'X-API-Key header is required'
          })
          return
        }

        if (apiKey !== expectedKey) {
          logger.warn(`${source} API Key validation failed`, {
            ip: req.ip,
            source,
            url: req.url
          })

          res.status(401).json({
            success: false,
            error: 'Invalid API Key'
          })
          return
        }

        req.apiKeySource = source as any
        next()
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'API Key validation failed'
        })
      }
    }
  }
}
