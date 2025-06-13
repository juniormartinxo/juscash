import { NextFunction, Request, Response } from 'express'
import winston from 'winston'

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    ...(process.env.NODE_ENV !== 'production'
      ? [new winston.transports.Console({
        format: winston.format.simple()
      })]
      : []
    ),
  ],
})

export class LoggingMiddleware {
  static requestLogger = (req: Request, res: Response, next: NextFunction): void => {
    const startTime = Date.now()

    // Log da requisição
    logger.info('Request received', {
      method: req.method,
      url: req.url,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      userId: (req as any).user?.userId,
    })

    // Interceptar o final da resposta
    const originalEnd = res.end
    res.end = function (chunk?: any, encoding?: BufferEncoding | (() => void), callback?: () => void): Response {
      const responseTime = Date.now() - startTime

      logger.info('Request completed', {
        method: req.method,
        url: req.url,
        statusCode: res.statusCode,
        responseTime,
        userId: (req as any).user?.userId,
      })

      return originalEnd.call(res, chunk, encoding as BufferEncoding, callback)
    }

    next()
  };

  static errorLogger = (error: Error, req: Request, res: Response, next: NextFunction): void => {
    logger.error('Request error', {
      error: error.message,
      stack: error.stack,
      method: req.method,
      url: req.url,
      userId: (req as any).user?.userId,
    })

    next(error)
  };
}