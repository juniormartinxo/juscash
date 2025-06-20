import { GetPublicationByIdUseCase, PublicationNotFoundError, GetPublicationByIdInput } from '@/application/usecases/publications/get-publication-by-id.usecase'
import { PublicationRepository } from '@/domain/repositories/publication.repository'
import { PublicationJsonEntity, PublicationEntity } from '@/domain/entities/publication.entity'

describe('GetPublicationByIdUseCase', () => {
    let publicationRepository: jest.Mocked<PublicationRepository>
    let useCase: GetPublicationByIdUseCase

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
        useCase = new GetPublicationByIdUseCase(publicationRepository)
    })

    it('should_return_publication_when_id_exists', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: 'pub-1',
            process_number: '12345',
            publication_date: new Date('2023-01-01'),
            availability_date: new Date('2023-01-02'),
            authors: ['Author A'],
            defendant: 'Defendant X',
            lawyers: [{ name: 'Lawyer Y', oab: 'OAB123' }],
            gross_value: '10000',
            net_value: '9000',
            interest_value: '500',
            attorney_fees: '100',
            content: 'Some content',
            status: 'ACTIVE' as any,
            scraping_source: 'source',
            caderno: 'caderno',
            instancia: 'instancia',
            local: 'local',
            parte: 'parte',
            extraction_metadata: null,
            createdAt: new Date('2023-01-01'),
            updatedAt: new Date('2023-01-02'),
        }
        publicationRepository.findById.mockResolvedValue(mockPublication)

        const input: GetPublicationByIdInput = { id: 'pub-1' }
        const result = await useCase.execute(input)

        expect(result.publication.id).toBe('pub-1')
        expect(result.publication.process_number).toBe('12345')
        expect(result.publication.gross_value).toBe(BigInt('10000'))
    })

    it('should_convert_string_monetary_fields_to_bigint', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: 'pub-2',
            process_number: '54321',
            publication_date: null,
            availability_date: new Date('2023-02-01'),
            authors: [],
            defendant: '',
            lawyers: null,
            gross_value: '12345678901234567890',
            net_value: '98765432109876543210',
            interest_value: '11111111111111111111',
            attorney_fees: '22222222222222222222',
            content: '',
            status: 'ACTIVE' as any,
            scraping_source: '',
            caderno: '',
            instancia: '',
            local: '',
            parte: '',
            extraction_metadata: null,
            createdAt: new Date('2023-02-01'),
            updatedAt: new Date('2023-02-02'),
        }
        publicationRepository.findById.mockResolvedValue(mockPublication)

        const input: GetPublicationByIdInput = { id: 'pub-2' }
        const result = await useCase.execute(input)

        expect(result.publication.gross_value).toBe(BigInt('12345678901234567890'))
        expect(result.publication.net_value).toBe(BigInt('98765432109876543210'))
        expect(result.publication.interest_value).toBe(BigInt('11111111111111111111'))
        expect(result.publication.attorney_fees).toBe(BigInt('22222222222222222222'))
    })

    it('should_return_all_fields_in_publication_entity', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: 'pub-3',
            process_number: '99999',
            publication_date: null,
            availability_date: new Date('2023-03-01'),
            authors: ['A', 'B'],
            defendant: 'Defendant Y',
            lawyers: [{ name: 'Lawyer Z', oab: 'OAB999' }],
            gross_value: '100',
            net_value: '90',
            interest_value: '5',
            attorney_fees: '1',
            content: 'Full content',
            status: 'ARCHIVED' as any,
            scraping_source: 'scraper',
            caderno: 'cadernoX',
            instancia: 'instanciaY',
            local: 'localZ',
            parte: 'parteW',
            extraction_metadata: { foo: 'bar' },
            createdAt: new Date('2023-03-01'),
            updatedAt: new Date('2023-03-02'),
        }
        publicationRepository.findById.mockResolvedValue(mockPublication)

        const input: GetPublicationByIdInput = { id: 'pub-3' }
        const result = await useCase.execute(input)

        expect(result.publication).toMatchObject({
            id: 'pub-3',
            process_number: '99999',
            publication_date: null,
            availability_date: mockPublication.availability_date,
            authors: ['A', 'B'],
            defendant: 'Defendant Y',
            lawyers: [{ name: 'Lawyer Z', oab: 'OAB999' }],
            gross_value: BigInt('100'),
            net_value: BigInt('90'),
            interest_value: BigInt('5'),
            attorney_fees: BigInt('1'),
            content: 'Full content',
            status: 'ARCHIVED',
            scraping_source: 'scraper',
            caderno: 'cadernoX',
            instancia: 'instanciaY',
            local: 'localZ',
            parte: 'parteW',
            extraction_metadata: { foo: 'bar' },
            createdAt: mockPublication.createdAt,
            updatedAt: mockPublication.updatedAt,
        })
    })

    it('should_throw_error_when_publication_not_found', async () => {
        publicationRepository.findById.mockResolvedValue(null)
        const input: GetPublicationByIdInput = { id: 'non-existent-id' }
        await expect(useCase.execute(input)).rejects.toThrow(PublicationNotFoundError)
        await expect(useCase.execute(input)).rejects.toThrow('Publication not found')
    })

    it('should_handle_null_monetary_fields', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: 'pub-4',
            process_number: '88888',
            publication_date: null,
            availability_date: new Date('2023-04-01'),
            authors: [],
            defendant: '',
            lawyers: null,
            gross_value: null,
            net_value: null,
            interest_value: null,
            attorney_fees: null,
            content: '',
            status: 'ACTIVE' as any,
            scraping_source: '',
            caderno: '',
            instancia: '',
            local: '',
            parte: '',
            extraction_metadata: null,
            createdAt: new Date('2023-04-01'),
            updatedAt: new Date('2023-04-02'),
        }
        publicationRepository.findById.mockResolvedValue(mockPublication)

        const input: GetPublicationByIdInput = { id: 'pub-4' }
        const result = await useCase.execute(input)

        expect(result.publication.gross_value).toBeNull()
        expect(result.publication.net_value).toBeNull()
        expect(result.publication.interest_value).toBeNull()
        expect(result.publication.attorney_fees).toBeNull()
    })

    it('should_handle_invalid_string_in_monetary_fields', async () => {
        const mockPublication: PublicationJsonEntity = {
            id: 'pub-5',
            process_number: '77777',
            publication_date: null,
            availability_date: new Date('2023-05-01'),
            authors: [],
            defendant: '',
            lawyers: null,
            gross_value: 'not-a-number',
            net_value: '9000',
            interest_value: 'invalid',
            attorney_fees: '100',
            content: '',
            status: 'ACTIVE' as any,
            scraping_source: '',
            caderno: '',
            instancia: '',
            local: '',
            parte: '',
            extraction_metadata: null,
            createdAt: new Date('2023-05-01'),
            updatedAt: new Date('2023-05-02'),
        }
        publicationRepository.findById.mockResolvedValue(mockPublication)

        const input: GetPublicationByIdInput = { id: 'pub-5' }
        await expect(useCase.execute(input)).rejects.toThrow()
    })
})