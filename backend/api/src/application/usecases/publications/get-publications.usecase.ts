import { PublicationEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

export class GetPublicationsUseCase {
  constructor(private publicationRepository: PublicationRepository) { }

  async execute(input: GetPublicationsInput): Promise<GetPublicationsOutput> {
    const result = await this.publicationRepository.findMany({
      page: input.page || 1,
      limit: input.limit || 30,
      status: input.status || 'NOVA',
      startDate: input.startDate || new Date(),
      endDate: input.endDate || new Date(),
      searchTerm: input.searchTerm || '',
    })

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

