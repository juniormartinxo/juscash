import { LoggingMiddleware } from '@/infrastructure/web/middleware/logging.middleware'
import { Request, Response, NextFunction } from 'express'

jest.mock('winston', () => {
    const mLogger = {
        info: jest.fn(),
        error: jest.fn(),
    }
    return {
        createLogger: jest.fn(() => mLogger),
        format: {
            combine: jest.fn(),
            timestamp: jest.fn(),
            errors: jest.fn(),
            json: jest.fn(),
            simple: jest.fn(),
        },
        transports: {
            File: jest.fn(),
            Console: jest.fn(),
        },
    }
})
const winston = require('winston')
const logger = winston.createLogger()

describe('LoggingMiddleware', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('shouldLogRequestDetailsOnRequestReceived', () => {
        const req = {
            method: 'GET',
            url: '/api/test',
            ip: '127.0.0.1',
            get: jest.fn().mockImplementation((header) => header === 'User-Agent' ? 'jest-agent' : undefined),
            user: { userId: 'user-123' },
        } as unknown as Request
        const res = {
            end: jest.fn(),
        } as unknown as Response
        const next = jest.fn()

        LoggingMiddleware.requestLogger(req, res, next)

        expect(logger.info).toHaveBeenCalledWith('Request received', expect.objectContaining({
            method: 'GET',
            url: '/api/test',
            ip: '127.0.0.1',
            userAgent: 'jest-agent',
            userId: 'user-123',
        }))
        expect(next).toHaveBeenCalled()
    })

    it('shouldLogRequestCompletionOnResponseEnd', () => {
        const req = {
            method: 'POST',
            url: '/api/complete',
            ip: '192.168.1.1',
            get: jest.fn().mockReturnValue('test-agent'),
            user: { userId: 'user-456' },
        } as unknown as Request
        const res: any = {
            statusCode: 201,
            end: function () { },
        }
        const next = jest.fn()

        LoggingMiddleware.requestLogger(req, res, next)

        // Simulate response end
        res.end('data', 'utf8', () => { })

        expect(logger.info).toHaveBeenCalledWith('Request completed', expect.objectContaining({
            method: 'POST',
            url: '/api/complete',
            statusCode: 201,
            responseTime: expect.any(Number),
            userId: 'user-456',
        }))
    })

    it('shouldLogErrorDetailsOnError', () => {
        const req = {
            method: 'DELETE',
            url: '/api/error',
            get: jest.fn(),
            user: { userId: 'user-789' },
        } as unknown as Request
        const res = {} as unknown as Response
        const next = jest.fn()
        const error = new Error('Something went wrong')

        LoggingMiddleware.errorLogger(error, req, res, next)

        expect(logger.error).toHaveBeenCalledWith('Request error', expect.objectContaining({
            error: 'Something went wrong',
            stack: error.stack,
            method: 'DELETE',
            url: '/api/error',
            userId: 'user-789',
        }))
        expect(next).toHaveBeenCalledWith(error)
    })

    it('shouldHandleMissingUserIdInLogs', () => {
        const req = {
            method: 'GET',
            url: '/api/no-user',
            ip: '10.0.0.1',
            get: jest.fn().mockReturnValue('agentless'),
            // no user property
        } as unknown as Request
        const res: any = {
            statusCode: 200,
            end: function () { },
        }
        const next = jest.fn()

        LoggingMiddleware.requestLogger(req, res, next)
        res.end()

        expect(logger.info).toHaveBeenCalledWith('Request received', expect.objectContaining({
            userId: undefined,
        }))
        expect(logger.info).toHaveBeenCalledWith('Request completed', expect.objectContaining({
            userId: undefined,
        }))

        const error = new Error('No user error')
        LoggingMiddleware.errorLogger(error, req, res, next)
        expect(logger.error).toHaveBeenCalledWith('Request error', expect.objectContaining({
            userId: undefined,
        }))
    })

    it('shouldHandleMissingOrMalformedUserAgentHeader', () => {
        const req = {
            method: 'GET',
            url: '/api/no-agent',
            ip: '10.0.0.2',
            get: jest.fn().mockReturnValueOnce(undefined),
            user: { userId: 'user-xyz' },
        } as unknown as Request
        const res: any = {
            statusCode: 200,
            end: function () { },
        }
        const next = jest.fn()

        LoggingMiddleware.requestLogger(req, res, next)
        res.end()

        expect(logger.info).toHaveBeenCalledWith('Request received', expect.objectContaining({
            userAgent: undefined,
        }))
    })

    it('shouldCallNextFunctionAfterLogging', () => {
        const req = {
            method: 'PUT',
            url: '/api/next',
            ip: '10.0.0.3',
            get: jest.fn(),
            user: { userId: 'user-next' },
        } as unknown as Request
        const res: any = {
            statusCode: 204,
            end: function () { },
        }
        const next = jest.fn()

        LoggingMiddleware.requestLogger(req, res, next)
        expect(next).toHaveBeenCalled()

        const error = new Error('Next error')
        LoggingMiddleware.errorLogger(error, req, res, next)
        expect(next).toHaveBeenCalledWith(error)
    })
})