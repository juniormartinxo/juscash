// Importações necessárias (ajustar conforme sua estrutura)
import { CreatePublicationInput } from '@/application/usecases/publications/create-publication.usecase'
import { PublicationEntity } from '@/domain/entities/publication.entity'
/**
 * DTO para criação de publicação via API (formato snake_case do scraper)
 */
export interface CreatePublicationDTO {
    process_number: string
    publication_date?: string | null
    availability_date: string
    authors: string[]
    defendant?: string
    lawyers?: Array<{ name: string; oab: string }> | null
    gross_value?: number | null // Recebido como number mas convertido para bigint
    net_value?: number | null // Recebido como number mas convertido para bigint
    interest_value?: number | null // Recebido como number mas convertido para bigint
    attorney_fees?: number | null // Recebido como number mas convertido para bigint
    content: string
    status?: 'NOVA' | 'LIDA' | 'ENVIADA_PARA_ADV' | 'CONCLUIDA'
    scraping_source?: string
    caderno?: string
    instancia?: string
    local?: string
    parte?: string
    extraction_metadata?: any
    scraping_execution_id?: string | null
}

/**
 * Mapper para converter DTO em Input do UseCase
 */
export class CreatePublicationMapper {
    /**
     * Converte DTO (snake_case) para Input (camelCase) do UseCase
     */
    static toUseCaseInput(dto: CreatePublicationDTO): CreatePublicationInput {
        // Validações básicas no nível do adapter
        if (!dto.process_number?.trim()) {
            throw new ValidationError('process_number is required')
        }

        if (!dto.availability_date) {
            throw new ValidationError('availability_date is required')
        }

        if (!dto.authors || dto.authors.length === 0) {
            throw new ValidationError('authors is required and must not be empty')
        }

        if (!dto.content?.trim()) {
            throw new ValidationError('content is required')
        }

        const input: CreatePublicationInput = {
            process_number: dto.process_number.trim(),
            availability_date: this.parseDate(dto.availability_date),
            authors: dto.authors,
            defendant: dto.defendant || 'Instituto Nacional do Seguro Social - INSS',
            content: dto.content.trim(),
            scraping_source: dto.scraping_source || 'DJE-SP',
            caderno: dto.caderno || '3',
            instancia: dto.instancia || '1',
            local: dto.local || 'Capital',
            parte: dto.parte || '1',
        }

        // Adicionar status se fornecido
        const mappedStatus = this.mapStatus(dto.status)
        if (mappedStatus) {
            input.status = mappedStatus
        }

        // Adicionar campos opcionais apenas se tiverem valores
        if (dto.publication_date) {
            input.publication_date = this.parseDate(dto.publication_date)
        }
        if (dto.lawyers) {
            input.lawyers = dto.lawyers
        }
        if (dto.gross_value !== undefined && dto.gross_value !== null) {
            input.gross_value = BigInt(dto.gross_value)
        }
        if (dto.net_value !== undefined && dto.net_value !== null) {
            input.net_value = BigInt(dto.net_value)
        }
        if (dto.interest_value !== undefined && dto.interest_value !== null) {
            input.interest_value = BigInt(dto.interest_value)
        }
        if (dto.attorney_fees !== undefined && dto.attorney_fees !== null) {
            input.attorney_fees = BigInt(dto.attorney_fees)
        }
        if (dto.extraction_metadata) {
            input.extraction_metadata = dto.extraction_metadata
        }

        return input
    }

    /**
     * Converte string de data para objeto Date
     */
    private static parseDate(dateString: string): Date {
        const date = new Date(dateString)

        if (isNaN(date.getTime())) {
            throw new ValidationError(`Invalid date format: ${dateString}`)
        }

        return date
    }

    /**
     * Mapeia status do DTO para enum do domínio
     */
    private static mapStatus(status?: string): PublicationEntity['status'] | undefined {
        if (!status) return undefined

        const statusMap: Record<string, PublicationEntity['status']> = {
            'NOVA': 'NOVA',
            'LIDA': 'LIDA',
            'ENVIADA_PARA_ADV': 'ENVIADA_PARA_ADV',
            'CONCLUIDA': 'CONCLUIDA'
        }

        const mappedStatus = statusMap[status]
        if (!mappedStatus) {
            throw new ValidationError(`Invalid status: ${status}`)
        }

        return mappedStatus
    }
}

export class ValidationError extends Error {
    constructor(message: string) {
        super(message)
        this.name = 'ValidationError'
    }
}