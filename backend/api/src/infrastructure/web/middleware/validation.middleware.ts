import { NextFunction, Request, Response } from 'express'
import { ZodError, ZodSchema } from 'zod'

export class ValidationMiddleware {
  static validateBody(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
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
          body: req.body,
        })
      }
    }
  }

  static validateQuery(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
      try {
        const validatedQuery = schema.parse(req.query)
          // Store validated query in a custom property instead of overwriting req.query
          ; (req as any).validatedQuery = validatedQuery
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
          query: req.query,
        })
      }
    }
  }

  static validateParams(schema: ZodSchema) {
    return (req: Request, res: Response, next: NextFunction) => {
      //console.log('ValidationMiddleware.validateParams', req.params.id)

      try {
        req.params = schema.parse(req.params)
        console.log('ValidationMiddleware.validateParams', req.params.id)
        next()
      } catch (error) {
        console.log('ValidationMiddleware.error', error)
        if (error instanceof ZodError) {
          res.status(400).json({
            success: false,
            error: 'Invalid URL parameters',
          })
          return
        }

        res.status(400).json({
          success: false,
          error: 'Invalid request parameters 03',
        })
      }
    }
  }
}
