import { PublicationEntity, PublicationValidation } from '@/domain/entities/publication.entity'
import { PublicationRepository, CreatePublicationData } from '@/domain/repositories/publication.repository'

export class CreatePublicationUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: CreatePublicationInput): Promise<CreatePublicationOutput> {
    // Validações de domínio (as validações básicas já foram feitas no mapper)
    this.validateDomainRules(input)

    // Verificar se já existe publicação com mesmo número de processo
    /*const existingPublication = await this.publicationRepository.findByProcessNumber(input.process_number)
    if (existingPublication) {
      throw new DuplicatePublicationError(`Publication with process number ${input.process_number} already exists`)
    }*/

    // Preparar dados para criação
    const publicationData: CreatePublicationData = {
      process_number: input.process_number,
      availability_date: input.availability_date,
      authors: input.authors,
      content: input.content,
      defendant: input.defendant || 'Instituto Nacional do Seguro Social - INSS',
      status: input.status || 'NOVA',
      scraping_source: input.scraping_source || 'DJE-SP',
      caderno: input.caderno || '3',
      instancia: input.instancia || '1',
      local: input.local || 'Capital',
      parte: input.parte || '1',

      // Campos opcionais
      ...(input.publication_date && { publication_date: input.publication_date }),
      ...(input.lawyers && { lawyers: input.lawyers }),
      ...(input.gross_value !== undefined && { gross_value: input.gross_value }),
      ...(input.net_value !== undefined && { net_value: input.net_value }),
      ...(input.interest_value !== undefined && { interest_value: input.interest_value }),
      ...(input.attorney_fees !== undefined && { attorney_fees: input.attorney_fees }),
      ...(input.extraction_metadata && { extraction_metadata: input.extraction_metadata }),
    }

    try {
      // Criar publicação
      const publication = await this.publicationRepository.upsert(publicationData)

      return {
        publication,
      }
    } catch (error) {
      // Log para debugging
      console.error('Error creating publication in repository:', error)

      // Re-throw como erro de domínio
      if (error instanceof Error) {
        throw new PublicationCreationError(`Failed to create publication: ${error.message}`)
      }

      throw new PublicationCreationError('Failed to create publication: Unknown error')
    }
  }

  /**
   * Validações específicas de domínio usando as classes de validação
   */
  private validateDomainRules(input: CreatePublicationInput): void {
  // Validar formato do número do processo
  /*if (!PublicationValidation.isValidprocess_number(input.process_number)) {
    throw new ValidationError('Process number must follow Brazilian court format (NNNNNNN-NN.NNNN.N.NN.NNNN)')
  }*/

  // Validar datas
  /*if (!PublicationValidation.areValidDates(input.publicationDate, input.availability_date)) {
    throw new ValidationError('Invalid dates: availability date cannot be in the future and must be after publication date')
  }*/

  // Validar autores
    if (!input.authors || input.authors.length === 0) {
      throw new ValidationError('At least one author is required')
    }

    if (input.authors.some(author => !author.trim())) {
      throw new ValidationError('Authors cannot contain empty names')
    }

    // Validar advogados
    if (!PublicationValidation.areValidLawyers(input.lawyers)) {
      throw new ValidationError('Invalid lawyers data: name and OAB are required for each lawyer')
    }

    // Validar valores monetários
    if (!PublicationValidation.areValidMonetaryValues(input)) {
      throw new ValidationError('Monetary values cannot be negative or invalid')
    }

    // Validar conteúdo mínimo
    if (!input.content || input.content.trim().length < 10) {
      throw new ValidationError('Content must have at least 10 characters')
    }
  }
}

export interface CreatePublicationInput {
  process_number: string
  publication_date?: Date
  availability_date: Date
  authors: string[]
  defendant?: string
  lawyers?: Array<{ name: string; oab: string }>
  gross_value?: bigint
  net_value?: bigint
  interest_value?: bigint
  attorney_fees?: bigint
  content: string
  status?: PublicationEntity['status']
  scraping_source?: string
  caderno?: string
  instancia?: string
  local?: string
  parte?: string
  extraction_metadata?: any
}

export interface CreatePublicationOutput {
  publication: PublicationEntity
}

// Erros específicos do domínio
export class ValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValidationError'
  }
}

export class DuplicatePublicationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DuplicatePublicationError'
  }
}

export class PublicationCreationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'PublicationCreationError'
  }
}