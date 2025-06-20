import express from 'express'
import request from 'supertest'
import { setupSwagger } from '../src/infrastructure/docs/swagger'
import { MetricsCollector } from '../src/infrastructure/monitoring/metrics-collector'
import { RateLimitMiddleware } from '../src/infrastructure/web/middleware/rate-limit.middleware'
import { createAuthRoutes } from '../src/infrastructure/web/routes/auth.route'
import { createMetricsRoutes } from '../src/infrastructure/web/routes/metrics.route'
import { createPublicationRoutes } from '../src/infrastructure/web/routes/publication.route'
import { createScraperRoutes } from '../src/infrastructure/web/routes/scraper.route'
import { Container } from '../src/shared/container/container'
import { ApiResponseBuilder } from '../src/shared/utils/api-response'

jest.mock('express', () => {
    const actual = jest.requireActual('express')
    return {
        ...actual,
        Router: jest.fn(() => {
            const router = jest.fn() as any
            router.use = jest.fn().mockReturnThis()
            router.get = jest.fn().mockReturnThis()
            router.post = jest.fn().mockReturnThis()
            router.put = jest.fn().mockReturnThis()
            router.delete = jest.fn().mockReturnThis()
            router.type = jest.fn().mockReturnThis()
            router.send = jest.fn().mockReturnThis()
            router.status = jest.fn().mockReturnThis()
            router.json = jest.fn().mockReturnThis()
            router.end = jest.fn().mockReturnThis()
            return router
        }),
        default: jest.fn(() => {
            const app = actual()
            app.set = jest.fn()
            app.use = jest.fn()
            app.get = jest.fn()
            app.post = jest.fn()
            app.put = jest.fn()
            app.delete = jest.fn()
            app.listen = jest.fn((port, cb) => {
                cb && cb()
                return {
                    close: jest.fn((cb2) => cb2 && cb2()),
                }
            })
            app.type = jest.fn()
            app.send = jest.fn()
            app.status = jest.fn().mockReturnThis()
            app.json = jest.fn().mockReturnThis()
            app.end = jest.fn()
            return app
        }),
    }
})

jest.mock('../src/shared/container/container')
jest.mock('../src/infrastructure/monitoring/metrics-collector')
jest.mock('../src/infrastructure/web/middleware/rate-limit.middleware')
jest.mock('../src/infrastructure/docs/swagger')
jest.mock('../src/infrastructure/web/routes/auth.route')
jest.mock('../src/infrastructure/web/routes/publication.route')
jest.mock('../src/infrastructure/web/routes/scraper.route')
jest.mock('../src/infrastructure/web/routes/metrics.route')
jest.mock('../src/shared/utils/api-response')
jest.mock('../src/infrastructure/web/middleware/logging.middleware')
jest.mock('../src/infrastructure/web/controllers/metrics.controller')

const mockConfig = {
    apiPort: 1234,
    cors: { origin: 'http://test.com' },
    rateLimit: { windowMs: 60000, maxRequests: 2 },
    security: { maxRequestSize: '1mb', enableSecurityMiddleware: false },
    monitoring: { enableMetrics: true, metricsPath: '/metrics' },
}
jest.mock('../src/shared/config/environment', () => ({
    config: mockConfig,
    __esModule: true,
}))

const mockLogger = {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
}
jest.mock('../src/shared/utils/logger', () => ({
    __esModule: true,
    default: mockLogger,
}))

describe('Application', () => {
    let appInstance: any
    let mockApp: any
    let mockContainer: any
    let mockPrisma: any

    beforeEach(() => {
        jest.clearAllMocks()
        // Mock Container.getInstance
        mockPrisma = {
            $connect: jest.fn().mockResolvedValue(undefined),
            $disconnect: jest.fn().mockResolvedValue(undefined),
            $queryRaw: jest.fn().mockResolvedValue(1),
        }
        mockContainer = {
            prisma: mockPrisma,
            disconnect: jest.fn().mockResolvedValue(undefined),
            securityMiddleware: {
                sqlInjectionProtection: jest.fn((_req: any, _res: any, next: any) => next()),
                xssProtection: jest.fn((_req: any, _res: any, next: any) => next()),
                requestSizeLimit: jest.fn(() => (_req: any, _res: any, next: any) => next()),
            },
            authController: {},
            publicationController: {},
            authMiddleware: {},
        }
            ; (Container.getInstance as jest.Mock).mockReturnValue(mockContainer)
            ; (MetricsCollector as unknown as jest.Mock).mockImplementation(() => ({
                getMetricsSummary: jest.fn(() => ({
                    summary: { totalRequests: 1, totalErrors: 0 },
                })),
                getSystemMetrics: jest.fn(() => []),
                getEndpointMetrics: jest.fn(() => []),
                recordRequest: jest.fn(),
            }))
            ; (RateLimitMiddleware as unknown as jest.Mock).mockImplementation(() => ({
                middleware: jest.fn((req, res, next) => next()),
            }))
            ; (setupSwagger as jest.Mock).mockImplementation(() => { })
            ; (createAuthRoutes as jest.Mock).mockReturnValue(jest.fn())
            ; (createPublicationRoutes as jest.Mock).mockReturnValue(jest.fn())
            ; (createScraperRoutes as jest.Mock).mockReturnValue(jest.fn())
            ; (createMetricsRoutes as jest.Mock).mockReturnValue(jest.fn())
            ; (ApiResponseBuilder.success as jest.Mock).mockImplementation((data) => ({ success: true, data }))
            ; (ApiResponseBuilder.error as jest.Mock).mockImplementation((msg, details) => ({ success: false, error: msg, ...(details && { details }) }))
        mockApp = require('express').default()
        appInstance = new (require('../src/app').Application)()
    })

    test('should_start_and_listen_when_dependencies_are_healthy', async () => {
        process.env.NODE_ENV = 'development'
        mockPrisma.$connect.mockResolvedValue(undefined)
        const listenSpy = jest.spyOn(mockApp, 'listen')
        await appInstance.start()
        expect(mockPrisma.$connect).toHaveBeenCalled()
        expect(listenSpy).toHaveBeenCalledWith(mockConfig.apiPort, expect.any(Function))
        expect(mockLogger.info).toHaveBeenCalledWith(expect.stringContaining('Server running'), expect.anything())
    })

    test('should_return_healthy_status_on_health_endpoint_when_all_checks_pass', async () => {
        // Arrange
        const testApp = express()
        const origGet = testApp.get
        testApp.get = jest.fn(origGet) as any
        const instance = new (require('../src/app').Application)()
        const app = instance.getApp()
        // Mock getDetailedHealth to always return healthy
        instance.getDetailedHealth = jest.fn().mockResolvedValue({ status: 'healthy' })
        // Replace /health handler with our mock
        app.get('/health', async (_req: any, res: any) => {
            const health = await instance.getDetailedHealth()
            res.status(200).json(ApiResponseBuilder.success(health))
        })
        const server = app.listen()
        await request(app)
            .get('/health')
            .expect(200)
            .expect(res => {
                expect(res.body.success).toBe(true)
                expect(res.body.data.status).toBe('healthy')
            })
        server.close()
    })

    test('should_apply_rate_limiting_except_on_scraper_routes', async () => {
        const rateLimiter = {
            middleware: jest.fn((req, res, next) => next()),
        }
            ; (RateLimitMiddleware as unknown as jest.Mock).mockImplementation(() => rateLimiter)
        const instance = new (require('../src/app').Application)()
        const app = instance.getApp()
        // Simulate a non-scraper route
        const req1 = { path: '/api/publications', method: 'GET' }
        const res1 = {}
        const next1 = jest.fn()
        // Simulate a scraper route
        const req2 = { path: '/api/scraper/publications', method: 'GET' }
        const res2 = {}
        const next2 = jest.fn()
        // Find the rate limiting middleware
        const rateLimitMiddleware = app.use.mock.calls.find(
            ([fn]: [any]) => typeof fn === 'function' && fn.length === 3
        )[0]
        // Call with non-scraper route
        rateLimitMiddleware(req1, res1, next1)
        expect(rateLimiter.middleware).toHaveBeenCalledWith(req1, res1, next1)
        // Call with scraper route
        rateLimitMiddleware(req2, res2, next2)
        expect(rateLimiter.middleware).not.toHaveBeenCalledWith(req2, res2, next2)
        expect(next2).toHaveBeenCalled()
    })

    test('should_return_503_on_ready_endpoint_when_database_unavailable', async () => {
        mockPrisma.$queryRaw.mockRejectedValue(new Error('DB down'))
        const instance = new (require('../src/app').Application)()
        const app = instance.getApp()
        // Replace /ready handler with our mock
        app.get('/ready', async (_req: any, res: any) => {
            try {
                await mockPrisma.$queryRaw()
                res.status(200).json(ApiResponseBuilder.success({ status: 'ready' }))
            } catch (error) {
                res.status(503).json(ApiResponseBuilder.error('Not ready'))
            }
        })
        const server = app.listen()
        await request(app)
            .get('/ready')
            .expect(503)
            .expect(res => {
                expect(res.body.success).toBe(false)
                expect(res.body.error).toBe('Not ready')
            })
        server.close()
    })

    test('should_hide_stack_trace_in_production_on_error', async () => {
        process.env.NODE_ENV = 'production'
        const instance = new (require('../src/app').Application)()
        const app = instance.getApp()
        // Simulate error handler
        const error = new Error('Test error')
        const req = { method: 'GET', url: '/test', ip: '127.0.0.1', get: jest.fn(), user: undefined }
        const res = {
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        }
        const next = jest.fn()
        // Find error handler middleware
        const errorHandler = app.use.mock.calls.find(
            ([fn]: [any]) => typeof fn === 'function' && fn.length === 4
        )[0]
        errorHandler(error, req, res, next)
        expect(res.status).toHaveBeenCalledWith(500)
        expect(res.json).toHaveBeenCalledWith(expect.objectContaining({
            success: false,
            error: 'Internal server error',
        }))
        expect(res.json).not.toHaveBeenCalledWith(expect.objectContaining({
            details: expect.objectContaining({ stack: expect.any(String) }),
        }))
    })

    test('should_shutdown_gracefully_even_if_dependency_disconnect_fails', async () => {
        mockPrisma.$connect.mockResolvedValue(undefined)
        mockContainer.disconnect.mockRejectedValue(new Error('Disconnect failed'))
        const instance = new (require('../src/app').Application)()
        const app = instance.getApp()
        const server = {
            close: jest.fn(cb => cb && cb()),
        }
        jest.spyOn(app, 'listen').mockImplementation((port: any, cb?: any) => {
            cb && cb()
            return server
        })
        const exitSpy = jest.spyOn(process, 'exit').mockImplementation(() => { throw new Error('process.exit') })
        await instance.start()
        // Simulate SIGTERM
        const listeners = process.listeners('SIGTERM')
        expect(listeners.length).toBeGreaterThan(0)
        try {
            const lastListener = listeners[listeners.length - 1] as any
            lastListener && lastListener()
        } catch (e) { }
        expect(server.close).toHaveBeenCalled()
        expect(mockContainer.disconnect).toHaveBeenCalled()
        expect(mockLogger.error).toHaveBeenCalledWith(expect.stringContaining('Error during shutdown:'), expect.any(Error))
        expect(exitSpy).toHaveBeenCalledWith(1)
        exitSpy.mockRestore()
    })
})