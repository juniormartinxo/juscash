import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class SearchPublicationsUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: SearchPublicationsInput): Promise<SearchPublicationsOutput> {
    if (!input.query || input.query.trim().length < 2) {
      throw new Error('Search query must be at least 2 characters long')
    }

    const publications = await this.publicationRepository.search(input.query.trim())

    return {
      publications: publications.map(pub => this.convertToEntity(pub)),
      query: input.query,
      total: publications.length,
    }
  }

  private convertToEntity(jsonEntity: PublicationJsonEntity): PublicationEntity {
    return {
      ...jsonEntity,
      gross_value: jsonEntity.gross_value ? BigInt(jsonEntity.gross_value) : null,
      net_value: jsonEntity.net_value ? BigInt(jsonEntity.net_value) : null,
      interest_value: jsonEntity.interest_value ? BigInt(jsonEntity.interest_value) : null,
      attorney_fees: jsonEntity.attorney_fees ? BigInt(jsonEntity.attorney_fees) : null,
    }
  }
}

export interface SearchPublicationsInput {
  query: string
}

export interface SearchPublicationsOutput {
  publications: PublicationEntity[]
  query: string
  total: number
}
