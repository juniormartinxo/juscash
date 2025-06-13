import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
import { AuthService, TokenPair, TokenPayload } from '@/domain/services/auth.service'

export class JwtAuthService implements AuthService {
  private readonly accessTokenSecret: string
  private readonly refreshTokenSecret: string
  private readonly accessTokenExpiry = '15m';
  private readonly refreshTokenExpiry = '7d';
  private readonly blacklistedTokens = new Set<string>(); // Simple in-memory blacklist

  constructor(accessTokenSecret: string, refreshTokenSecret: string) {
    this.accessTokenSecret = accessTokenSecret
    this.refreshTokenSecret = refreshTokenSecret
  }

  async generateTokens(userId: string): Promise<TokenPair> {
    const payload = { userId }

    const accessToken = jwt.sign(payload, this.accessTokenSecret, {
      expiresIn: this.accessTokenExpiry,
      issuer: 'dje-api',
      audience: 'dje-client',
    })

    const refreshToken = jwt.sign(payload, this.refreshTokenSecret, {
      expiresIn: this.refreshTokenExpiry,
      issuer: 'dje-api',
      audience: 'dje-client',
    })

    return { accessToken, refreshToken }
  }

  async validatePassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash)
  }

  async hashPassword(password: string): Promise<string> {
    const saltRounds = 12
    return bcrypt.hash(password, saltRounds)
  }

  async validateToken(token: string): Promise<TokenPayload | null> {
    try {
      // Check if token is blacklisted
      if (this.blacklistedTokens.has(token)) {
        return null
      }

      const decoded = jwt.verify(token, this.accessTokenSecret, {
        issuer: 'dje-api',
        audience: 'dje-client',
      }) as any

      return {
        userId: decoded.userId,
        email: decoded.email,
      }
    } catch (error) {
      return null
    }
  }

  async invalidateToken(token: string): Promise<void> {
    this.blacklistedTokens.add(token)

    // Clean up old tokens periodically (simple implementation)
    if (this.blacklistedTokens.size > 10000) {
      this.blacklistedTokens.clear()
    }
  }
}
