import { PublicationEntity } from '@/domain/entities/publication.entity'
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
      publications: result.publications,
      pagination: {
        current: result.page,
        total: result.totalPages,
        count: result.total,
        perPage: input.limit || 30,
      },
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

