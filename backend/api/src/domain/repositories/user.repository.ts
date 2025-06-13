import { UserEntity } from '@/domain/entities/user.entity'

export interface UserRepository {
  findById(id: string): Promise<UserEntity | null>
  findByEmail(email: string): Promise<UserEntity | null>
  findByEmailWithPassword(email: string): Promise<UserWithPassword | null>
  create(userData: CreateUserData): Promise<UserEntity>
  updatePassword(id: string, passwordHash: string): Promise<void>
}

export interface UserWithPassword extends UserEntity {
  passwordHash: string
}

export interface CreateUserData {
  name: string
  email: string
  passwordHash: string
}
