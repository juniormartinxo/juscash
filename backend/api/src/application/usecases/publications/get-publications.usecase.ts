import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class GetPublicationsUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: GetPublicationsInput): Promise<GetPublicationsOutput> {
    const params: any = {
      page: input.page || 1,
      limit: input.limit || 30,
      searchTerm: input.searchTerm || '',
    }


    if (input.status) {
      params.status = input.status
    }


    if (input.startDate) {
      params.startDate = input.startDate
    }
    if (input.endDate) {
      params.endDate = input.endDate
    }

    const result = await this.publicationRepository.findMany(params)

    return {
      publications: result.publications.map(pub => this.convertToEntity(pub)),
      pagination: {
        current: result.page,
        total: result.totalPages,
        count: result.total,
        perPage: input.limit || 30,
      },
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

export interface GetPublicationsInput {
  page?: number
  limit?: number
  status?: PublicationEntity['status']
  startDate?: Date
  endDate?: Date
  searchTerm?: string
}

export interface GetPublicationsOutput {
  publications: PublicationEntity[]
  pagination: {
    current: number
    total: number
    count: number
    perPage: number
  }
}

