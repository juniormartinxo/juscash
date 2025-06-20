import { PrismaUserRepository } from '@/infrastructure/database/repositories/user.repository'
import { PrismaClient } from '@/generated/prisma/index'
import { CreateUserData } from '@/domain/repositories/user.repository'

jest.mock('@/generated/prisma/index')

const mockPrisma = {
    user: {
        findUnique: jest.fn(),
        create: jest.fn(),
        update: jest.fn(),
    },
}

const repository = new PrismaUserRepository(mockPrisma as unknown as PrismaClient)

describe('PrismaUserRepository', () => {
    afterEach(() => {
        jest.clearAllMocks()
    })

    it('should_return_user_entity_when_findById_given_existing_id', async () => {
        const dbUser = {
            id: 'user-1',
            name: 'Alice',
            email: 'alice@example.com',
            is_active: true,
            created_at: new Date('2023-01-01T00:00:00Z'),
            updated_at: new Date('2023-01-02T00:00:00Z'),
        }
        mockPrisma.user.findUnique.mockResolvedValue(dbUser)

        const result = await repository.findById('user-1')

        expect(mockPrisma.user.findUnique).toHaveBeenCalledWith({ where: { id: 'user-1' } })
        expect(result).toEqual({
            id: 'user-1',
            name: 'Alice',
            email: 'alice@example.com',
            isActive: true,
            createdAt: dbUser.created_at,
            updatedAt: dbUser.updated_at,
        })
    })

    it('should_create_and_return_user_entity_when_create_given_valid_data', async () => {
        const userData: CreateUserData = {
            name: 'Bob',
            email: 'bob@example.com',
            passwordHash: 'hashedpw',
        }
        const dbUser = {
            id: 'user-2',
            name: 'Bob',
            email: 'bob@example.com',
            password_hash: 'hashedpw',
            is_active: true,
            created_at: new Date('2023-02-01T00:00:00Z'),
            updated_at: new Date('2023-02-01T00:00:00Z'),
        }
        mockPrisma.user.create.mockResolvedValue(dbUser)

        const result = await repository.create(userData)

        expect(mockPrisma.user.create).toHaveBeenCalledWith({
            data: {
                name: 'Bob',
                email: 'bob@example.com',
                password_hash: 'hashedpw',
                is_password_temporary: false,
            },
        })
        expect(result).toEqual({
            id: 'user-2',
            name: 'Bob',
            email: 'bob@example.com',
            isActive: true,
            createdAt: dbUser.created_at,
            updatedAt: dbUser.updated_at,
        })
    })

    it('should_update_password_without_error_when_updatePassword_given_existing_user', async () => {
        mockPrisma.user.update.mockResolvedValue({})

        await expect(
            repository.updatePassword('user-3', 'newhash')
        ).resolves.toBeUndefined()

        expect(mockPrisma.user.update).toHaveBeenCalledWith({
            where: { id: 'user-3' },
            data: {
                password_hash: 'newhash',
                last_password_change: expect.any(Date),
            },
        })
    })

    it('should_return_null_when_findById_given_nonexistent_id', async () => {
        mockPrisma.user.findUnique.mockResolvedValue(null)

        const result = await repository.findById('nonexistent-id')

        expect(mockPrisma.user.findUnique).toHaveBeenCalledWith({ where: { id: 'nonexistent-id' } })
        expect(result).toBeNull()
    })

    it('should_throw_error_when_updatePassword_given_nonexistent_user', async () => {
        const error = new Error('User not found')
        mockPrisma.user.update.mockRejectedValue(error)

        await expect(
            repository.updatePassword('missing-id', 'irrelevant')
        ).rejects.toThrow('User not found')

        expect(mockPrisma.user.update).toHaveBeenCalledWith({
            where: { id: 'missing-id' },
            data: {
                password_hash: 'irrelevant',
                last_password_change: expect.any(Date),
            },
        })
    })

    it('should_return_null_when_findByEmail_given_nonexistent_email', async () => {
        mockPrisma.user.findUnique.mockResolvedValue(null)

        const result = await repository.findByEmail('noone@example.com')

        expect(mockPrisma.user.findUnique).toHaveBeenCalledWith({ where: { email: 'noone@example.com' } })
        expect(result).toBeNull()
    })
})