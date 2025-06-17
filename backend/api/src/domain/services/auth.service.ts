export interface TokenPair {
  accessToken: string
  refreshToken: string
}

export interface TokenPayload {
  userId: string
  email: string
}

export interface AuthService {
  generateTokens(user: { id: string, email: string }): Promise<TokenPair>
  validatePassword(password: string, hash: string): Promise<boolean>
  hashPassword(password: string): Promise<string>
  validateToken(token: string): Promise<TokenPayload | null>
  invalidateToken(token: string): Promise<void>
}
