import { PrismaPublicationRepository } from '@/infrastructure/database/repositories/publication.repository'
import { PrismaClient } from '@/generated/prisma/index'
import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { CreatePublicationData, FindPublicationsParams, PublicationJsonResult } from '@/domain/repositories/publication.repository'

jest.mock('@/generated/prisma/index')

const mockPrisma = {
    publication: {
        findUnique: jest.fn(),
        findMany: jest.fn(),
        count: jest.fn(),
        update: jest.fn(),
        upsert: jest.fn(),
        create: jest.fn(),
        groupBy: jest.fn(),
        deleteMany: jest.fn(),
    },
}

const repository = new PrismaPublicationRepository((mockPrisma as unknown) as PrismaClient)

describe('PrismaPublicationRepository', () => {
    afterEach(() => {
        jest.clearAllMocks()
    })

    it('should_return_publication_when_findById_given_existing_id', async () => {
        const prismaPublication = {
            id: 'pub-1',
            process_number: '12345',
            publication_date: new Date('2023-01-01'),
            availability_date: new Date('2023-01-02'),
            authors: ['John Doe'],
            defendant: 'INSS',
            lawyers: JSON.stringify([{ name: 'Lawyer', oab: '123' }]),
            gross_value: BigInt(10000),
            net_value: BigInt(9000),
            interest_value: BigInt(1000),
            attorney_fees: BigInt(500),
            content: 'Some content',
            status: 'NOVA',
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
            extraction_metadata: JSON.stringify({ foo: 'bar' }),
            created_at: new Date('2023-01-01T10:00:00Z'),
            updated_at: new Date('2023-01-01T12:00:00Z'),
        }
        mockPrisma.publication.findUnique.mockResolvedValue(prismaPublication)

        const result = await repository.findById('pub-1')

        expect(mockPrisma.publication.findUnique).toHaveBeenCalledWith({ where: { id: 'pub-1' } })
        expect(result).toEqual({
            id: 'pub-1',
            process_number: '12345',
            publication_date: prismaPublication.publication_date,
            availability_date: prismaPublication.availability_date,
            authors: ['John Doe'],
            defendant: 'INSS',
            lawyers: [{ name: 'Lawyer', oab: '123' }],
            gross_value: '10000',
            net_value: '9000',
            interest_value: '1000',
            attorney_fees: '500',
            content: 'Some content',
            status: 'NOVA',
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
            extraction_metadata: { foo: 'bar' },
            createdAt: prismaPublication.created_at,
            updatedAt: prismaPublication.updated_at,
        })
    })

    it('should_create_publication_with_all_fields', async () => {
        const createData: CreatePublicationData = {
            process_number: '99999',
            publication_date: new Date('2023-02-01'),
            availability_date: new Date('2023-02-02'),
            authors: ['Alice', 'Bob'],
            defendant: 'Empresa XYZ',
            lawyers: [{ name: 'Advogado 1', oab: 'OAB123' }],
            gross_value: BigInt(20000),
            net_value: BigInt(18000),
            interest_value: BigInt(1500),
            attorney_fees: BigInt(500),
            content: 'Conteúdo completo',
            status: 'NOVA',
            scraping_source: 'DJE-RJ',
            caderno: '5',
            instancia: '2',
            local: 'Interior',
            parte: '2',
            extraction_metadata: { meta: 'info' },
        }
        const prismaPublication = {
            id: 'pub-2',
            process_number: createData.process_number,
            publication_date: createData.publication_date,
            availability_date: createData.availability_date,
            authors: createData.authors,
            defendant: createData.defendant,
            lawyers: JSON.stringify(createData.lawyers),
            gross_value: createData.gross_value,
            net_value: createData.net_value,
            interest_value: createData.interest_value,
            attorney_fees: createData.attorney_fees,
            content: createData.content,
            status: createData.status,
            scraping_source: createData.scraping_source,
            caderno: createData.caderno,
            instancia: createData.instancia,
            local: createData.local,
            parte: createData.parte,
            extraction_metadata: JSON.stringify(createData.extraction_metadata),
            created_at: new Date('2023-02-01T10:00:00Z'),
            updated_at: new Date('2023-02-01T12:00:00Z'),
        }
        mockPrisma.publication.create.mockResolvedValue(prismaPublication)

        const result = await repository.create(createData)

        expect(mockPrisma.publication.create).toHaveBeenCalledWith({
            data: expect.objectContaining({
                process_number: createData.process_number,
                publication_date: createData.publication_date,
                availability_date: createData.availability_date,
                authors: createData.authors,
                defendant: createData.defendant,
                gross_value: createData.gross_value,
                net_value: createData.net_value,
                interest_value: createData.interest_value,
                attorney_fees: createData.attorney_fees,
                content: createData.content,
                status: createData.status,
                scraping_source: createData.scraping_source,
                caderno: createData.caderno,
                instancia: createData.instancia,
                local: createData.local,
                parte: createData.parte,
                lawyers: JSON.stringify(createData.lawyers),
                extraction_metadata: JSON.stringify(createData.extraction_metadata),
            }),
        })
        expect(result).toEqual({
            id: 'pub-2',
            process_number: createData.process_number,
            publication_date: createData.publication_date,
            availability_date: createData.availability_date,
            authors: createData.authors,
            defendant: createData.defendant,
            lawyers: createData.lawyers,
            gross_value: createData.gross_value!.toString(),
            net_value: createData.net_value!.toString(),
            interest_value: createData.interest_value!.toString(),
            attorney_fees: createData.attorney_fees!.toString(),
            content: createData.content,
            status: createData.status,
            scraping_source: createData.scraping_source,
            caderno: createData.caderno,
            instancia: createData.instancia,
            local: createData.local,
            parte: createData.parte,
            extraction_metadata: createData.extraction_metadata,
            createdAt: prismaPublication.created_at,
            updatedAt: prismaPublication.updated_at,
        })
    })

    it('should_return_filtered_and_paginated_publications_with_findMany', async () => {
        const params: FindPublicationsParams = {
            page: 2,
            limit: 1,
            status: 'NOVA',
            startDate: new Date('2023-01-01'),
            endDate: new Date('2023-12-31'),
            searchTerm: 'Alice',
        }
        const prismaPublications = [
            {
                id: 'pub-3',
                process_number: '88888',
                publication_date: new Date('2023-03-01'),
                availability_date: new Date('2023-03-02'),
                authors: ['Alice'],
                defendant: 'Empresa ABC',
                lawyers: null,
                gross_value: BigInt(30000),
                net_value: BigInt(25000),
                interest_value: BigInt(2000),
                attorney_fees: BigInt(1000),
                content: 'Conteúdo filtrado',
                status: 'NOVA',
                scraping_source: 'DJE-SP',
                caderno: '1',
                instancia: '1',
                local: 'Capital',
                parte: '1',
                extraction_metadata: null,
                created_at: new Date('2023-03-01T10:00:00Z'),
                updated_at: new Date('2023-03-01T12:00:00Z'),
            },
        ]
        mockPrisma.publication.findMany.mockResolvedValue(prismaPublications)
        mockPrisma.publication.count.mockResolvedValue(2)

        const result = await repository.findMany(params)

        expect(mockPrisma.publication.findMany).toHaveBeenCalledWith({
            where: expect.objectContaining({
                status: 'NOVA',
                availability_date: {
                    gte: params.startDate,
                    lte: params.endDate,
                },
                OR: expect.any(Array),
            }),
            skip: 1,
            take: 1,
            orderBy: { created_at: 'desc' },
        })
        expect(mockPrisma.publication.count).toHaveBeenCalledWith({
            where: expect.any(Object),
        })
        expect(result).toEqual({
            publications: [
                {
                    id: 'pub-3',
                    process_number: '88888',
                    publication_date: prismaPublications[0]!.publication_date,
                    availability_date: prismaPublications[0]!.availability_date,
                    authors: ['Alice'],
                    defendant: 'Empresa ABC',
                    lawyers: null,
                    gross_value: '30000',
                    net_value: '25000',
                    interest_value: '2000',
                    attorney_fees: '1000',
                    content: 'Conteúdo filtrado',
                    status: 'NOVA',
                    scraping_source: 'DJE-SP',
                    caderno: '1',
                    instancia: '1',
                    local: 'Capital',
                    parte: '1',
                    extraction_metadata: null,
                    createdAt: prismaPublications[0]!.created_at,
                    updatedAt: prismaPublications[0]!.updated_at,
                },
            ],
            total: 2,
            page: 2,
            totalPages: 2,
        })
    })

    it('should_return_null_when_findById_given_nonexistent_id', async () => {
        mockPrisma.publication.findUnique.mockResolvedValue(null)

        const result = await repository.findById('nonexistent-id')

        expect(mockPrisma.publication.findUnique).toHaveBeenCalledWith({ where: { id: 'nonexistent-id' } })
        expect(result).toBeNull()
    })

    it('should_throw_error_when_create_given_duplicate_process_number', async () => {
        const createData: CreatePublicationData = {
            process_number: 'dup-123',
            availability_date: new Date(),
            authors: ['Dup'],
            content: 'Duplicate',
        }
        const error = new Error('Unique constraint failed on the fields: (`process_number`)')
        mockPrisma.publication.create.mockRejectedValue(error)

        await expect(repository.create(createData)).rejects.toThrow(
            `Publication with process number ${createData.process_number} already exists`
        )
    })

    it('should_throw_error_when_database_connection_fails', async () => {
        const dbError = new Error('Database connection lost')
        mockPrisma.publication.findUnique.mockRejectedValue(dbError)
        await expect(repository.findById('any-id')).rejects.toThrow('Failed to find publication with ID any-id')

        mockPrisma.publication.create.mockRejectedValue(dbError)
        await expect(
            repository.create({
                process_number: 'fail-1',
                availability_date: new Date(),
                authors: ['Fail'],
                content: 'Fail',
            })
        ).rejects.toThrow('Failed to create publication')

        mockPrisma.publication.findMany.mockRejectedValue(dbError)
        mockPrisma.publication.count.mockResolvedValue(0)
        await expect(repository.findMany({})).rejects.toThrow('Failed to find publications')

        mockPrisma.publication.update.mockRejectedValue(dbError)
        await expect(repository.updateStatus('id', 'NOVA')).rejects.toThrow('Failed to update publication status for ID id')

        mockPrisma.publication.upsert.mockRejectedValue(dbError)
        await expect(
            repository.upsert({
                process_number: 'upsert-1',
                availability_date: new Date(),
                authors: ['Upsert'],
                content: 'Upsert',
            })
        ).rejects.toThrow('Failed to upsert publication')

        mockPrisma.publication.groupBy.mockRejectedValue(dbError)
        mockPrisma.publication.count.mockRejectedValue(dbError)
        await expect(repository.getPublicationStats()).rejects.toThrow('Failed to get publication statistics')

        mockPrisma.publication.deleteMany.mockRejectedValue(dbError)
        await expect(repository.deleteOldPublications(10)).rejects.toThrow('Failed to delete old publications')
    })
})