import { LogoutUseCase } from '@/application/usecases/auth/logout.usecase'
import { AuthService } from '@/domain/services/auth.service'

describe('LogoutUseCase', () => {
    let authService: jest.Mocked<AuthService>
    let logoutUseCase: LogoutUseCase

    beforeEach(() => {
        authService = {
            invalidateToken: jest.fn(),
            generateTokens: jest.fn(),
            validatePassword: jest.fn(),
            hashPassword: jest.fn(),
            validateToken: jest.fn(),
        }
        logoutUseCase = new LogoutUseCase(authService)
    })

    it('should_logout_successfully_with_valid_token', async () => {
        const input = { accessToken: 'valid-token' }
        authService.invalidateToken.mockResolvedValueOnce(undefined)

        const result = await logoutUseCase.execute(input)

        expect(result).toEqual({ message: 'Logged out successfully' })
        expect(authService.invalidateToken).toHaveBeenCalledWith('valid-token')
    })

    it('should_call_invalidateToken_with_correct_token', async () => {
        const input = { accessToken: 'expected-token' }
        authService.invalidateToken.mockResolvedValueOnce(undefined)

        await logoutUseCase.execute(input)

        expect(authService.invalidateToken).toHaveBeenCalledWith('expected-token')
    })

    it('should_return_expected_logout_message', async () => {
        const input = { accessToken: 'any-token' }
        authService.invalidateToken.mockResolvedValueOnce(undefined)

        const result = await logoutUseCase.execute(input)

        expect(result).toHaveProperty('message', 'Logged out successfully')
    })

    it('should_handle_already_invalidated_token', async () => {
        const input = { accessToken: 'already-invalidated-token' }
        // Simulate invalidateToken resolves even if token is already invalidated
        authService.invalidateToken.mockResolvedValueOnce(undefined)

        const result = await logoutUseCase.execute(input)

        expect(result).toEqual({ message: 'Logged out successfully' })
        expect(authService.invalidateToken).toHaveBeenCalledWith('already-invalidated-token')
    })

    it('should_handle_invalidateToken_errors', async () => {
        const input = { accessToken: 'error-token' }
        const error = new Error('Service failure')
        authService.invalidateToken.mockRejectedValueOnce(error)

        await expect(logoutUseCase.execute(input)).rejects.toThrow('Service failure')
        expect(authService.invalidateToken).toHaveBeenCalledWith('error-token')
    })

    it('should_handle_missing_or_malformed_accessToken', async () => {
        const input = {}
        // @ts-expect-error Testing missing accessToken
        await expect(logoutUseCase.execute(input)).rejects.toThrow()
        const malformedInput = { accessToken: 12345 }
        // @ts-expect-error Testing malformed accessToken (not a string)
        await expect(logoutUseCase.execute(malformedInput)).rejects.toThrow()
    })
})