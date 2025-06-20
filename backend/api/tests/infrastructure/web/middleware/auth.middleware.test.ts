import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'
import { AuthService } from '@/domain/services/auth.service'
import logger from '@/shared/utils/logger'
import { Request, Response, NextFunction } from 'express'

jest.mock('@/shared/utils/logger', () => ({
    debug: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
}))

describe('AuthMiddleware', () => {
    let authService: jest.Mocked<AuthService>
    let middleware: AuthMiddleware
    let req: any
    let res: any
    let next: jest.MockedFunction<NextFunction>

    beforeEach(() => {
        authService = {
            validateToken: jest.fn(),
            generateTokens: jest.fn(),
            validatePassword: jest.fn(),
            hashPassword: jest.fn(),
            invalidateToken: jest.fn(),
        } as any

        middleware = new AuthMiddleware(authService)
        req = {
            headers: {},
        }
        res = {
            status: jest.fn().mockReturnThis(),
            json: jest.fn(),
        }
        next = jest.fn()
        jest.clearAllMocks()
    })

    it('should_authenticate_and_attach_user_with_valid_token', async () => {
        req.headers.authorization = 'Bearer validtoken'
        const userPayload = { userId: '123', email: 'test@example.com' }
        authService.validateToken.mockResolvedValue(userPayload)

        await middleware.authenticate(req, res as Response, next)

        expect(authService.validateToken).toHaveBeenCalledWith('validtoken')
        expect(req.user).toEqual(userPayload)
        expect(next).toHaveBeenCalled()
        expect(res.status).not.toHaveBeenCalled()
        expect(res.json).not.toHaveBeenCalled()
    })

    it('should_call_next_on_successful_authentication', async () => {
        req.headers.authorization = 'Bearer validtoken'
        authService.validateToken.mockResolvedValue({ userId: 'abc', email: 'a@b.com' })

        await middleware.authenticate(req, res as Response, next)

        expect(next).toHaveBeenCalled()
    })

    it('should_log_debug_information_on_successful_authentication', async () => {
        req.headers.authorization = 'Bearer validtoken'
        const userPayload = { userId: 'u1', email: 'e@e.com' }
        authService.validateToken.mockResolvedValue(userPayload)

        await middleware.authenticate(req, res as Response, next)

        expect(logger.debug).toHaveBeenCalledWith('Auth header received:', 'Bearer validtoken')
        expect(logger.debug).toHaveBeenCalledWith('Token extracted:', expect.stringContaining('validtoken'))
        expect(logger.debug).toHaveBeenCalledWith('Token validation result:', userPayload)
        expect(logger.debug).toHaveBeenCalledWith('User authenticated:', userPayload)
    })

    it('should_return_401_if_authorization_header_missing', async () => {
        req.headers = {}

        await middleware.authenticate(req, res as Response, next)

        expect(logger.warn).toHaveBeenCalledWith('Missing or invalid authorization header')
        expect(res.status).toHaveBeenCalledWith(401)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Authorization token required',
        })
        expect(next).not.toHaveBeenCalled()
    })

    it('should_return_401_if_token_invalid_or_expired', async () => {
        req.headers.authorization = 'Bearer invalidtoken'
        authService.validateToken.mockResolvedValue(null)

        await middleware.authenticate(req, res as Response, next)

        expect(authService.validateToken).toHaveBeenCalledWith('invalidtoken')
        expect(logger.warn).toHaveBeenCalledWith('Token validation failed - payload is null')
        expect(res.status).toHaveBeenCalledWith(401)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Invalid or expired token',
        })
        expect(next).not.toHaveBeenCalled()
    })

    it('should_return_401_and_log_error_on_authentication_exception', async () => {
        req.headers.authorization = 'Bearer sometoken'
        const error = new Error('Unexpected')
        authService.validateToken.mockRejectedValue(error)

        await middleware.authenticate(req, res as Response, next)

        expect(logger.error).toHaveBeenCalledWith('Authentication error:', error)
        expect(res.status).toHaveBeenCalledWith(401)
        expect(res.json).toHaveBeenCalledWith({
            success: false,
            error: 'Authentication failed',
        })
        expect(next).not.toHaveBeenCalled()
    })
})