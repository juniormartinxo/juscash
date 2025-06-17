import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'
import { AppError } from '@/shared/utils/error-handler'

export class RefreshTokenUseCase {
  constructor(
    private userRepository: UserRepository,
    private authService: AuthService
  ) { }

  async execute(input: RefreshTokenInput): Promise<RefreshTokenOutput> {
    // Validar refresh token
    const payload = await this.authService.validateToken(input.refreshToken)

    if (!payload) {
      throw new AppError('Invalid or expired refresh token', 401)
    }

    const user = await this.userRepository.findById(payload.userId)

    if (!user) {
      throw new AppError('User not found', 404)
    }

    // Gerar novos tokens
    const tokens = await this.authService.generateTokens(user)

    return {
      tokens,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
    }
  }
}

export interface RefreshTokenInput {
  refreshToken: string
}

export interface RefreshTokenOutput {
  tokens: TokenPair
  user: {
    id: string
    name: string
    email: string
  }
}