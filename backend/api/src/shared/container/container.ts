import { JwtAuthService } from '@/infrastructure/security/jwt-auth.service'
import { PerformanceMiddleware } from '@/infrastructure/web/middleware/performance.middleware'
import { SecurityMiddleware } from '@/infrastructure/web/middleware/security.middleware'
import { config } from '@/shared/config/environment'
import { RegisterUserUseCase } from '@/application/usecases/auth/register-user.usecase'
import { LoginUserUseCase } from '@/application/usecases/auth/login-user.usecase'
import { RefreshTokenUseCase } from '@/application/usecases/auth/refresh-token.usecase'
import { LogoutUseCase } from '@/application/usecases/auth/logout.usecase'
import { GetPublicationsUseCase } from '@/application/usecases/publications/get-publications.usecase'
import { GetPublicationByIdUseCase } from '@/application/usecases/publications/get-publication-by-id.usecase'
import { UpdatePublicationStatusUseCase } from '@/application/usecases/publications/update-publication-status.usecase'
import { SearchPublicationsUseCase } from '@/application/usecases/publications/search-publications.usecase'
import { CreatePublicationUseCase } from '@/application/usecases/publications/create-publication.usecase'
import { PrismaClient } from '@/generated/prisma/index'
import { PrismaUserRepository } from '@/infrastructure/database/repositories/user.repository'
import { PrismaPublicationRepository } from '@/infrastructure/database/repositories/publication.repository'
import { AuthController } from '@/infrastructure/web/controllers/auth.controller'
import { PublicationController } from '@/infrastructure/web/controllers/publication.controller'
import { AuthMiddleware } from '@/infrastructure/web/middleware/auth.middleware'

export class Container {
  private static instance: Container

  // Infrastructure
  public readonly prisma: PrismaClient
  public readonly userRepository: PrismaUserRepository
  public readonly publicationRepository: PrismaPublicationRepository
  public readonly authService: JwtAuthService

  // Use Cases
  public readonly registerUserUseCase: RegisterUserUseCase
  public readonly loginUserUseCase: LoginUserUseCase
  public readonly refreshTokenUseCase: RefreshTokenUseCase
  public readonly logoutUseCase: LogoutUseCase
  public readonly getPublicationsUseCase: GetPublicationsUseCase
  public readonly getPublicationByIdUseCase: GetPublicationByIdUseCase
  public readonly updatePublicationStatusUseCase: UpdatePublicationStatusUseCase
  public readonly searchPublicationsUseCase: SearchPublicationsUseCase
  public readonly createPublicationUseCase: CreatePublicationUseCase

  // Controllers
  public readonly authController: AuthController
  public readonly publicationController: PublicationController

  // Middleware
  public readonly authMiddleware: AuthMiddleware
  public readonly performanceMiddleware: PerformanceMiddleware
  public readonly securityMiddleware: SecurityMiddleware

  private constructor() {
    // Infrastructure
    this.prisma = new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['query', 'info', 'warn', 'error'] : ['error'],
    })

    this.userRepository = new PrismaUserRepository(this.prisma)
    this.publicationRepository = new PrismaPublicationRepository(this.prisma)
    this.authService = new JwtAuthService(
      config.jwt.accessTokenSecret,
      config.jwt.refreshTokenSecret
    )

    // Use Cases
    this.registerUserUseCase = new RegisterUserUseCase(
      this.userRepository,
      this.authService
    )
    this.loginUserUseCase = new LoginUserUseCase(
      this.userRepository,
      this.authService
    )
    this.refreshTokenUseCase = new RefreshTokenUseCase(
      this.userRepository,
      this.authService
    )
    this.logoutUseCase = new LogoutUseCase(this.authService)

    this.getPublicationsUseCase = new GetPublicationsUseCase(
      this.publicationRepository
    )
    this.getPublicationByIdUseCase = new GetPublicationByIdUseCase(
      this.publicationRepository
    )
    this.updatePublicationStatusUseCase = new UpdatePublicationStatusUseCase(
      this.publicationRepository
    )
    this.searchPublicationsUseCase = new SearchPublicationsUseCase(
      this.publicationRepository
    )
    this.createPublicationUseCase = new CreatePublicationUseCase(
      this.publicationRepository
    )

    // Controllers
    this.authController = new AuthController(
      this.registerUserUseCase,
      this.loginUserUseCase,
      this.refreshTokenUseCase,
      this.logoutUseCase
    )
    this.publicationController = new PublicationController(
      this.getPublicationsUseCase,
      this.getPublicationByIdUseCase,
      this.updatePublicationStatusUseCase,
      this.searchPublicationsUseCase,
      this.createPublicationUseCase
    )

    // Middleware
    this.authMiddleware = new AuthMiddleware(this.authService)
    this.performanceMiddleware = new PerformanceMiddleware()
    this.securityMiddleware = new SecurityMiddleware()
  }

  public static getInstance(): Container {
    if (!Container.instance) {
      Container.instance = new Container()
    }
    return Container.instance
  }

  public async disconnect(): Promise<void> {
    await this.prisma.$disconnect()
  }
}
