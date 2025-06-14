import { createHash } from 'crypto'
import { Request, Response, NextFunction } from 'express'

export class SecurityMiddleware {
  private suspiciousRequests = new Map<string, number>();
  private readonly maxSuspiciousRequests = 10;
  private readonly suspiciousWindowMs = 60 * 1000; // 1 minute

  // SQL Injection protection
  sqlInjectionProtection = (req: Request, res: Response, next: NextFunction): void => {
    const sqlPatterns = [
      /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)/i,
      /(UNION|HAVING|GROUP BY|ORDER BY)/i,
      /('(''|[^'])*')/i,
      /(;|\|\||&&)/,
      /(\bOR\b.*=.*\bOR\b)/i,
      /(\bAND\b.*=.*\bAND\b)/i,
    ]

    const checkValue = (value: any): boolean => {
      if (typeof value === 'string') {
        return sqlPatterns.some(pattern => pattern.test(value))
      }
      if (typeof value === 'object' && value !== null) {
        return Object.values(value).some(v => checkValue(v))
      }
      return false
    }

    const suspicious = checkValue(req.query) || checkValue(req.body) || checkValue(req.params)

    if (suspicious) {
      this.markSuspiciousRequest(req)
      res.status(400).json({
        success: false,
        error: 'Invalid request parameters',
      })
      return
    }

    next()
  };

  // XSS Protection
  xssProtection = (req: Request, res: Response, next: NextFunction): void => {
    // Skip XSS protection for scraper routes to avoid array/object conversion issues
    if (req.url.startsWith('/api/scraper/')) {
      next()
      return
    }

    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /<iframe[^>]*>.*?<\/iframe>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<[^>]*>/gi,
    ]

    const containsXSS = (value: any): boolean => {
      if (typeof value === 'string') {
        return xssPatterns.some(pattern => pattern.test(value))
      }
      if (typeof value === 'object' && value !== null) {
        return Object.values(value).some(v => containsXSS(v))
      }
      return false
    }

    const sanitizeValue = (value: any): any => {
      if (typeof value === 'string') {
        return xssPatterns.reduce((acc, pattern) => acc.replace(pattern, ''), value)
      }
      if (typeof value === 'object' && value !== null) {
        const sanitized: any = {}
        for (const [key, val] of Object.entries(value)) {
          sanitized[key] = sanitizeValue(val)
        }
        return sanitized
      }
      return value
    }

    // Check for XSS in query parameters (read-only in Express 5.x)
    if (req.query && containsXSS(req.query)) {
      this.markSuspiciousRequest(req)
      res.status(400).json({
        success: false,
        error: 'Invalid request parameters',
      })
      return
    }

    // Sanitize body (can be modified)
    if (req.body) {
      req.body = sanitizeValue(req.body)
    }

    next()
  };

  // Request size limiting
  requestSizeLimit = (maxSize: number = 1024 * 1024) => {
    return (req: Request, res: Response, next: NextFunction): void => {
      const contentLength = req.get('content-length')

      if (contentLength && parseInt(contentLength) > maxSize) {
        res.status(413).json({
          success: false,
          error: 'Request too large',
        })
        return
      }

      next()
    }
  };

  private markSuspiciousRequest(req: Request): void {
    const ip = req.ip || req.connection.remoteAddress || 'unknown'
    const key = this.generateKey(ip, req.get('user-agent') || '')

    const count = this.suspiciousRequests.get(key) || 0
    this.suspiciousRequests.set(key, count + 1)

    // Clean up old entries
    setTimeout(() => {
      this.suspiciousRequests.delete(key)
    }, this.suspiciousWindowMs)

    // Log if too many suspicious requests
    if (count > this.maxSuspiciousRequests) {
      console.warn(`Suspicious activity detected from ${ip}`)
    }
  }

  private generateKey(ip: string, userAgent: string): string {
    return createHash('sha256').update(ip + userAgent).digest('hex')
  }
}
