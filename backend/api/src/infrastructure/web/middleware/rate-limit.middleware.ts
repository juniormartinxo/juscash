import { NextFunction, Request, Response } from 'express'

interface RateLimitStore {
  [key: string]: {
    count: number
    resetTime: number
  }
}

export class RateLimitMiddleware {
  private store: RateLimitStore = {};
  private readonly windowMs: number
  private readonly maxRequests: number

  constructor(windowMs: number = 15 * 60 * 1000, maxRequests: number = 100) {
    this.windowMs = windowMs
    this.maxRequests = maxRequests

    // Limpar registros expirados a cada minuto
    setInterval(() => this.cleanExpiredEntries(), 60 * 1000)
  }

  middleware = (req: Request, res: Response, next: NextFunction): void => {
    const key = this.getKey(req)
    const now = Date.now()
    const entry = this.store[key]

    if (!entry || now > entry.resetTime) {
      this.store[key] = {
        count: 1,
        resetTime: now + this.windowMs,
      }
      next()
      return
    }

    if (entry.count >= this.maxRequests) {
      res.status(429).json({
        success: false,
        error: 'Too many requests',
        retryAfter: Math.ceil((entry.resetTime - now) / 1000),
      })
      return
    }

    entry.count++
    next()
  };

  private getKey(req: Request): string {
    // Use IP + User ID (if authenticated) for better rate limiting
    const ip = req.ip || req.connection.remoteAddress || 'unknown'
    const userId = (req as any).user?.userId || ''
    return `${ip}:${userId}`
  }

  private cleanExpiredEntries(): void {
    const now = Date.now()
    Object.keys(this.store).forEach(key => {
      const entry = this.store[key]
      if (entry && now > entry.resetTime) {
        delete this.store[key]
      }
    })
  }
}