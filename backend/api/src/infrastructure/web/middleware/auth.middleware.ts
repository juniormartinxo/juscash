import { NextFunction, Request, Response } from 'express'
import { AuthService } from '../../../domain/services/auth.service.js'

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

      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        res.status(401).json({
          success: false,
          error: 'Authorization token required',
        })
        return
      }

      const token = authHeader.substring(7)
      const payload = await this.authService.validateToken(token)

      if (!payload) {
        res.status(401).json({
          success: false,
          error: 'Invalid or expired token',
        })
        return
      }

      req.user = payload
      next()
    } catch (error) {
      res.status(401).json({
        success: false,
        error: 'Authentication failed',
      })
    }
  };
}
