import { UpdatePublicationStatusUseCase } from '@/application/usecases/publications/update-publication-status.usecase'
import { PublicationRepository } from '@/domain/repositories/publication.repository'
import { PublicationJsonEntity, PublicationEntity, PublicationStatus } from '@/domain/entities/publication.entity'

describe('UpdatePublicationStatusUseCase', () => {
    let publicationRepository: jest.Mocked<PublicationRepository>
    let useCase: UpdatePublicationStatusUseCase

    const baseJsonEntity: PublicationJsonEntity = {
        id: 'pub-1',
        process_number: '12345',
        publication_date: new Date('2024-01-01T00:00:00Z'),
        availability_date: new Date('2024-01-02T00:00:00Z'),
        authors: ['Author 1'],
        defendant: 'Defendant 1',
        lawyers: [{ name: 'Lawyer 1', oab: 'OAB123' }],
        gross_value: '10000',
        net_value: '9000',
        interest_value: '500',
        attorney_fees: '200',
        content: 'Some content',
        status: 'NOVA' as PublicationStatus,
        scraping_source: 'source',
        caderno: 'caderno',
        instancia: 'instancia',
        local: 'local',
        parte: 'parte',
        extraction_metadata: null,
        createdAt: new Date('2024-01-01T00:00:00Z'),
        updatedAt: new Date('2024-01-02T00:00:00Z'),
    }

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
        useCase = new UpdatePublicationStatusUseCase(publicationRepository)
    })

    it('should_update_status_when_transition_is_valid', async () => {
        const input = { publicationId: 'pub-1', newStatus: 'LIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue({ ...baseJsonEntity, status: 'NOVA' as PublicationStatus })
        publicationRepository.updateStatus.mockResolvedValue({ ...baseJsonEntity, status: 'LIDA' as PublicationStatus })

        const result = await useCase.execute(input)

        expect(publicationRepository.findById).toHaveBeenCalledWith('pub-1')
        expect(publicationRepository.updateStatus).toHaveBeenCalledWith('pub-1', 'LIDA')
        expect(result.status).toBe('LIDA')
    })

    it('should_convert_stringified_monetary_values_to_bigint', async () => {
        const input = { publicationId: 'pub-1', newStatus: 'LIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue({ ...baseJsonEntity, status: 'NOVA' as PublicationStatus })
        publicationRepository.updateStatus.mockResolvedValue({
            ...baseJsonEntity,
            status: 'LIDA' as PublicationStatus,
            gross_value: '12345678901234567890',
            net_value: '9876543210987654321',
            interest_value: '1111111111111111111',
            attorney_fees: '2222222222222222222',
        })

        const result = await useCase.execute(input)

        expect(result.gross_value).toBe(BigInt('12345678901234567890'))
        expect(result.net_value).toBe(BigInt('9876543210987654321'))
        expect(result.interest_value).toBe(BigInt('1111111111111111111'))
        expect(result.attorney_fees).toBe(BigInt('2222222222222222222'))
    })

    it('should_return_complete_entity_after_successful_update', async () => {
        const input = { publicationId: 'pub-1', newStatus: 'LIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue({ ...baseJsonEntity, status: 'NOVA' as PublicationStatus })
        publicationRepository.updateStatus.mockResolvedValue({ ...baseJsonEntity, status: 'LIDA' as PublicationStatus })

        const result = await useCase.execute(input)

        expect(result).toMatchObject({
            id: baseJsonEntity.id,
            process_number: baseJsonEntity.process_number,
            publication_date: baseJsonEntity.publication_date,
            availability_date: baseJsonEntity.availability_date,
            authors: baseJsonEntity.authors,
            defendant: baseJsonEntity.defendant,
            lawyers: baseJsonEntity.lawyers,
            gross_value: BigInt(baseJsonEntity.gross_value!),
            net_value: BigInt(baseJsonEntity.net_value!),
            interest_value: BigInt(baseJsonEntity.interest_value!),
            attorney_fees: BigInt(baseJsonEntity.attorney_fees!),
            content: baseJsonEntity.content,
            status: 'LIDA',
            scraping_source: baseJsonEntity.scraping_source,
            caderno: baseJsonEntity.caderno,
            instancia: baseJsonEntity.instancia,
            local: baseJsonEntity.local,
            parte: baseJsonEntity.parte,
            extraction_metadata: baseJsonEntity.extraction_metadata,
            createdAt: baseJsonEntity.createdAt,
            updatedAt: baseJsonEntity.updatedAt,
        })
    })

    it('should_throw_error_if_publication_not_found', async () => {
        const input = { publicationId: 'non-existent', newStatus: 'LIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue(null)

        await expect(useCase.execute(input)).rejects.toThrow('Publication not found')
        expect(publicationRepository.findById).toHaveBeenCalledWith('non-existent')
        expect(publicationRepository.updateStatus).not.toHaveBeenCalled()
    })

    it('should_throw_error_on_invalid_status_transition', async () => {
        const input = { publicationId: 'pub-1', newStatus: 'CONCLUIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue({ ...baseJsonEntity, status: 'NOVA' as PublicationStatus })

        await expect(useCase.execute(input)).rejects.toThrow('Invalid status transition from NOVA to CONCLUIDA')
        expect(publicationRepository.updateStatus).not.toHaveBeenCalled()
    })

    it('should_handle_null_monetary_values_in_conversion', async () => {
        const input = { publicationId: 'pub-1', newStatus: 'LIDA' as PublicationStatus }
        publicationRepository.findById.mockResolvedValue({ ...baseJsonEntity, status: 'NOVA' as PublicationStatus })
        publicationRepository.updateStatus.mockResolvedValue({
            ...baseJsonEntity,
            status: 'LIDA' as PublicationStatus,
            gross_value: null,
            net_value: null,
            interest_value: null,
            attorney_fees: null,
        })

        const result = await useCase.execute(input)

        expect(result.gross_value).toBeNull()
        expect(result.net_value).toBeNull()
        expect(result.interest_value).toBeNull()
        expect(result.attorney_fees).toBeNull()
    })
})