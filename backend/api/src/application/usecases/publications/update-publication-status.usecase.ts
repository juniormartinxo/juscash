import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class UpdatePublicationStatusUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: UpdatePublicationStatusInput): Promise<PublicationEntity> {
    const publication = await this.publicationRepository.findById(input.publicationId)

    if (!publication) {
      throw new Error('Publication not found')
    }

    // Validar transições de status
    this.validateStatusTransition(publication.status, input.newStatus)

    const updatedPublication = await this.publicationRepository.updateStatus(
      input.publicationId,
      input.newStatus
    )

    return this.convertToEntity(updatedPublication)
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

  private validateStatusTransition(
    currentStatus: PublicationEntity['status'],
    newStatus: PublicationEntity['status']
  ): void {
    const validTransitions: Record<PublicationEntity['status'], PublicationEntity['status'][]> = {
      NOVA: ['LIDA'],
      LIDA: ['ENVIADA_PARA_ADV', 'CONCLUIDA'],
      ENVIADA_PARA_ADV: ['LIDA', 'CONCLUIDA'],
      CONCLUIDA: [],
    }

    if (!validTransitions[currentStatus].includes(newStatus)) {
      throw new Error(`Invalid status transition from ${currentStatus} to ${newStatus}`)
    }
  }
}

export interface UpdatePublicationStatusInput {
  publicationId: string
  newStatus: PublicationEntity['status']
}
