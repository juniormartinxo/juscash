export interface PublicationEntity {
  id: string
  processNumber: string
  publicationDate?: Date
  availabilityDate: Date
  authors: string[]
  defendant: string
  lawyers?: Array<{ name: string; oab: string }>
  grossValue?: number
  netValue?: number
  interestValue?: number
  attorneyFees?: number
  content: string
  status: 'NOVA' | 'LIDA' | 'ENVIADA_PARA_ADV' | 'CONCLUIDA'
  createdAt: Date
  updatedAt: Date
}