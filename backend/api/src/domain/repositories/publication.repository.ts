import { PublicationEntity } from '@/domain/entities/publication.entity'

export interface PublicationRepository {
  findById(id: string): Promise<PublicationEntity | null>
  findMany(params: FindPublicationsParams): Promise<PublicationResult>
  updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationEntity>
  search(query: string): Promise<PublicationEntity[]>
  create(data: CreatePublicationData): Promise<PublicationEntity>
}

export interface CreatePublicationData {
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
