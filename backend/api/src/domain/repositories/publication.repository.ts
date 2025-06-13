import { PublicationEntity } from '@/domain/entities/publication.entity'

export interface PublicationRepository {
  findById(id: string): Promise<PublicationEntity | null>
  findMany(params: FindPublicationsParams): Promise<PublicationResult>
  updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationEntity>
  search(query: string): Promise<PublicationEntity[]>
}

export interface FindPublicationsParams {
  page?: number
  limit?: number
  status?: PublicationEntity['status']
  startDate?: Date
  endDate?: Date
  searchTerm?: string
}

export interface PublicationResult {
  publications: PublicationEntity[]
  total: number
  page: number
  totalPages: number
}