import { GetPublicationsUseCase } from '@/application/usecases/publications/get-publications.usecase'
import { PublicationRepository } from '@/domain/repositories/publication.repository'
import { PublicationJsonEntity, PublicationEntity, PublicationStatus } from '@/domain/entities/publication.entity'

describe('GetPublicationsUseCase', () => {
    let publicationRepository: jest.Mocked<PublicationRepository>
    let useCase: GetPublicationsUseCase

    beforeEach(() => {
        publicationRepository = {
            findById: jest.fn(),
            findByProcessNumber: jest.fn(),
            findMany: jest.fn(),
            updateStatus: jest.fn(),
            search: jest.fn(),
            create: jest.fn(),
            upsert: jest.fn(),
        }
        useCase = new GetPublicationsUseCase(publicationRepository)
    })

    it('shouldReturnDefaultPaginatedPublications', async () => {
        const mockResult = {
            publications: [
                {
                    id: '1',
                    process_number: '123',
                    publication_date: new Date(),
                    availability_date: new Date(),
                    authors: ['Author'],
                    defendant: 'Defendant',
                    lawyers: null,
                    gross_value: '10000',
                    net_value: '9000',
                    interest_value: '1000',
                    attorney_fees: '500',
                    content: 'Content',
                    status: 'NOVA' as PublicationStatus,
                    scraping_source: 'source',
                    caderno: 'caderno',
                    instancia: 'instancia',
                    local: 'local',
                    parte: 'parte',
                    extraction_metadata: null,
                    createdAt: new Date(),
                    updatedAt: new Date(),
                } as PublicationJsonEntity,
            ],
            page: 1,
            totalPages: 1,
            total: 1,
        }
        publicationRepository.findMany.mockResolvedValue(mockResult)

        const result = await useCase.execute({})

        expect(publicationRepository.findMany).toHaveBeenCalledWith({
            page: 1,
            limit: 30,
            searchTerm: '',
        })
        expect(result.publications).toHaveLength(1)
        expect(result.pagination).toEqual({
            current: 1,
            total: 1,
            count: 1,
            perPage: 30,
        })
    })

    it('shouldFilterPublicationsByStatusAndDateRange', async () => {
        const mockResult = {
            publications: [],
            page: 2,
            totalPages: 5,
            total: 10,
        }
        publicationRepository.findMany.mockResolvedValue(mockResult)

        const input = {
            page: 2,
            limit: 5,
            status: 'NOVA' as PublicationStatus,
            startDate: new Date('2023-01-01'),
            endDate: new Date('2023-12-31'),
            searchTerm: 'test',
        }

        await useCase.execute(input)

        expect(publicationRepository.findMany).toHaveBeenCalledWith({
            page: 2,
            limit: 5,
            searchTerm: 'test',
            status: 'NOVA',
            startDate: input.startDate,
            endDate: input.endDate,
        })
    })

    it('shouldConvertStringMonetaryFieldsToBigInt', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: '1',
            process_number: '123',
            publication_date: new Date(),
            availability_date: new Date(),
            authors: ['Author'],
            defendant: 'Defendant',
            lawyers: null,
            gross_value: '10000',
            net_value: '9000',
            interest_value: '1000',
            attorney_fees: '500',
            content: 'Content',
            status: 'NOVA' as PublicationStatus,
            scraping_source: 'source',
            caderno: 'caderno',
            instancia: 'instancia',
            local: 'local',
            parte: 'parte',
            extraction_metadata: null,
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        publicationRepository.findMany.mockResolvedValue({
            publications: [mockPublication],
            page: 1,
            totalPages: 1,
            total: 1,
        })

        const result = await useCase.execute({})

        expect(result.publications[0]?.gross_value).toBe(BigInt('10000'))
        expect(result.publications[0]?.net_value).toBe(BigInt('9000'))
        expect(result.publications[0]?.interest_value).toBe(BigInt('1000'))
        expect(result.publications[0]?.attorney_fees).toBe(BigInt('500'))
    })

    it('shouldHandleNoMatchingPublications', async () => {
        publicationRepository.findMany.mockResolvedValue({
            publications: [],
            page: 1,
            totalPages: 0,
            total: 0,
        })

        const result = await useCase.execute({ searchTerm: 'no-match' })

        expect(result.publications).toEqual([])
        expect(result.pagination).toEqual({
            current: 1,
            total: 0,
            count: 0,
            perPage: 30,
        })
    })

    it('shouldHandleNullOrMissingMonetaryFields', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: '2',
            process_number: '456',
            publication_date: new Date(),
            availability_date: new Date(),
            authors: ['Author'],
            defendant: 'Defendant',
            lawyers: null,
            gross_value: null,
            net_value: null,
            interest_value: null,
            attorney_fees: null,
            content: 'Content',
            status: 'NOVA' as PublicationStatus,
            scraping_source: 'source',
            caderno: 'caderno',
            instancia: 'instancia',
            local: 'local',
            parte: 'parte',
            extraction_metadata: null,
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        publicationRepository.findMany.mockResolvedValue({
            publications: [mockPublication],
            page: 1,
            totalPages: 1,
            total: 1,
        })

        const result = await useCase.execute({})

        expect(result.publications[0]?.gross_value).toBeNull()
        expect(result.publications[0]?.net_value).toBeNull()
        expect(result.publications[0]?.interest_value).toBeNull()
        expect(result.publications[0]?.attorney_fees).toBeNull()
    })

    it('shouldPropagateRepositoryErrors', async () => {
        const error = new Error('Repository failure')
        publicationRepository.findMany.mockRejectedValue(error)

        await expect(useCase.execute({})).rejects.toThrow('Repository failure')
    })
})