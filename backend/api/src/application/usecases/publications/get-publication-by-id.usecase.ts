import { PublicationEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class GetPublicationByIdUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: GetPublicationByIdInput): Promise<GetPublicationByIdOutput> {
    const publication = await this.publicationRepository.findById(input.id)

    if (!publication) {
      throw new PublicationNotFoundError('Publication not found')
    }

    return {
      publication,
    }
  }
}

export interface GetPublicationByIdInput {
  id: string
}

export interface GetPublicationByIdOutput {
  publication: PublicationEntity
}

export class PublicationNotFoundError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'PublicationNotFoundError'
  }
}
