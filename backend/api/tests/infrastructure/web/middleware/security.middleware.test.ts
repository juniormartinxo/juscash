import { SecurityMiddleware } from '@/infrastructure/web/middleware/security.middleware'
import { Request, Response, NextFunction } from 'express'
import { createHash } from 'crypto'

jest.mock('crypto', () => ({
    createHash: jest.fn(() => ({
        update: jest.fn().mockReturnThis(),
        digest: jest.fn(() => 'mockedhash')
    }))
}))

describe('SecurityMiddleware', () => {
    let middleware: SecurityMiddleware
    let req: jest.Mocked<Request>
    let res: jest.Mocked<Response>
    let next: jest.MockedFunction<NextFunction>
    let statusMock: jest.Mock
    let jsonMock: jest.Mock

    beforeEach(() => {
        middleware = new SecurityMiddleware()
        req = {
            query: {},
            body: {},
            params: {},
            url: '/api/test',
            ip: '127.0.0.1',
            get: jest.fn(),
            connection: { remoteAddress: '127.0.0.1' } as any
        } as any
        statusMock = jest.fn().mockReturnThis()
        jsonMock = jest.fn().mockReturnThis()
        res = {
            status: statusMock,
            json: jsonMock
        } as any
        next = jest.fn()
        jest.useFakeTimers()
        jest.clearAllMocks()
    })

    afterEach(() => {
        jest.useRealTimers()
    })

    it('shouldAllowSafeRequest', () => {
        req.query = { name: 'John' }
        req.body = { message: 'Hello world' }
        req.params = { id: '123' }
        req.url = '/api/test'
        req.get.mockReturnValue(undefined)

        middleware.sqlInjectionProtection(req, res, next)
        expect(next).toHaveBeenCalledTimes(1)
        middleware.xssProtection(req, res, next)
        expect(next).toHaveBeenCalledTimes(2)
        middleware.requestSizeLimit()(req, res, next)
        expect(next).toHaveBeenCalledTimes(3)
    })

    it('shouldSanitizeHtmlTagsInRequestBody', () => {
        req.body = { comment: '<script>alert("xss")</script>hello <b>world</b>' }
        req.url = '/api/test'
        middleware.xssProtection(req, res, next)
        expect(req.body.comment).toBe('hello world')
        expect(next).toHaveBeenCalled()
    })

    it('shouldAllowRequestWithinSizeLimit', () => {
        req.get.mockImplementation((header: string) => header === 'content-length' ? '512' : undefined)
        middleware.requestSizeLimit(1024)(req, res, next)
        expect(next).toHaveBeenCalled()
        expect(res.status).not.toHaveBeenCalled()
    })

    it('shouldBlockSqlInjectionAttempt', () => {
        req.query = { search: "1 OR 1=1" }
        middleware.sqlInjectionProtection(req, res, next)
        expect(res.status).toHaveBeenCalledWith(400)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Invalid request parameters 01',
        })
        expect(next).not.toHaveBeenCalled()
    })

    it('shouldBypassXssProtectionForScraperRoute', () => {
        req.url = '/api/scraper/data'
        req.body = { comment: '<script>alert("xss")</script>' }
        middleware.xssProtection(req, res, next)
        expect(req.body.comment).toBe('<script>alert("xss")</script>')
        expect(next).toHaveBeenCalled()
    })

    it('shouldRejectOversizedRequest', () => {
        req.get.mockImplementation((header: string) => header === 'content-length' ? '2048' : undefined)
        middleware.requestSizeLimit(1024)(req, res, next)
        expect(res.status).toHaveBeenCalledWith(413)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Request too large',
        })
        expect(next).not.toHaveBeenCalled()
    })
})