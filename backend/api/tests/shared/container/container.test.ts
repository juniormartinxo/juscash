import { LoginUserUseCase } from '@/application/usecases/auth/login-user.usecase'
import { LogoutUseCase } from '@/application/usecases/auth/logout.usecase'
import { RefreshTokenUseCase } from '@/application/usecases/auth/refresh-token.usecase'
import { RegisterUserUseCase } from '@/application/usecases/auth/register-user.usecase'
import { CreatePublicationUseCase } from '@/application/usecases/publications/create-publication.usecase'
import { GetPublicationByIdUseCase } from '@/application/usecases/publications/get-publication-by-id.usecase'
import { GetPublicationsUseCase } from '@/application/usecases/publications/get-publications.usecase'
import { SearchPublicationsUseCase } from '@/application/usecases/publications/search-publications.usecase'
import { UpdatePublicationStatusUseCase } from '@/application/usecases/publications/update-publication-status.usecase'
import { PrismaClient } from '@/generated/prisma/index'
import { PrismaPublicationRepository } from '@/infrastructure/database/repositories/publication.repository'
import { PrismaUserRepository } from '@/infrastructure/database/repositories/user.repository'
import { JwtAuthService } from '@/infrastructure/security/jwt-auth.service'
import { AuthController } from '@/infrastructure/web/controllers/auth.controller'
import { PublicationController } from '@/infrastructure/web/controllers/publication.controller'
import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'
import { PerformanceMiddleware } from '@/infrastructure/web/middleware/performance.middleware'
import { SecurityMiddleware } from '@/infrastructure/web/middleware/security.middleware'
import { Container } from '@/shared/container/container'

jest.mock('@/generated/prisma/index')
jest.mock('@/infrastructure/database/repositories/user.repository')
jest.mock('@/infrastructure/database/repositories/publication.repository')
jest.mock('@/infrastructure/security/jwt-auth.service')
jest.mock('@/shared/config/environment', () => ({
    config: {
        jwt: {
            accessTokenSecret: 'test-access-secret',
            refreshTokenSecret: 'test-refresh-secret',
        }
    }
}))

describe('Container', () => {
    beforeEach(() => {
        jest.clearAllMocks()
        // Reset singleton instance for each test
        // @ts-ignore
        Container.instance = undefined
    })

    it('should_initialize_all_components_with_correct_dependencies', () => {
        const container = Container.getInstance()

        expect(container.prisma).toBeInstanceOf(PrismaClient)
        expect(container.userRepository).toBeInstanceOf(PrismaUserRepository)
        expect(container.publicationRepository).toBeInstanceOf(PrismaPublicationRepository)
        expect(container.authService).toBeInstanceOf(JwtAuthService)

        expect(container.registerUserUseCase).toBeInstanceOf(RegisterUserUseCase)
        expect(container.loginUserUseCase).toBeInstanceOf(LoginUserUseCase)
        expect(container.refreshTokenUseCase).toBeInstanceOf(RefreshTokenUseCase)
        expect(container.logoutUseCase).toBeInstanceOf(LogoutUseCase)
        expect(container.getPublicationsUseCase).toBeInstanceOf(GetPublicationsUseCase)
        expect(container.getPublicationByIdUseCase).toBeInstanceOf(GetPublicationByIdUseCase)
        expect(container.updatePublicationStatusUseCase).toBeInstanceOf(UpdatePublicationStatusUseCase)
        expect(container.searchPublicationsUseCase).toBeInstanceOf(SearchPublicationsUseCase)
        expect(container.createPublicationUseCase).toBeInstanceOf(CreatePublicationUseCase)

        expect(container.authController).toBeInstanceOf(AuthController)
        expect(container.publicationController).toBeInstanceOf(PublicationController)

        expect(container.authMiddleware).toBeInstanceOf(AuthMiddleware)
        expect(container.performanceMiddleware).toBeInstanceOf(PerformanceMiddleware)
        expect(container.securityMiddleware).toBeInstanceOf(SecurityMiddleware)
    })

    it('should_return_same_instance_on_multiple_getInstance_calls', () => {
        const instance1 = Container.getInstance()
        const instance2 = Container.getInstance()
        expect(instance1).toBe(instance2)
    })

    it('should_disconnect_prisma_client_on_disconnect_call', async () => {
        const container = Container.getInstance()
        const disconnectSpy = jest.spyOn(container.prisma, '$disconnect').mockResolvedValue(undefined)
        await container.disconnect()
        expect(disconnectSpy).toHaveBeenCalled()
    })

    it('should_throw_error_if_jwt_secrets_are_missing', () => {
        jest.resetModules()
        jest.doMock('@/shared/config/environment', () => ({
            config: {
                jwt: {
                    accessTokenSecret: undefined,
                    refreshTokenSecret: undefined,
                }
            }
        }))
        // Remove singleton instance
        // @ts-ignore
        Container.instance = undefined
        // Remove previous mocks to force reload
        const { Container: FreshContainer } = require('@/shared/container/container')
        expect(() => {
            FreshContainer.getInstance()
        }).toThrow()
    })

    it('should_handle_prisma_client_initialization_failure', () => {
        (PrismaClient as jest.Mock).mockImplementation(() => {
            throw new Error('DB connection failed')
        })
        // Remove singleton instance
        // @ts-ignore
        Container.instance = undefined
        expect(() => {
            Container.getInstance()
        }).toThrow('DB connection failed')
    })

    it('should_prevent_direct_constructor_instantiation', () => {
        // @ts-ignore
        expect(() => new Container()).toThrow()
    })
})