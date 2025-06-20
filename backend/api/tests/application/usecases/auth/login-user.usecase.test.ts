import { LoginUserUseCase, LoginUserInput, LoginUserOutput } from '@/application/usecases/auth/login-user.usecase'
import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

jest.mock('@/domain/repositories/user.repository')
jest.mock('@/domain/services/auth.service')

const mockUser = {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com',
    passwordHash: 'hashed-password',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
}

const mockTokens: TokenPair = {
    accessToken: 'access-token',
    refreshToken: 'refresh-token'
}

describe('LoginUserUseCase', () => {
    let userRepository: jest.Mocked<UserRepository>
    let authService: jest.Mocked<AuthService>
    let useCase: LoginUserUseCase

    beforeEach(() => {
        userRepository = {
            findById: jest.fn(),
            findByEmail: jest.fn(),
            findByEmailWithPassword: jest.fn(),
            create: jest.fn(),
            updatePassword: jest.fn()
        }
        authService = {
            generateTokens: jest.fn(),
            validatePassword: jest.fn(),
            hashPassword: jest.fn(),
            validateToken: jest.fn(),
            invalidateToken: jest.fn()
        }
        useCase = new LoginUserUseCase(userRepository, authService)
    })

    it('should_return_user_and_tokens_when_credentials_are_valid', async () => {
        userRepository.findByEmailWithPassword.mockResolvedValue(mockUser)
        authService.validatePassword.mockResolvedValue(true)
        authService.generateTokens.mockResolvedValue(mockTokens)

        const input: LoginUserInput = { email: mockUser.email, password: 'password123' }
        const result = await useCase.execute(input)

        expect(result).toEqual({
            user: {
                id: mockUser.id,
                name: mockUser.name,
                email: mockUser.email
            },
            tokens: mockTokens
        })
        expect(userRepository.findByEmailWithPassword).toHaveBeenCalledWith(mockUser.email)
        expect(authService.validatePassword).toHaveBeenCalledWith('password123', mockUser.passwordHash)
        expect(authService.generateTokens).toHaveBeenCalledWith(mockUser)
    })

    it('should_generate_access_and_refresh_tokens_on_successful_login', async () => {
        userRepository.findByEmailWithPassword.mockResolvedValue(mockUser)
        authService.validatePassword.mockResolvedValue(true)
        authService.generateTokens.mockResolvedValue(mockTokens)

        const input: LoginUserInput = { email: mockUser.email, password: 'password123' }
        const result = await useCase.execute(input)

        expect(result.tokens.accessToken).toBe('access-token')
        expect(result.tokens.refreshToken).toBe('refresh-token')
    })

    it('should_return_correct_user_data_on_successful_login', async () => {
        userRepository.findByEmailWithPassword.mockResolvedValue(mockUser)
        authService.validatePassword.mockResolvedValue(true)
        authService.generateTokens.mockResolvedValue(mockTokens)

        const input: LoginUserInput = { email: mockUser.email, password: 'password123' }
        const result = await useCase.execute(input)

        expect(result.user).toEqual({
            id: mockUser.id,
            name: mockUser.name,
            email: mockUser.email
        })
    })

    it('should_throw_error_when_email_does_not_exist', async () => {
        userRepository.findByEmailWithPassword.mockResolvedValue(null)
        const input: LoginUserInput = { email: 'notfound@example.com', password: 'password123' }

        await expect(useCase.execute(input)).rejects.toThrow('Invalid credentials')
        expect(userRepository.findByEmailWithPassword).toHaveBeenCalledWith('notfound@example.com')
    })

    it('should_throw_error_when_password_is_incorrect', async () => {
        userRepository.findByEmailWithPassword.mockResolvedValue(mockUser)
        authService.validatePassword.mockResolvedValue(false)
        const input: LoginUserInput = { email: mockUser.email, password: 'wrongpassword' }

        await expect(useCase.execute(input)).rejects.toThrow('Invalid credentials')
        expect(authService.validatePassword).toHaveBeenCalledWith('wrongpassword', mockUser.passwordHash)
    })

    it('should_handle_errors_from_dependencies_during_login', async () => {
        userRepository.findByEmailWithPassword.mockRejectedValue(new Error('DB error'))
        const input: LoginUserInput = { email: mockUser.email, password: 'password123' }

        await expect(useCase.execute(input)).rejects.toThrow('DB error')

        userRepository.findByEmailWithPassword.mockResolvedValue(mockUser)
        authService.validatePassword.mockRejectedValue(new Error('Hash error'))

        await expect(useCase.execute(input)).rejects.toThrow('Hash error')

        authService.validatePassword.mockResolvedValue(true)
        authService.generateTokens.mockRejectedValue(new Error('Token error'))

        await expect(useCase.execute(input)).rejects.toThrow('Token error')
    })
})