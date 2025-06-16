import 'dotenv/config'
import compression from 'compression'
import cors from 'cors'
import express from 'express'
import helmet from 'helmet'
import { setupSwagger } from './infrastructure/docs/swagger'
import { MetricsCollector } from './infrastructure/monitoring/metrics-collector'
import { MetricsController } from './infrastructure/web/controllers/metrics.controller'
import { LoggingMiddleware } from './infrastructure/web/middleware/logging.middleware'
import { RateLimitMiddleware } from './infrastructure/web/middleware/rate-limit.middleware'
import { createAuthRoutes } from './infrastructure/web/routes/auth.route'
import { createMetricsRoutes } from './infrastructure/web/routes/metrics.route'
import { createPublicationRoutes } from './infrastructure/web/routes/publication.route'
import { createScraperRoutes } from './infrastructure/web/routes/scraper.route'
import { config } from './shared/config/environment'
import { Container } from './shared/container/container'
import { ApiResponseBuilder } from './shared/utils/api-response'
import { AppError } from './shared/utils/error-handler'
import logger from './shared/utils/logger'

class Application {
  private app: express.Application
  private container: Container
  private metricsCollector: MetricsCollector
  private rateLimiter: RateLimitMiddleware

  constructor() {
    this.app = express()
    this.container = Container.getInstance()
    this.metricsCollector = new MetricsCollector()
    this.rateLimiter = new RateLimitMiddleware(
      config.rateLimit.windowMs,
      config.rateLimit.maxRequests
    )

    this.setupMiddlewares()
    this.setupRoutes()
    this.setupErrorHandling()
  }

  private setupMiddlewares(): void {
    // Trust proxy (important for rate limiting and IP detection)
    this.app.set('trust proxy', 1)

    // Security headers
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
        },
      },
      hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
      }
    }))

    // CORS configuration
    this.app.use(cors({
      origin: config.cors.origin,
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    }))

    // Request parsing
    this.app.use(express.json({
      limit: config.security.maxRequestSize,
      type: ['application/json', 'text/plain']
    }))
    this.app.use(express.urlencoded({
      extended: true,
      limit: config.security.maxRequestSize
    }))

    // Compression
    this.app.use(compression({
      filter: (req, res) => {
        if (req.headers['x-no-compression']) {
          return false
        }
        return compression.filter(req, res)
      },
      level: 6,
      threshold: 1024,
    }))

    // Rate limiting (excluir rotas do scraper que têm seu próprio rate limiting)
    this.app.use((req, res, next) => {
      if (req.path.startsWith('/api/scraper')) {
        // Pular rate limiting geral para rotas do scraper
        next()
      } else {
        // Aplicar rate limiting geral para outras rotas
        this.rateLimiter.middleware(req, res, next)
      }
    })

    // Security middleware
    if (config.security.enableSecurityMiddleware) {
      this.app.use(this.container.securityMiddleware.sqlInjectionProtection)
      this.app.use(this.container.securityMiddleware.xssProtection)
      this.app.use(this.container.securityMiddleware.requestSizeLimit())
    }

    // Performance monitoring
    // this.app.use(this.container.performanceMiddleware.middleware)

    // Request logging
    // this.app.use(LoggingMiddleware.requestLogger)

    // Metrics collection
    // if (config.monitoring.enableMetrics) {
    //   this.app.use((req, res, next) => {
    //     const startTime = Date.now()

    //     res.on('finish', () => {
    //       const responseTime = Date.now() - startTime
    //       this.metricsCollector.recordRequest(
    //         req.method,
    //         req.route?.path || req.path,
    //         res.statusCode,
    //         responseTime
    //       )
    //     })

    //     next()
    //   })
    // }
  }

  private setupRoutes(): void {
    // Setup Swagger documentation
    setupSwagger(this.app)

    // Health check with detailed information
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.getDetailedHealth()
        res.status(health.status === 'healthy' ? 200 : 503)
          .json(ApiResponseBuilder.success(health))
      } catch (error) {
        logger.error('Health check failed:', error)
        res.status(503).json(ApiResponseBuilder.error('Health check failed'))
      }
    })

    // Readiness probe (for Kubernetes)
    this.app.get('/ready', async (req, res) => {
      try {
        await this.container.prisma.$queryRaw`SELECT 1`
        res.status(200).json(ApiResponseBuilder.success({ status: 'ready' }))
      } catch (error) {
        res.status(503).json(ApiResponseBuilder.error('Not ready'))
      }
    })

    // Liveness probe (for Kubernetes)
    this.app.get('/alive', (req, res) => {
      res.status(200).json(ApiResponseBuilder.success({ status: 'alive' }))
    })

    // API information endpoint
    this.app.get('/api', (req, res) => {
      res.json(ApiResponseBuilder.success({
        name: 'DJE Management API',
        version: '1.0.0',
        description: 'API para gerenciamento de publicações do DJE de São Paulo',
        environment: process.env.NODE_ENV || 'development',
        documentation: '/api-docs',
        health: '/health',
        metrics: config.monitoring.enableMetrics ? config.monitoring.metricsPath : null,
        endpoints: {
          auth: {
            register: 'POST /api/auth/register',
            login: 'POST /api/auth/login',
            refresh: 'POST /api/auth/refresh',
            logout: 'POST /api/auth/logout',
          },
          publications: {
            create: 'POST /api/publications',
            list: 'GET /api/publications',
            search: 'GET /api/publications/search',
            get: 'GET /api/publications/:id',
            updateStatus: 'PUT /api/publications/:id/status',
          },
          scraper: {
            createPublication: 'POST /api/scraper/publications (requires X-API-Key header)',
          },
        },
      }))
    })

    // Main API routes
    this.app.use('/api/auth', createAuthRoutes(this.container.authController))
    this.app.use('/api/publications', createPublicationRoutes(
      this.container.publicationController,
      this.container.authMiddleware
    ))

    // Scraper API routes (sem autenticação JWT, usa API Key)
    this.app.use('/api/scraper', createScraperRoutes(
      this.container.publicationController
    ))

    // Metrics routes (admin only)
    if (config.monitoring.enableMetrics) {
      const metricsController = new MetricsController(this.metricsCollector)
      this.app.use(config.monitoring.metricsPath, createMetricsRoutes(
        metricsController,
        this.container.authMiddleware
      ))
    }

    // Robots.txt
    this.app.get('/robots.txt', (req, res) => {
      res.type('text/plain')
      res.send('User-agent: *\nDisallow: /')
    })

    // Favicon
    this.app.get('/favicon.ico', (req, res) => {
      res.status(204).end()
    })

    // Simple test endpoint
    this.app.post('/test', (req, res) => {
      res.json({ success: true, message: 'Test endpoint working', body: req.body })
    })
  }

  private setupErrorHandling(): void {
    // Error logging middleware
    this.app.use(LoggingMiddleware.errorLogger)

    // Global error handler
    this.app.use((error: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
      logger.error('Unhandled error:', {
        error: error.message,
        stack: error.stack,
        method: req.method,
        url: req.url,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        userId: (req as any).user?.userId,
      })

      // Don't send stack traces in production
      const isDevelopment = process.env.NODE_ENV === 'development'

      if (error instanceof AppError) {
        res.status(error.statusCode).json(ApiResponseBuilder.error(
          error.message,
          isDevelopment ? { stack: error.stack } : undefined
        ))
        return
      }

      // Default error response
      const statusCode = (error as any).statusCode || 500
      const message = statusCode === 500 ? 'Internal server error' : error.message

      res.status(statusCode).json(ApiResponseBuilder.error(
        message,
        isDevelopment ? { stack: error.stack } : undefined
      ))
    })

    // 404 handler
    this.app.use((req, res) => {
      logger.warn('Route not found:', {
        method: req.method,
        url: req.url,
        ip: req.ip,
      })

      res.status(404).json(ApiResponseBuilder.error('Route not found'))
    })
  }

  private async getDetailedHealth(): Promise<any> {
    const checks = await Promise.allSettled([
      this.checkDatabase(),
      this.checkMemoryUsage(),
      this.checkDiskSpace(),
    ])

    const databaseHealth = checks[0].status === 'fulfilled' ? checks[0].value : 'unhealthy'
    const memoryHealth = checks[1].status === 'fulfilled' ? checks[1].value : 'unhealthy'
    const diskHealth = checks[2].status === 'fulfilled' ? checks[2].value : 'unhealthy'

    const overallHealth = [databaseHealth, memoryHealth, diskHealth].every(h => h === 'healthy')
      ? 'healthy'
      : 'unhealthy'

    return {
      status: overallHealth,
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: process.uptime(),
      environment: process.env.NODE_ENV || 'development',
      checks: {
        database: databaseHealth,
        memory: memoryHealth,
        disk: diskHealth,
      },
      metrics: config.monitoring.enableMetrics ? this.metricsCollector.getMetricsSummary().summary : null,
      system: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage(),
        cpu: process.cpuUsage(),
      },
    }
  }

  private async checkDatabase(): Promise<string> {
    try {
      await this.container.prisma.$queryRaw`SELECT 1`
      return 'healthy'
    } catch (error) {
      logger.error('Database health check failed:', error)
      return 'unhealthy'
    }
  }

  private async checkMemoryUsage(): Promise<string> {
    const memUsage = process.memoryUsage()
    const heapUsedMB = memUsage.heapUsed / 1024 / 1024
    const heapTotalMB = memUsage.heapTotal / 1024 / 1024
    const usagePercent = (heapUsedMB / heapTotalMB) * 100

    // Alert if memory usage is over 85%
    if (usagePercent > 85) {
      logger.warn(`High memory usage: ${usagePercent.toFixed(2)}%`)
      return 'warning'
    }

    return usagePercent > 95 ? 'unhealthy' : 'healthy'
  }

  private async checkDiskSpace(): Promise<string> {
    // This is a simplified check - in production you'd use a proper disk space check
    try {
      const fs = await import('fs/promises')
      const stats = await fs.stat('./')
      return 'healthy'
    } catch (error) {
      return 'unhealthy'
    }
  }

  public async start(): Promise<void> {
    const apiPort = config.apiPort

    try {
      // Test database connection
      await this.container.prisma.$connect()
      logger.info('✅ Database connected successfully')

      // Start server
      const server = this.app.listen(apiPort, () => {
        logger.info(`🚀 Server running on http://localhost:${apiPort}`)
        logger.info(`📋 Health check: http://localhost:${apiPort}/health`)
        logger.info(`📚 API docs: http://localhost:${apiPort}/api-docs`)
        logger.info(`🔗 API info: http://localhost:${apiPort}/api`)

        if (config.monitoring.enableMetrics) {
          logger.info(`📊 Metrics: http://localhost:${apiPort}${config.monitoring.metricsPath}`)
        }
      })

      // Graceful shutdown handlers
      const gracefulShutdown = async (signal: string) => {
        logger.info(`${signal} received, shutting down gracefully...`)

        server.close(async () => {
          try {
            await this.container.disconnect()
            logger.info('✅ Server shut down gracefully')
            process.exit(0)
          } catch (error) {
            logger.error('❌ Error during shutdown:', error)
            process.exit(1)
          }
        })

        // Force shutdown after 30 seconds
        setTimeout(() => {
          logger.error('❌ Could not close connections in time, forcefully shutting down')
          process.exit(1)
        }, 30000)
      }

      process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
      process.on('SIGINT', () => gracefulShutdown('SIGINT'))

      // Handle uncaught exceptions
      process.on('uncaughtException', (error) => {
        logger.error('Uncaught exception:', error)
        process.exit(1)
      })

      process.on('unhandledRejection', (reason, promise) => {
        logger.error('Unhandled rejection at:', promise, 'reason:', reason)
        process.exit(1)
      })

    } catch (error) {
      logger.error('❌ Failed to start server:', error)
      process.exit(1)
    }
  }

  public getApp(): express.Application {
    return this.app
  }
}

// Create and start application
const application = new Application()

// Start server only if this file is run directly
// More robust check for different environments (works better in containers)
const isMainModule = process.argv[1] && (
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url.endsWith(process.argv[1]) ||
  process.argv[1].endsWith('src/app.ts')
)

if (isMainModule) {
  application.start().catch((error) => {
    console.error('Failed to start application:', error)
    process.exit(1)
  })
}

export default application.getApp()
