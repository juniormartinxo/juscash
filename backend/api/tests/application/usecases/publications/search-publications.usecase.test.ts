import { SearchPublicationsUseCase, SearchPublicationsInput, SearchPublicationsOutput } from '@/application/usecases/publications/search-publications.usecase'
import { PublicationRepository } from '@/domain/repositories/publication.repository'
import { PublicationJsonEntity, PublicationStatus } from '@/domain/entities/publication.entity'

describe('SearchPublicationsUseCase', () => {
    let publicationRepository: jest.Mocked<PublicationRepository>
    let useCase: SearchPublicationsUseCase

    beforeEach(() => {
        publicationRepository = {
            search: jest.fn(),
            findById: jest.fn(),
            findByProcessNumber: jest.fn(),
            findMany: jest.fn(),
            updateStatus: jest.fn(),
            create: jest.fn(),
            upsert: jest.fn(),
        } as unknown as jest.Mocked<PublicationRepository>
        useCase = new SearchPublicationsUseCase(publicationRepository)
    })

    it('should_return_publications_for_valid_query', async () => {
        const mockPublications: PublicationJsonEntity[] = [
            {
                id: '1',
                process_number: '123',
                publication_date: new Date(),
                availability_date: new Date(),
                authors: ['Author A'],
                defendant: 'Defendant A',
                lawyers: null,
                gross_value: '10000',
                net_value: '9000',
                interest_value: '500',
                attorney_fees: '100',
                content: 'Some content',
                status: 'NOVA' as PublicationStatus,
                scraping_source: 'source',
                caderno: 'caderno',
                instancia: 'instancia',
                local: 'local',
                parte: 'parte',
                extraction_metadata: null,
                createdAt: new Date(),
                updatedAt: new Date(),
            },
        ]
        publicationRepository.search.mockResolvedValue(mockPublications)
        const input: SearchPublicationsInput = { query: 'valid query' }
        const result = await useCase.execute(input)
        expect(result.publications).toHaveLength(1)
        expect(result.publications[0]!.id).toBe('1')
        expect(result.query).toBe('valid query')
    })

    it('should_convert_string_monetary_fields_to_bigint', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: '2',
            process_number: '456',
            publication_date: new Date(),
            availability_date: new Date(),
            authors: ['Author B'],
            defendant: 'Defendant B',
            lawyers: null,
            gross_value: '12345678901234567890',
            net_value: '9876543210987654321',
            interest_value: '1111111111111111111',
            attorney_fees: '2222222222222222222',
            content: 'Other content',
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
        publicationRepository.search.mockResolvedValue([mockPublication])
        const input: SearchPublicationsInput = { query: 'money' }
        const result = await useCase.execute(input)
        expect(result.publications[0]!.gross_value).toBe(BigInt('12345678901234567890'))
        expect(result.publications[0]!.net_value).toBe(BigInt('9876543210987654321'))
        expect(result.publications[0]!.interest_value).toBe(BigInt('1111111111111111111'))
        expect(result.publications[0]!.attorney_fees).toBe(BigInt('2222222222222222222'))
    })

    it('should_return_correct_total_count', async () => {
        const mockPublications: PublicationJsonEntity[] = [
            {
                id: '1',
                process_number: '123',
                publication_date: new Date(),
                availability_date: new Date(),
                authors: ['Author A'],
                defendant: 'Defendant A',
                lawyers: null,
                gross_value: '10000',
                net_value: '9000',
                interest_value: '500',
                attorney_fees: '100',
                content: 'Some content',
                status: 'NOVA' as PublicationStatus,
                scraping_source: 'source',
                caderno: 'caderno',
                instancia: 'instancia',
                local: 'local',
                parte: 'parte',
                extraction_metadata: null,
                createdAt: new Date(),
                updatedAt: new Date(),
            },
            {
                id: '2',
                process_number: '456',
                publication_date: new Date(),
                availability_date: new Date(),
                authors: ['Author B'],
                defendant: 'Defendant B',
                lawyers: null,
                gross_value: '20000',
                net_value: '18000',
                interest_value: '1000',
                attorney_fees: '200',
                content: 'Other content',
                status: 'NOVA' as PublicationStatus,
                scraping_source: 'source',
                caderno: 'caderno',
                instancia: 'instancia',
                local: 'local',
                parte: 'parte',
                extraction_metadata: null,
                createdAt: new Date(),
                updatedAt: new Date(),
            },
        ]
        publicationRepository.search.mockResolvedValue(mockPublications)
        const input: SearchPublicationsInput = { query: 'count' }
        const result = await useCase.execute(input)
        expect(result.total).toBe(2)
    })

    it('should_throw_error_for_empty_query', async () => {
        const input: SearchPublicationsInput = { query: '' }
        await expect(useCase.execute(input)).rejects.toThrow('Search query must be at least 2 characters long')
    })

    it('should_throw_error_for_short_query', async () => {
        const input: SearchPublicationsInput = { query: ' a ' }
        await expect(useCase.execute(input)).rejects.toThrow('Search query must be at least 2 characters long')
    })

    it('should_return_empty_list_when_no_publications_found', async () => {
        publicationRepository.search.mockResolvedValue([])
        const input: SearchPublicationsInput = { query: 'noresults' }
        const result = await useCase.execute(input)
        expect(result.publications).toEqual([])
        expect(result.total).toBe(0)
        expect(result.query).toBe('noresults')
    })
})