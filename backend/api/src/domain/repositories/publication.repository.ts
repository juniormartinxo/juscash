import { PublicationEntity } from '@/domain/entities/publication.entity'

export interface PublicationRepository {
  findById(id: string): Promise<PublicationEntity | null>
  findByProcessNumber(process_number: string): Promise<PublicationEntity | null>
  findMany(params: FindPublicationsParams): Promise<PublicationResult>
  updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationEntity>
  search(query: string): Promise<PublicationEntity[]>
  create(data: CreatePublicationData): Promise<PublicationEntity>
  upsert(data: CreatePublicationData): Promise<PublicationEntity>
}

export interface CreatePublicationData {
  process_number: string
  publication_date?: Date
  availability_date?: Date
  authors: string[]
  defendant?: string
  lawyers?: Array<{ name: string; oab: string }>
  gross_value?: number
  net_value?: number
  interest_value?: number
  attorney_fees?: number
  content: string
  status?: PublicationEntity['status']
  scrapingSource?: string
  caderno?: string
  instancia?: string
  local?: string
  parte?: string
  extraction_metadata?: any
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