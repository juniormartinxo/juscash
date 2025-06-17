import { PublicationEntity } from '@/domain/entities/publication.entity'
import { 
  PublicationRepository,
  CreatePublicationData, 
  FindPublicationsParams, 
  PublicationResult
} from '@/domain/repositories/publication.repository'
import { PrismaClient } from '@/generated/prisma/index'

export class PrismaPublicationRepository implements PublicationRepository {
  constructor(private prisma: PrismaClient) { }

  async findById(id: string): Promise<PublicationEntity | null> {
    try {
      const publication = await this.prisma.publication.findUnique({
        where: { id },
      })

      return publication ? this.toDomainEntity(publication) : null
    } catch (error) {
      console.error('Error finding publication by ID:', error)
      throw new Error(`Failed to find publication with ID ${id}`)
    }
  }

  async findByProcessNumber(process_number: string): Promise<PublicationEntity | null> {
    try {
      const publication = await this.prisma.publication.findUnique({
        where: {
          process_number: process_number
        },
      })

      return publication ? this.toDomainEntity(publication) : null
    } catch (error) {
      console.error('Error finding publication by process number:', error)
      throw new Error(`Failed to find publication with process number ${process_number}`)
    }
  }

  async findMany(params: FindPublicationsParams): Promise<PublicationResult> {
    try {
      const {
        page = 1,
        limit = 30,
        status,
        startDate,
        endDate,
        searchTerm,
      } = params

      const skip = (page - 1) * limit

      // Construir filtros
      const where: any = {}

      if (status) {
        where.status = status
      }

      if (startDate || endDate) {
        where.availability_date = {}
        if (startDate) {
          where.availability_date.gte = startDate
        }
        if (endDate) {
          where.availability_date.lte = endDate
        }
      }

      if (searchTerm) {
        where.OR = [
          { process_number: { contains: searchTerm, mode: 'insensitive' } },
          { authors: { has: searchTerm } },
          { defendant: { contains: searchTerm, mode: 'insensitive' } },
          { content: { contains: searchTerm, mode: 'insensitive' } },
        ]
      }

      // Buscar publicações e total
      const [publications, total] = await Promise.all([
        this.prisma.publication.findMany({
          where,
          skip,
          take: limit,
          orderBy: {
            created_at: 'desc',
          },
        }),
        this.prisma.publication.count({ where }),
      ])

      const totalPages = Math.ceil(total / limit)

      return {
        publications: publications.map(this.toDomainEntity),
        total,
        page,
        totalPages,
      }
    } catch (error) {
      console.error('Error finding publications:', error)
      throw new Error('Failed to find publications')
    }
  }

  async updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationEntity> {
    try {
      const updatedPublication = await this.prisma.publication.update({
        where: { id },
        data: {
          status,
          updated_at: new Date(),
        },
      })

      return this.toDomainEntity(updatedPublication)
    } catch (error) {
      console.error('Error updating publication status:', error)
      throw new Error(`Failed to update publication status for ID ${id}`)
    }
  }

  async search(query: string): Promise<PublicationEntity[]> {
    try {
      const publications = await this.prisma.publication.findMany({
        where: {
          OR: [
            { process_number: { contains: query, mode: 'insensitive' } },
            { authors: { has: query } },
            { defendant: { contains: query, mode: 'insensitive' } },
            { content: { contains: query, mode: 'insensitive' } },
          ],
        },
        orderBy: {
          created_at: 'desc',
        },
        take: 100, // Limitar resultados de busca
      })

      return publications.map(this.toDomainEntity)
    } catch (error) {
      console.error('Error searching publications:', error)
      throw new Error('Failed to search publications')
    }
  }

  async create(data: CreatePublicationData): Promise<PublicationEntity> {
    try {
      // Converter valores monetários de reais para centavos se necessário
      const monetaryFieldsInCents = {
        gross_value: data.grossValue ? Math.round(data.grossValue * 100) : null,
        net_value: data.netValue ? Math.round(data.netValue * 100) : null,
        interest_value: data.interestValue ? Math.round(data.interestValue * 100) : null,
        attorney_fees: data.attorneyFees ? Math.round(data.attorneyFees * 100) : null,
      }

      const publicationData: any = {
        process_number: data.process_number,
        publication_date: data.publicationDate || null,
        availability_date: data.availabilityDate,
        authors: data.authors,
        defendant: data.defendant || 'Instituto Nacional do Seguro Social - INSS',
        ...monetaryFieldsInCents,
        content: data.content,
        status: data.status || 'NOVA',
        scraping_source: data.scrapingSource || 'DJE-SP',
        caderno: data.caderno || '3',
        instancia: data.instancia || '1',
        local: data.local || 'Capital',
        parte: data.parte || '1',
      }

      if (data.lawyers) {
        publicationData.lawyers = JSON.stringify(data.lawyers)
      }

      if (data.extractionMetadata) {
        publicationData.extraction_metadata = JSON.stringify(data.extractionMetadata)
      }

      const createdPublication = await this.prisma.publication.create({
        data: publicationData,
      })

      return this.toDomainEntity(createdPublication)
    } catch (error) {
      console.error('Error creating publication:', error)

      // Tratar erro de duplicata especificamente
      if (error instanceof Error && error.message.includes('Unique constraint')) {
        throw new Error(`Publication with process number ${data.process_number} already exists`)
      }

      throw new Error('Failed to create publication')
    }
  }

  /**
   * Converte dados do Prisma para entidade de domínio
   */
  private toDomainEntity(prismaPublication: any): PublicationEntity {
    return {
      id: prismaPublication.id,
      process_number: prismaPublication.process_number,
      publicationDate: prismaPublication.publication_date,
      availabilityDate: prismaPublication.availability_date,
      authors: prismaPublication.authors,
      defendant: prismaPublication.defendant,
      lawyers: prismaPublication.lawyers ? JSON.parse(prismaPublication.lawyers) : null,
      // Converter centavos para reais
      grossValue: prismaPublication.gross_value ? prismaPublication.gross_value / 100 : null,
      netValue: prismaPublication.net_value ? prismaPublication.net_value / 100 : null,
      interestValue: prismaPublication.interest_value ? prismaPublication.interest_value / 100 : null,
      attorneyFees: prismaPublication.attorney_fees ? prismaPublication.attorney_fees / 100 : null,
      content: prismaPublication.content,
      status: prismaPublication.status,
      scrapingSource: prismaPublication.scraping_source,
      caderno: prismaPublication.caderno,
      instancia: prismaPublication.instancia,
      local: prismaPublication.local,
      parte: prismaPublication.parte,
      extractionMetadata: prismaPublication.extraction_metadata ?
        JSON.parse(prismaPublication.extraction_metadata) : null,
      createdAt: prismaPublication.created_at,
      updatedAt: prismaPublication.updated_at,
    }
  }

  /**
   * Métodos auxiliares para estatísticas e monitoramento
   */
  async getPublicationStats(): Promise<{
    total: number
    byStatus: Record<string, number>
    bySource: Record<string, number>
  }> {
    try {
      const [total, byStatus, bySource] = await Promise.all([
        this.prisma.publication.count(),
        this.prisma.publication.groupBy({
          by: ['status'],
          _count: {
            status: true,
          },
        }),
        this.prisma.publication.groupBy({
          by: ['scraping_source'],
          _count: {
            scraping_source: true,
          },
        }),
      ])

      return {
        total,
        byStatus: Object.fromEntries(
          byStatus.map((item: { status: string; _count: { status: number } }) => [item.status, item._count.status])
        ),
        bySource: Object.fromEntries(
          bySource.map((item: { scraping_source: string; _count: { scraping_source: number } }) => [item.scraping_source, item._count.scraping_source])
        ),
      }
    } catch (error) {
      console.error('Error getting publication stats:', error)
      throw new Error('Failed to get publication statistics')
    }
  }

  /**
   * Método para limpeza/manutenção
   */
  async deleteOldPublications(olderThanDays: number = 365): Promise<number> {
    try {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - olderThanDays)

      const result = await this.prisma.publication.deleteMany({
        where: {
          created_at: {
            lt: cutoffDate,
          },
          status: 'CONCLUIDA', // Só deletar publicações concluídas
        },
      })

      return result.count
    } catch (error) {
      console.error('Error deleting old publications:', error)
      throw new Error('Failed to delete old publications')
    }
  }
}