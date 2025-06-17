import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

export class LoginUserUseCase {
  constructor(
    private userRepository: UserRepository,
    private authService: AuthService
  ) { }

  async execute(input: LoginUserInput): Promise<LoginUserOutput> {
    // Buscar usuário com senha
    const user = await this.userRepository.findByEmailWithPassword(input.email)

    if (!user) {
      throw new Error('Invalid credentials')
    }

    // Validar senha
    const isValidPassword = await this.authService.validatePassword(
      input.password,
      user.passwordHash
    )

    if (!isValidPassword) {
      throw new Error('Invalid credentials')
    }

    // Gerar tokens
    const tokens = await this.authService.generateTokens(user)

    return {
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
      tokens,
    }
  }
}

export interface LoginUserInput {
  email: string
  password: string
}

export interface LoginUserOutput {
  user: {
    id: string
    name: string
    email: string
  }
  tokens: TokenPair
}
