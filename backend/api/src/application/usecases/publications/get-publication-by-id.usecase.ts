import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class GetPublicationByIdUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: GetPublicationByIdInput): Promise<GetPublicationByIdOutput> {
    const publication = await this.publicationRepository.findById(input.id)

    if (!publication) {
      throw new PublicationNotFoundError('Publication not found')
    }

    return {
      publication: this.convertToEntity(publication),
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
