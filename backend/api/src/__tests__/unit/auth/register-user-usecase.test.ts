import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { RegisterUserUseCase } from '@/application/usecases/auth/register-user.usecase'
import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService } from '@/domain/services/auth.service'

// Mocks
const mockUserRepository: jest.Mocked<UserRepository> = {
  findById: jest.fn(),
  findByEmail: jest.fn(),
  findByEmailWithPassword: jest.fn(),
  create: jest.fn(),
  updatePassword: jest.fn(),
}

const mockAuthService: jest.Mocked<AuthService> = {
  generateTokens: jest.fn(),
  validatePassword: jest.fn(),
  hashPassword: jest.fn(),
  validateToken: jest.fn(),
  invalidateToken: jest.fn(),
}

describe('RegisterUserUseCase', () => {
  let useCase: RegisterUserUseCase

  beforeEach(() => {
    jest.clearAllMocks()
    useCase = new RegisterUserUseCase(mockUserRepository, mockAuthService)
  })

  describe('execute', () => {
    const validInput = {
      name: 'João Silva',
      email: 'joao@exemplo.com',
      password: 'MinhaSenh@123',
    }

    it('should register a new user successfully', async () => {
      // Arrange
      mockUserRepository.findByEmail.mockResolvedValue(null)
      mockAuthService.hashPassword.mockResolvedValue('hashed-password')
      mockUserRepository.create.mockResolvedValue({
        id: 'user-id',
        name: 'João Silva',
        email: 'joao@exemplo.com',
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      })
      mockAuthService.generateTokens.mockResolvedValue({
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
      })

      // Act
      const result = await useCase.execute(validInput)

      // Assert
      expect(result).toEqual({
        user: {
          id: 'user-id',
          name: 'João Silva',
          email: 'joao@exemplo.com',
          isActive: true,
          createdAt: expect.any(Date),
          updatedAt: expect.any(Date),
        },
        tokens: {
          accessToken: 'access-token',
          refreshToken: 'refresh-token',
        },
      })

      expect(mockUserRepository.findByEmail).toHaveBeenCalledWith('joao@exemplo.com')
      expect(mockAuthService.hashPassword).toHaveBeenCalledWith('MinhaSenh@123')
      expect(mockUserRepository.create).toHaveBeenCalledWith({
        name: 'João Silva',
        email: 'joao@exemplo.com',
        passwordHash: 'hashed-password',
      })
    })

    it('should throw error if user already exists', async () => {
      // Arrange
      mockUserRepository.findByEmail.mockResolvedValue({
        id: 'existing-user',
        name: 'Existing User',
        email: 'joao@exemplo.com',
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
      })

      // Act & Assert
      await expect(useCase.execute(validInput)).rejects.toThrow('User already exists')
      expect(mockAuthService.hashPassword).not.toHaveBeenCalled()
      expect(mockUserRepository.create).not.toHaveBeenCalled()
    })

    it('should validate password strength', async () => {
      // Arrange
      mockUserRepository.findByEmail.mockResolvedValue(null)
      const weakPasswordInput = {
        ...validInput,
        password: 'weak',
      }

      // Act & Assert
      await expect(useCase.execute(weakPasswordInput)).rejects.toThrow(
        'Password must be at least 8 characters long'
      )
    })

    it('should validate password complexity', async () => {
      // Arrange
      mockUserRepository.findByEmail.mockResolvedValue(null)
      const simplePasswordInput = {
        ...validInput,
        password: 'simplepwd',
      }

      // Act & Assert
      await expect(useCase.execute(simplePasswordInput)).rejects.toThrow(
        'Password must contain uppercase, lowercase, number and special character'
      )
    })
  })
})