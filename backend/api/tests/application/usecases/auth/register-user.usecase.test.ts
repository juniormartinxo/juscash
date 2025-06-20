import { RegisterUserUseCase } from '@/application/usecases/auth/register-user.usecase'
import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

describe('RegisterUserUseCase', () => {
    let userRepository: jest.Mocked<UserRepository>
    let authService: jest.Mocked<AuthService>
    let useCase: RegisterUserUseCase

    const validInput = {
        name: 'John Doe',
        email: 'john@example.com',
        password: 'StrongP@ssw0rd'
    }

    const createdUser = {
        id: 'user-123',
        name: 'John Doe',
        email: 'john@example.com',
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
    }

    const tokenPair: TokenPair = {
        accessToken: 'access-token',
        refreshToken: 'refresh-token'
    }

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
        useCase = new RegisterUserUseCase(userRepository, authService)
    })

    it('should_register_user_with_valid_input', async () => {
        userRepository.findByEmail.mockResolvedValue(null)
        authService.hashPassword.mockResolvedValue('hashed-password')
        userRepository.create.mockResolvedValue(createdUser)
        authService.generateTokens.mockResolvedValue(tokenPair)

        const result = await useCase.execute(validInput)

        expect(userRepository.findByEmail).toHaveBeenCalledWith(validInput.email)
        expect(authService.hashPassword).toHaveBeenCalledWith(validInput.password)
        expect(userRepository.create).toHaveBeenCalledWith({
            name: validInput.name,
            email: validInput.email,
            passwordHash: 'hashed-password'
        })
        expect(authService.generateTokens).toHaveBeenCalledWith(createdUser)
        expect(result).toEqual({
            user: createdUser,
            tokens: tokenPair
        })
    })

    it('should_hash_password_before_storing', async () => {
        userRepository.findByEmail.mockResolvedValue(null)
        authService.hashPassword.mockResolvedValue('hashed-password')
        userRepository.create.mockResolvedValue(createdUser)
        authService.generateTokens.mockResolvedValue(tokenPair)

        await useCase.execute(validInput)

        expect(authService.hashPassword).toHaveBeenCalledWith(validInput.password)
        expect(userRepository.create).toHaveBeenCalledWith(
            expect.objectContaining({ passwordHash: 'hashed-password' })
        )
    })

    it('should_generate_tokens_on_successful_registration', async () => {
        userRepository.findByEmail.mockResolvedValue(null)
        authService.hashPassword.mockResolvedValue('hashed-password')
        userRepository.create.mockResolvedValue(createdUser)
        authService.generateTokens.mockResolvedValue(tokenPair)

        const result = await useCase.execute(validInput)

        expect(authService.generateTokens).toHaveBeenCalledWith(createdUser)
        expect(result.tokens).toEqual(tokenPair)
    })

    it('should_throw_error_if_email_already_exists', async () => {
        userRepository.findByEmail.mockResolvedValue(createdUser)

        await expect(useCase.execute(validInput)).rejects.toThrow('User already exists')
        expect(userRepository.findByEmail).toHaveBeenCalledWith(validInput.email)
        expect(userRepository.create).not.toHaveBeenCalled()
    })

    it('should_throw_error_if_password_too_short', async () => {
        const input = { ...validInput, password: 'Sh0rt!' }
        userRepository.findByEmail.mockResolvedValue(null)

        await expect(useCase.execute(input)).rejects.toThrow('Password must be at least 8 characters long')
        expect(authService.hashPassword).not.toHaveBeenCalled()
        expect(userRepository.create).not.toHaveBeenCalled()
    })

    it('should_throw_error_if_password_lacks_required_characters', async () => {
        const passwords = [
            'alllowercase1!', // no uppercase
            'ALLUPPERCASE1!', // no lowercase
            'NoNumber!',      // no number
            'NoSpecial1'      // no special character
        ]
        userRepository.findByEmail.mockResolvedValue(null)

        for (const password of passwords) {
            const input = { ...validInput, password }
            await expect(useCase.execute(input)).rejects.toThrow(
                'Password must contain uppercase, lowercase, number and special character'
            )
        }
        expect(authService.hashPassword).not.toHaveBeenCalled()
        expect(userRepository.create).not.toHaveBeenCalled()
    })
})