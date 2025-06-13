import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

export class RefreshTokenUseCase {
  constructor(
    private userRepository: UserRepository,
    private authService: AuthService
  ) { }

  async execute(input: RefreshTokenInput): Promise<RefreshTokenOutput> {
    // Validar refresh token
    const payload = await this.authService.validateToken(input.refreshToken)

    if (!payload) {
      throw new Error('Invalid refresh token')
    }

    // Verificar se usuário ainda existe e está ativo
    const user = await this.userRepository.findById(payload.userId)

    if (!user || !user.isActive) {
      throw new Error('User not found or inactive')
    }

    // Gerar novos tokens
    const tokens = await this.authService.generateTokens(user.id)

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