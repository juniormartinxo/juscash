import { ApiKeyMiddleware } from '@/infrastructure/web/middleware/api-key.middleware'
import { config } from '@/shared/config/environment'
import logger from '@/shared/utils/logger'
import { Request, Response, NextFunction } from 'express'

jest.mock('@/shared/config/environment', () => ({
    config: {
        scraper: {
            apiKey: 'test-scraper-key'
        }
    }
}))
jest.mock('@/shared/utils/logger', () => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
}))

describe('ApiKeyMiddleware', () => {
    let req: Partial<Request> & { apiKeySource?: string, headers: Record<string, string> }
    let res: Partial<Response>
    let next: NextFunction

    beforeEach(() => {
        req = {
            headers: {},
            ip: '127.0.0.1',
            get: jest.fn().mockImplementation((header) => {
                if (header === 'User-Agent') return 'jest-agent'
                return undefined
            }),
            url: '/test',
            method: 'GET'
        }
        res = {
            status: jest.fn().mockReturnThis(),
            json: jest.fn()
        }
        next = jest.fn()
        jest.clearAllMocks()
    })

    it('should_allow_request_with_valid_scraper_api_key_and_set_source', () => {
        req.headers['x-api-key'] = 'test-scraper-key'
        ApiKeyMiddleware.validateScraperApiKey(
            req as any,
            res as any,
            next
        )
        expect(req.apiKeySource).toBe('SCRAPER')
        expect(next).toHaveBeenCalled()
        expect(res.status).not.toHaveBeenCalled()
        expect(res.json).not.toHaveBeenCalled()
    })

    it('should_allow_request_with_valid_generic_api_key_and_set_source', () => {
        req.headers['x-api-key'] = 'generic-key'
        const middleware = ApiKeyMiddleware.validateApiKey('generic-key', 'GENERIC')
        middleware(req as any, res as any, next)
        expect(req.apiKeySource).toBe('GENERIC')
        expect(next).toHaveBeenCalled()
        expect(res.status).not.toHaveBeenCalled()
        expect(res.json).not.toHaveBeenCalled()
    })

    it('should_log_successful_api_key_validation', () => {
        req.headers['x-api-key'] = 'test-scraper-key'
        ApiKeyMiddleware.validateScraperApiKey(
            req as any,
            res as any,
            next
        )
        expect(logger.info).toHaveBeenCalledWith(
            'Scraper API Key validated successfully',
            expect.objectContaining({
                ip: '127.0.0.1',
                userAgent: 'jest-agent',
                url: '/test',
                method: 'GET',
                source: 'SCRAPER'
            })
        )
    })

    it('should_reject_request_missing_api_key_header_with_400', () => {
        ApiKeyMiddleware.validateScraperApiKey(
            req as any,
            res as any,
            next
        )
        expect(res.status).toHaveBeenCalledWith(400)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'X-API-Key header is required'
        })
        expect(next).not.toHaveBeenCalled()
    })

    it('should_reject_request_with_invalid_api_key_with_401_and_log_warning', () => {
        req.headers['x-api-key'] = 'wrong-key'
        ApiKeyMiddleware.validateScraperApiKey(
            req as any,
            res as any,
            next
        )
        expect(res.status).toHaveBeenCalledWith(401)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Invalid API Key 01'
        })
        expect(logger.warn).toHaveBeenCalledWith(
            'API Key validation failed: Invalid API Key',
            expect.objectContaining({
                ip: '127.0.0.1',
                userAgent: 'jest-agent',
                url: '/test',
                method: 'GET',
                providedKey: expect.stringContaining('wrong-key'.substring(0, 8))
            })
        )
        expect(next).not.toHaveBeenCalled()
    })

    it('should_return_500_if_scraper_api_key_not_configured_and_log_error', () => {
        // @ts-ignore
        config.scraper.apiKey = undefined
        req.headers['x-api-key'] = 'test-scraper-key'
        ApiKeyMiddleware.validateScraperApiKey(
            req as any,
            res as any,
            next
        )
        expect(res.status).toHaveBeenCalledWith(500)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Server configuration error'
        })
        expect(logger.error).toHaveBeenCalledWith(
            'SCRAPER_API_KEY not configured in environment variables'
        )
        expect(next).not.toHaveBeenCalled()
    })
})