import { PublicationEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository, CreatePublicationData } from '@/domain/repositories/publication.repository'

export class CreatePublicationUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: CreatePublicationInput): Promise<CreatePublicationOutput> {
    // Validações básicas
    if (!input.processNumber || input.processNumber.trim().length === 0) {
      throw new ValidationError('Process number is required')
    }

    if (!input.availabilityDate) {
      throw new ValidationError('Availability date is required')
    }

    if (!input.authors || input.authors.length === 0) {
      throw new ValidationError('At least one author is required')
    }

    if (!input.content || input.content.trim().length === 0) {
      throw new ValidationError('Content is required')
    }

    const publicationData: CreatePublicationData = {
      processNumber: input.processNumber.trim(),
      availabilityDate: input.availabilityDate,
      authors: input.authors,
      content: input.content.trim(),
      ...(input.publicationDate && { publicationDate: input.publicationDate }),
      ...(input.defendant && { defendant: input.defendant }),
      ...(input.lawyers && { lawyers: input.lawyers }),
      ...(input.grossValue && { grossValue: input.grossValue }),
      ...(input.netValue && { netValue: input.netValue }),
      ...(input.interestValue && { interestValue: input.interestValue }),
      ...(input.attorneyFees && { attorneyFees: input.attorneyFees }),
      ...(input.status && { status: input.status }),
      ...(input.scrapingSource && { scrapingSource: input.scrapingSource }),
      ...(input.caderno && { caderno: input.caderno }),
      ...(input.instancia && { instancia: input.instancia }),
      ...(input.local && { local: input.local }),
      ...(input.parte && { parte: input.parte }),
      ...(input.extractionMetadata && { extractionMetadata: input.extractionMetadata }),
    }

    const publication = await this.publicationRepository.create(publicationData)

    return {
      publication,
    }
  }
}

export interface CreatePublicationInput {
  processNumber: string
  publicationDate?: Date
  availabilityDate: Date
  authors: string[]
  defendant?: string
  lawyers?: Array<{ name: string; oab: string }>
  grossValue?: number
  netValue?: number
  interestValue?: number
  attorneyFees?: number
  content: string
  status?: PublicationEntity['status']
  scrapingSource?: string
  caderno?: string
  instancia?: string
  local?: string
  parte?: string
  extractionMetadata?: any
}

export interface CreatePublicationOutput {
  publication: PublicationEntity
}

export class ValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ValidationError'
  }
}
