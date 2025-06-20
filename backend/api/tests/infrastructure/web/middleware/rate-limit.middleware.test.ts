import { RateLimitMiddleware } from '../../../../src/infrastructure/web/middleware/rate-limit.middleware'
import { Request, Response, NextFunction } from 'express'

jest.useFakeTimers()

describe('RateLimitMiddleware', () => {
    let middlewareInstance: RateLimitMiddleware
    let req: Partial<Request>
    let res: Partial<Response>
    let next: jest.Mock

    beforeEach(() => {
        jest.clearAllMocks()
        jest.clearAllTimers()
        middlewareInstance = new RateLimitMiddleware(1000, 2) // 1s window, 2 requests allowed
        req = {
            ip: '1.2.3.4',
            connection: { remoteAddress: '1.2.3.4' } as any
        }
        res = {
            status: jest.fn().mockReturnThis(),
            json: jest.fn()
        }
        next = jest.fn()
    })

    test('shouldAllowRequestsUnderLimit', () => {
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(2)
        expect(res.status).not.toHaveBeenCalled()
        expect(res.json).not.toHaveBeenCalled()
    })

    test('shouldResetCountAfterWindowExpires', () => {
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(2)
        jest.spyOn(Date, 'now').mockImplementation(() => Date.now() + 2000)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(3)
        expect(res.status).not.toHaveBeenCalled()
    })

    test('shouldTrackLimitsPerUserOrIp', () => {
        const req1 = { ...req, ip: '1.2.3.4', user: { userId: 'user1' } }
        const req2 = { ...req, ip: '5.6.7.8', user: { userId: 'user2' } }
        middlewareInstance.middleware(req1 as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req2 as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req1 as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req2 as Request, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(4)
        expect(res.status).not.toHaveBeenCalled()
    })

    test('shouldBlockRequestsExceedingLimit', () => {
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(2)
        expect(res.status).toHaveBeenCalledWith(429)
        expect(res.json).toHaveBeenCalledWith(
            expect.objectContaining({
                success: false,
                error: 'Too many requests',
                retryAfter: expect.any(Number)
            })
        )
    })

    test('shouldHandleMissingOrMalformedIp', () => {
        const malformedReq = { connection: {}, user: { userId: 'abc' } }
        middlewareInstance.middleware(malformedReq as any, res as Response, next as NextFunction)
        expect(next).toHaveBeenCalledTimes(1)
        expect(res.status).not.toHaveBeenCalled()
    })

    test('shouldCleanExpiredEntriesPeriodically', () => {
        const now = Date.now()
        jest.spyOn(Date, 'now').mockImplementation(() => now)
        middlewareInstance.middleware(req as Request, res as Response, next as NextFunction)
        expect(Object.keys((middlewareInstance as any).store)).toHaveLength(1)
        jest.spyOn(Date, 'now').mockImplementation(() => now + 2000)
        jest.advanceTimersByTime(60 * 1000)
            // Force cleanup
            ; (middlewareInstance as any).cleanExpiredEntries()
        expect(Object.keys((middlewareInstance as any).store)).toHaveLength(0)
    })
})