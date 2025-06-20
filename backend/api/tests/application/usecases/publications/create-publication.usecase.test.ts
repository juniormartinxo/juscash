import { CreatePublicationUseCase } from '@/application/usecases/publications/create-publication.usecase'
import { PublicationRepository } from '@/domain/repositories/publication.repository'
import { PublicationValidation, PublicationEntity, PublicationJsonEntity, PublicationStatus } from '@/domain/entities/publication.entity'
import { ValidationError, PublicationCreationError } from '@/application/usecases/publications/create-publication.usecase'

jest.mock('@/domain/entities/publication.entity', () => {
    const actual = jest.requireActual('@/domain/entities/publication.entity')
    return {
        ...actual,
        PublicationValidation: {
            ...actual.PublicationValidation,
            areValidLawyers: jest.fn(),
            areValidMonetaryValues: jest.fn(),
        }
    }
})

describe('CreatePublicationUseCase', () => {
    let publicationRepository: jest.Mocked<PublicationRepository>
    let useCase: CreatePublicationUseCase

    beforeEach(() => {
        publicationRepository = {
            upsert: jest.fn(),
            findById: jest.fn(),
            findByProcessNumber: jest.fn(),
            findMany: jest.fn(),
            updateStatus: jest.fn(),
            search: jest.fn(),
            create: jest.fn(),
        } as any
        useCase = new CreatePublicationUseCase(publicationRepository)
        jest.clearAllMocks()
    })

    it('should_create_publication_with_all_fields', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const input = {
            process_number: '1234567-89.2020.1.23.4567',
            publication_date: new Date('2023-01-01'),
            availability_date: new Date('2023-01-02'),
            authors: ['John Doe'],
            defendant: 'Some Defendant',
            lawyers: [{ name: 'Lawyer Name', oab: '12345' }],
            gross_value: BigInt(10000),
            net_value: BigInt(9000),
            interest_value: BigInt(500),
            attorney_fees: BigInt(100),
            content: 'This is a valid publication content.',
            status: 'NOVA' as PublicationStatus,
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
            extraction_metadata: { foo: 'bar' }
        }
        const publicationJson: PublicationJsonEntity = {
            ...input,
            id: 'pub-1',
            gross_value: input.gross_value!.toString(),
            net_value: input.net_value!.toString(),
            interest_value: input.interest_value!.toString(),
            attorney_fees: input.attorney_fees!.toString(),
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        publicationRepository.upsert.mockResolvedValue(publicationJson)

        const result = await useCase.execute(input)

        expect(publicationRepository.upsert).toHaveBeenCalledWith(expect.objectContaining({
            process_number: input.process_number,
            publication_date: input.publication_date,
            availability_date: input.availability_date,
            authors: input.authors,
            defendant: input.defendant,
            lawyers: input.lawyers,
            gross_value: input.gross_value,
            net_value: input.net_value,
            interest_value: input.interest_value,
            attorney_fees: input.attorney_fees,
            content: input.content,
            status: input.status,
            scraping_source: input.scraping_source,
            caderno: input.caderno,
            instancia: input.instancia,
            local: input.local,
            parte: input.parte,
            extraction_metadata: input.extraction_metadata,
        }))
        expect(result.publication).toMatchObject({
            ...publicationJson,
            gross_value: BigInt(publicationJson.gross_value!),
            net_value: BigInt(publicationJson.net_value!),
            interest_value: BigInt(publicationJson.interest_value!),
            attorney_fees: BigInt(publicationJson.attorney_fees!),
        })
    })

    it('should_create_publication_with_required_fields_and_defaults', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const input = {
            process_number: '1234567-89.2020.1.23.4567',
            availability_date: new Date('2023-01-02'),
            authors: ['Jane Doe'],
            content: 'This is a valid publication content.',
        }
        const publicationJson: PublicationJsonEntity = {
            ...input,
            id: 'pub-2',
            defendant: 'Instituto Nacional do Seguro Social - INSS',
            status: 'NOVA' as PublicationStatus,
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
            gross_value: null,
            net_value: null,
            interest_value: null,
            attorney_fees: null,
            lawyers: null,
            publication_date: null,
            extraction_metadata: null,
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        publicationRepository.upsert.mockResolvedValue(publicationJson)

        const result = await useCase.execute(input)

        expect(publicationRepository.upsert).toHaveBeenCalledWith(expect.objectContaining({
            process_number: input.process_number,
            availability_date: input.availability_date,
            authors: input.authors,
            content: input.content,
            defendant: 'Instituto Nacional do Seguro Social - INSS',
            status: 'NOVA',
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
        }))
        expect(result.publication).toMatchObject({
            ...publicationJson,
            gross_value: null,
            net_value: null,
            interest_value: null,
            attorney_fees: null,
        })
    })

    it('should_create_publication_with_valid_lawyers_and_monetary_values', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const input = {
            process_number: '1234567-89.2020.1.23.4567',
            availability_date: new Date('2023-01-02'),
            authors: ['Valid Author'],
            content: 'This is a valid publication content.',
            lawyers: [{ name: 'Lawyer One', oab: '11111' }, { name: 'Lawyer Two', oab: '22222' }],
            gross_value: BigInt(5000),
            net_value: BigInt(4000),
            interest_value: BigInt(200),
            attorney_fees: BigInt(100),
        }
        const publicationJson: PublicationJsonEntity = {
            ...input,
            id: 'pub-3',
            gross_value: input.gross_value!.toString(),
            net_value: input.net_value!.toString(),
            interest_value: input.interest_value!.toString(),
            attorney_fees: input.attorney_fees!.toString(),
            defendant: 'Instituto Nacional do Seguro Social - INSS',
            status: 'NOVA' as PublicationStatus,
            scraping_source: 'DJE-SP',
            caderno: '3',
            instancia: '1',
            local: 'Capital',
            parte: '1',
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        publicationRepository.upsert.mockResolvedValue(publicationJson)

        const result = await useCase.execute(input)

        expect(PublicationValidation.areValidLawyers).toHaveBeenCalledWith(input.lawyers)
        expect(PublicationValidation.areValidMonetaryValues).toHaveBeenCalledWith(input)
        expect(result.publication.lawyers).toEqual(input.lawyers)
        expect(result.publication.gross_value).toEqual(BigInt(input.gross_value!))
        expect(result.publication.net_value).toEqual(BigInt(input.net_value!))
        expect(result.publication.interest_value).toEqual(BigInt(input.interest_value!))
        expect(result.publication.attorney_fees).toEqual(BigInt(input.attorney_fees!))
    })

    it('should_throw_validation_error_for_empty_or_invalid_authors', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const baseInput = {
            process_number: '1234567-89.2020.1.23.4567',
            availability_date: new Date('2023-01-02'),
            content: 'This is a valid publication content.',
        }

        // Empty authors array
        await expect(useCase.execute({ ...baseInput, authors: [] }))
            .rejects.toThrow(ValidationError)

        // Authors array with empty string
        await expect(useCase.execute({ ...baseInput, authors: [''] }))
            .rejects.toThrow(ValidationError)

        // Authors array with whitespace string
        await expect(useCase.execute({ ...baseInput, authors: ['   '] }))
            .rejects.toThrow(ValidationError)
    })

    it('should_throw_validation_error_for_insufficient_content', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const baseInput = {
            process_number: '1234567-89.2020.1.23.4567',
            availability_date: new Date('2023-01-02'),
            authors: ['Valid Author'],
        }

        // Missing content
        await expect(useCase.execute({ ...baseInput, content: '' }))
            .rejects.toThrow(ValidationError)

        // Content too short
        await expect(useCase.execute({ ...baseInput, content: 'short' }))
            .rejects.toThrow(ValidationError)

        // Content with only spaces
        await expect(useCase.execute({ ...baseInput, content: '      ' }))
            .rejects.toThrow(ValidationError)
    })

    it('should_throw_publication_creation_error_on_repository_failure', async () => {
        (PublicationValidation.areValidLawyers as jest.Mock).mockReturnValue(true)
            (PublicationValidation.areValidMonetaryValues as jest.Mock).mockReturnValue(true)

        const input = {
            process_number: '1234567-89.2020.1.23.4567',
            availability_date: new Date('2023-01-02'),
            authors: ['Valid Author'],
            content: 'This is a valid publication content.',
        }
        publicationRepository.upsert.mockRejectedValue(new Error('DB failure'))

        await expect(useCase.execute(input)).rejects.toThrow(PublicationCreationError)
        await expect(useCase.execute(input)).rejects.toThrow('Failed to create publication: DB failure')
    })
})