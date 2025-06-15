import { NextFunction, Request, Response } from 'express'
import { ZodError, ZodSchema } from 'zod'

export class ValidationMiddleware {
  static validateBody(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
      console.log('req.body', req.body)
      console.log('res', res)
      try {
        req.body = schema.parse(req.body)
        next()
      } catch (error) {
        if (error instanceof ZodError) {
          const errors = error.errors.map(err => ({
            field: err.path.join('.'),
            message: err.message,
          }))

          res.status(400).json({
            success: false,
            error: 'Validation failed',
            details: errors,
          })
          return
        }

        res.status(400).json({
          success: false,
          error: 'Invalid request data',
        })
      }
    }
  }

  static validateQuery(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
      console.log('req.query', req.query)
      try {
        req.query = schema.parse(req.query)
        next()
      } catch (error) {
        if (error instanceof ZodError) {
          const errors = error.errors.map(err => ({
            field: err.path.join('.'),
            message: err.message,
          }))

          res.status(400).json({
            success: false,
            error: 'Query validation failed',
            details: errors,
          })
          return
        }

        res.status(400).json({
          success: false,
          error: 'Invalid query parameters',
        })
      }
    }
  }

  static validateParams(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
      try {
        req.params = schema.parse(req.params)
        next()
      } catch (error) {
        if (error instanceof ZodError) {
          res.status(400).json({
            success: false,
            error: 'Invalid URL parameters',
          })
          return
        }

        res.status(400).json({
          success: false,
          error: 'Invalid request parameters',
        })
      }
    }
  }
}