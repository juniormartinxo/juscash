import { PublicationEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class SearchPublicationsUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: SearchPublicationsInput): Promise<SearchPublicationsOutput> {
    if (!input.query || input.query.trim().length < 2) {
      throw new Error('Search query must be at least 2 characters long')
    }

    const publications = await this.publicationRepository.search(input.query.trim())

    return {
      publications,
      query: input.query,
      total: publications.length,
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
