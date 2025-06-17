import { PublicationEntity, PublicationJsonEntity } from '@/domain/entities/publication.entity'

export interface PublicationRepository {
  findById(id: string): Promise<PublicationJsonEntity | null>
  findByProcessNumber(process_number: string): Promise<PublicationJsonEntity | null>
  findMany(params: FindPublicationsParams): Promise<PublicationJsonResult>
  updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationJsonEntity>
  search(query: string): Promise<PublicationJsonEntity[]>
  create(data: CreatePublicationData): Promise<PublicationJsonEntity>
  upsert(data: CreatePublicationData): Promise<PublicationJsonEntity>
}

export interface CreatePublicationData {
  process_number: string
  publication_date?: Date
  availability_date?: Date
  authors: string[]
  defendant?: string
  lawyers?: Array<{ name: string; oab: string }>
  gross_value?: bigint
  net_value?: bigint
  interest_value?: bigint
  attorney_fees?: bigint
  content: string
  status?: PublicationEntity['status']
  scraping_source?: string
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

export interface PublicationJsonResult {
  publications: PublicationJsonEntity[]
  total: number
  page: number
  totalPages: number
}