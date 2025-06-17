import { NextFunction, Request, Response } from 'express'
import { AuthService } from '@/domain/services/auth.service'
import logger from '@/shared/utils/logger'

interface AuthenticatedRequest extends Request {
  user?: {
    userId: string
    email: string
  }
}

export class AuthMiddleware {
  constructor(private authService: AuthService) { }

  authenticate = async (
    req: AuthenticatedRequest,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      const authHeader = req.headers.authorization
      logger.debug('Auth header received:', authHeader)

      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        logger.warn('Missing or invalid authorization header')
        res.status(401).json({
          success: false,
          error: 'Authorization token required',
        })
        return
      }

      const token = authHeader.substring(7)
      logger.debug('Token extracted:', token.substring(0, 20) + '...')

      const payload = await this.authService.validateToken(token)
      logger.debug('Token validation result:', payload)

      if (!payload) {
        logger.warn('Token validation failed - payload is null')
        res.status(401).json({
          success: false,
          error: 'Invalid or expired token',
        })
        return
      }

      req.user = payload
      logger.debug('User authenticated:', payload)
      next()
    } catch (error) {
      logger.error('Authentication error:', error)
      res.status(401).json({
        success: false,
        error: 'Authentication failed',
      })
    }
  };
}
