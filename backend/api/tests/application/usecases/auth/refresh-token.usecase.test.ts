import { RefreshTokenUseCase } from '@/application/usecases/auth/refresh-token.usecase'
import { AppError } from '@/shared/utils/error-handler'
import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

describe('RefreshTokenUseCase', () => {
    let userRepository: jest.Mocked<UserRepository>
    let authService: jest.Mocked<AuthService>
    let useCase: RefreshTokenUseCase

    const validRefreshToken = 'valid-refresh-token'
    const validPayload = { userId: 'user-123', email: 'user@example.com' }
    const user = {
        id: 'user-123',
        name: 'Test User',
        email: 'user@example.com',
        isActive: true,
        createdAt: new Date('2024-01-01'),
        updatedAt: new Date('2024-01-01')
    }
    const tokens: TokenPair = { accessToken: 'new-access', refreshToken: 'new-refresh' }

    beforeEach(() => {
        userRepository = {
            findById: jest.fn(),
            findByEmail: jest.fn(),
            findByEmailWithPassword: jest.fn(),
            create: jest.fn(),
            updatePassword: jest.fn(),
        }
        authService = {
            generateTokens: jest.fn(),
            validatePassword: jest.fn(),
            hashPassword: jest.fn(),
            validateToken: jest.fn(),
            invalidateToken: jest.fn(),
        }
        useCase = new RefreshTokenUseCase(userRepository, authService)
    })

    it('should_refresh_tokens_with_valid_refresh_token_and_existing_user', async () => {
        authService.validateToken.mockResolvedValue(validPayload)
        userRepository.findById.mockResolvedValue(user)
        authService.generateTokens.mockResolvedValue(tokens)

        const result = await useCase.execute({ refreshToken: validRefreshToken })

        expect(authService.validateToken).toHaveBeenCalledWith(validRefreshToken)
        expect(userRepository.findById).toHaveBeenCalledWith(validPayload.userId)
        expect(authService.generateTokens).toHaveBeenCalledWith(user)
        expect(result.tokens).toEqual(tokens)
        expect(result.user).toEqual({
            id: user.id,
            name: user.name,
            email: user.email,
        })
    })

    it('should_return_user_info_and_tokens_on_successful_refresh', async () => {
        authService.validateToken.mockResolvedValue(validPayload)
        userRepository.findById.mockResolvedValue(user)
        authService.generateTokens.mockResolvedValue(tokens)

        const result = await useCase.execute({ refreshToken: validRefreshToken })

        expect(result).toEqual({
            tokens,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
            },
        })
    })

    it('should_call_auth_service_and_user_repository_in_correct_order', async () => {
        const callOrder: string[] = []
        authService.validateToken.mockImplementation(async () => {
            callOrder.push('validateToken')
            return validPayload
        })
        userRepository.findById.mockImplementation(async () => {
            callOrder.push('findById')
            return user
        })
        authService.generateTokens.mockImplementation(async () => {
            callOrder.push('generateTokens')
            return tokens
        })

        await useCase.execute({ refreshToken: validRefreshToken })

        expect(callOrder).toEqual(['validateToken', 'findById', 'generateTokens'])
    })

    it('should_throw_error_for_invalid_or_expired_refresh_token', async () => {
        authService.validateToken.mockResolvedValue(null)

        await expect(
            useCase.execute({ refreshToken: 'invalid-token' })
        ).rejects.toThrowError(new AppError('Invalid or expired refresh token', 401))
    })

    it('should_throw_error_when_user_not_found', async () => {
        authService.validateToken.mockResolvedValue(validPayload)
        userRepository.findById.mockResolvedValue(null)

        await expect(
            useCase.execute({ refreshToken: validRefreshToken })
        ).rejects.toThrowError(new AppError('User not found', 404))
    })

    it('should_handle_unexpected_errors_from_dependencies', async () => {
        const dependencyError = new Error('Unexpected error')
        authService.validateToken.mockRejectedValue(dependencyError)

        await expect(
            useCase.execute({ refreshToken: validRefreshToken })
        ).rejects.toThrow(dependencyError)

        // Also test if userRepository throws
        authService.validateToken.mockResolvedValue(validPayload)
        userRepository.findById.mockRejectedValue(dependencyError)

        await expect(
            useCase.execute({ refreshToken: validRefreshToken })
        ).rejects.toThrow(dependencyError)

        // Also test if generateTokens throws
        userRepository.findById.mockResolvedValue(user)
        authService.generateTokens.mockRejectedValue(dependencyError)

        await expect(
            useCase.execute({ refreshToken: validRefreshToken })
        ).rejects.toThrow(dependencyError)
    })
})