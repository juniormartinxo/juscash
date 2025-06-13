import { AuthService } from '@/domain/services/auth.service'

export class LogoutUseCase {
  constructor(private authService: AuthService) { }

  async execute(input: LogoutInput): Promise<LogoutOutput> {
    // Invalidar token (implementar blacklist se necessário)
    await this.authService.invalidateToken(input.accessToken)

    return {
      message: 'Logged out successfully',
    }
  }
}

export interface LogoutInput {
  accessToken: string
}

export interface LogoutOutput {
  message: string
}