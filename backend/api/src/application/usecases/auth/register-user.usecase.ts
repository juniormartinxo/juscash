import { UserRepository } from '@/domain/repositories/user.repository'
import { AuthService, TokenPair } from '@/domain/services/auth.service'

export class RegisterUserUseCase {
  constructor(
    private userRepository: UserRepository,
    private authService: AuthService
  ) { }

  async execute(input: RegisterUserInput): Promise<RegisterUserOutput> {
    // Validar se usuário já existe
    const existingUser = await this.userRepository.findByEmail(input.email)
    if (existingUser) {
      throw new Error('User already exists')
    }

    // Validar senha
    this.validatePassword(input.password)


    // Hash da senha
    const passwordHash = await this.authService.hashPassword(input.password)

    // Criar usuário
    const user = await this.userRepository.create({
      name: input.name,
      email: input.email,
      passwordHash,
    })

    // Gerar tokens
    const tokens = await this.authService.generateTokens(user.id)

    return {
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
      tokens,
    }
  }

  private validatePassword(password: string): void {
    const minLength = 8
    const hasUpperCase = /[A-Z]/.test(password)
    const hasLowerCase = /[a-z]/.test(password)
    const hasNumbers = /\d/.test(password)
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password)

    if (password.length < minLength) {
      throw new Error('Password must be at least 8 characters long')
    }

    if (!hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecialChar) {
      throw new Error('Password must contain uppercase, lowercase, number and special character')
    }
  }
}

export interface RegisterUserInput {
  name: string
  email: string
  password: string
}

export interface RegisterUserOutput {
  user: {
    id: string
    name: string
    email: string
  }
  tokens: TokenPair
}
