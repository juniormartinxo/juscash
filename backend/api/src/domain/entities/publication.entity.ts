/**
 * Entidade de domínio para Publicação
 * Representa uma publicação judicial do DJE
 */
export interface PublicationEntity {
  id: string
  process_number: string
  publication_date?: Date | null
  availability_date: Date
  authors: string[]
  defendant: string
  lawyers?: Array<{ name: string; oab: string }> | null
  gross_value?: bigint | null // Valor em centavos (bigint para suportar valores grandes)
  net_value?: bigint | null // Valor em centavos (bigint para suportar valores grandes)
  interest_value?: bigint | null // Valor em centavos (bigint para suportar valores grandes)
  attorney_fees?: bigint | null // Valor em centavos (bigint para suportar valores grandes)
  content: string
  status: PublicationStatus
  scraping_source: string
  caderno: string
  instancia: string
  local: string
  parte: string
  extraction_metadata?: any | null
  createdAt: Date
  updatedAt: Date
}

export type PublicationJsonEntity = Omit<PublicationEntity, 'gross_value' | 'net_value' | 'interest_value' | 'attorney_fees'> & {
  gross_value?: string | null
  net_value?: string | null
  interest_value?: string | null
  attorney_fees?: string | null
}
/**
 * Enum para status da publicação
 * Corresponde ao enum do Prisma schema
 */
export type PublicationStatus =
  | 'NOVA'           // Publicação nova (scraping inicial)
  | 'LIDA'           // Publicação foi lida/revisada
  | 'ENVIADA_PARA_ADV' // Enviada para advogado
  | 'CONCLUIDA'      // Processamento concluído

/**
 * Classe utilitária para validações de domínio
 */
export class PublicationValidation {
  /**
   * Valida se o número do processo segue o formato brasileiro
   */
  static isValidprocess_number(process_number: string): boolean {
    const regex = /^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$/
    return regex.test(process_number)
  }

  /**
   * Valida se a transição de status é permitida
   */
  static isValidStatusTransition(from: PublicationStatus, to: PublicationStatus): boolean {
    const allowedTransitions: Record<PublicationStatus, PublicationStatus[]> = {
      'NOVA': ['LIDA'],
      'LIDA': ['ENVIADA_PARA_ADV', 'CONCLUIDA'],
      'ENVIADA_PARA_ADV': ['LIDA', 'CONCLUIDA'],
      'CONCLUIDA': [], // Status final, não pode ser alterado
    }

    return allowedTransitions[from]?.includes(to) ?? false
  }

  /**
   * Valida se os dados monetários são válidos
   */
  static areValidMonetaryValues(publication: Partial<PublicationEntity>): boolean {
    const fields = ['gross_value', 'net_value', 'interest_value', 'attorney_fees'] as const

    for (const field of fields) {
      const value = publication[field]
      if (value !== undefined && value !== null && (value < 0 || !Number.isFinite(value))) {
        return false
      }
    }

    return true
  }

  /**
   * Valida se as datas são consistentes
   */
  static areValidDates(publication_date?: Date | null, availability_date?: Date): boolean {
    if (!availability_date) return false

    const today = new Date()
    today.setHours(23, 59, 59, 999)

    // Availability date não pode ser futura
    if (availability_date > today) return false

    // Se publication date existe, deve ser <= availability date
    if (publication_date && publication_date > availability_date) return false

    return true
  }

  /**
   * Valida estrutura de advogados
   */
  static areValidLawyers(lawyers?: Array<{ name: string; oab: string }> | null): boolean {
    if (!lawyers) return true // Advogados são opcionais

    return lawyers.every(lawyer =>
      lawyer.name &&
      lawyer.name.trim().length > 0 &&
      lawyer.oab &&
      lawyer.oab.trim().length > 0
    )
  }
}

/**
 * Factory para criar entidades de publicação
 */
export class PublicationFactory {
  /**
   * Cria uma nova publicação com valores padrão
   */
  static create(data: {
    process_number: string
    availability_date: Date
    authors: string[]
    content: string
    publication_date?: Date
    lawyers?: Array<{ name: string; oab: string }>
    gross_value?: bigint
    net_value?: bigint
    interest_value?: bigint
    attorney_fees?: bigint
    extraction_metadata?: any
  }): Omit<PublicationEntity, 'id' | 'createdAt' | 'updatedAt'> {

    // Validações
    if (!PublicationValidation.isValidprocess_number(data.process_number)) {
      throw new Error('Invalid process number format')
    }

    if (!PublicationValidation.areValidDates(data.publication_date, data.availability_date)) {
      throw new Error('Invalid dates')
    }

    if (!PublicationValidation.areValidLawyers(data.lawyers)) {
      throw new Error('Invalid lawyers data')
    }

    if (!data.authors || data.authors.length === 0) {
      throw new Error('At least one author is required')
    }

    if (!data.content || data.content.trim().length < 10) {
      throw new Error('Content must have at least 10 characters')
    }

    return {
      process_number: data.process_number,
      publication_date: data.publication_date || null,
      availability_date: data.availability_date,
      authors: data.authors,
      defendant: 'Instituto Nacional do Seguro Social - INSS',
      lawyers: data.lawyers || null,
      gross_value: data.gross_value || null,
      net_value: data.net_value || null,
      interest_value: data.interest_value || null,
      attorney_fees: data.attorney_fees || null,
      content: data.content,
      status: 'NOVA',
      scraping_source: 'DJE-SP',
      caderno: '3',
      instancia: '1',
      local: 'Capital',
      parte: '1',
      extraction_metadata: data.extraction_metadata || null,
    }
  }

  /**
   * Clona uma publicação existente com modificações
   */
  static clone(
    original: PublicationEntity,
    changes: Partial<PublicationEntity>
  ): PublicationEntity {
    return {
      ...original,
      ...changes,
      updatedAt: new Date(),
    }
  }
}

/**
 * Utilitários para formatação de dados da publicação
 */
export class PublicationFormatter {
  /**
   * Formata valores monetários para exibição
   */
  static formatMoney(value?: bigint | null): string {
    if (value === null || value === undefined) return 'N/A'

    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value)
  }

  /**
   * Formata lista de autores
   */
  static formatAuthors(authors: string[]): string {
    if (authors.length === 0) return 'N/A'
    if (authors.length === 1) return authors[0] || 'N/A'
    if (authors.length === 2) return authors.join(' e ')

    return `${authors.slice(0, -1).join(', ')} e ${authors[authors.length - 1] || ''}`
  }

  /**
   * Formata advogados para exibição
   */
  static formatLawyers(lawyers?: Array<{ name: string; oab: string }> | null): string {
    if (!lawyers || lawyers.length === 0) return 'N/A'

    return lawyers
      .map(lawyer => `${lawyer.name} (OAB: ${lawyer.oab})`)
      .join(', ')
  }

  /**
   * Gera resumo da publicação
   */
  static generateSummary(publication: PublicationEntity): string {
    const parts = [
      `Processo: ${publication.process_number}`,
      `Autor(es): ${this.formatAuthors(publication.authors)}`,
      `Status: ${publication.status}`,
    ]

    if (publication.gross_value) {
      parts.push(`Valor: ${this.formatMoney(publication.gross_value)}`)
    }

    return parts.join(' | ')
  }
}
