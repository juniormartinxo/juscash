import { UserEntity } from '@/domain/entities/user.entity'
import { CreateUserData, UserRepository, UserWithPassword } from '@/domain/repositories/user.repository'
import { PrismaClient } from '@/generated/prisma/index'

export class PrismaUserRepository implements UserRepository {
  constructor(private prisma: PrismaClient) { }

  async findById(id: string): Promise<UserEntity | null> {
    const user = await this.prisma.user.findUnique({
      where: { id },
    })

    return user ? this.toDomain(user) : null
  }

  async findByEmail(email: string): Promise<UserEntity | null> {
    const user = await this.prisma.user.findUnique({
      where: { email },
    })

    return user ? this.toDomain(user) : null
  }

  async findByEmailWithPassword(email: string): Promise<UserWithPassword | null> {
    const user = await this.prisma.user.findUnique({
      where: { email },
    })

    return user ? this.toDomainWithPassword(user) : null
  }

  async create(userData: CreateUserData): Promise<UserEntity> {
    const user = await this.prisma.user.create({
      data: {
        name: userData.name,
        email: userData.email,
        password_hash: userData.passwordHash,
        is_password_temporary: false,
      },
    })

    return this.toDomain(user)
  }

  async updatePassword(id: string, passwordHash: string): Promise<void> {
    await this.prisma.user.update({
      where: { id },
      data: {
        password_hash: passwordHash,
        last_password_change: new Date(),
      },
    })
  }

  private toDomain(user: any): UserEntity {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      isActive: user.is_active,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
    }
  }

  private toDomainWithPassword(user: any): UserWithPassword {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      isActive: user.is_active,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
      passwordHash: user.password_hash,
    }
  }
}
