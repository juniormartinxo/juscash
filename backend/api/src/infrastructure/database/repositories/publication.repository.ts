import { PublicationEntity } from '@/domain/entities/publication.entity'
import {
  FindPublicationsParams,
  PublicationRepository,
  PublicationResult,
  CreatePublicationData
} from '@/domain/repositories/publication.repository'
import { PrismaClient } from '@/generated/prisma/index'

export class PrismaPublicationRepository implements PublicationRepository {
  constructor(private prisma: PrismaClient) { }

  async findById(id: string): Promise<PublicationEntity | null> {
    const publication = await this.prisma.publication.findUnique({
      where: { id },
    })

    return publication ? this.toDomain(publication) : null
  }

  async create(data: CreatePublicationData): Promise<PublicationEntity> {
    const createData: any = {
      process_number: data.processNumber,
      availability_date: data.availabilityDate,
      authors: data.authors,
      defendant: data.defendant || 'Instituto Nacional do Seguro Social - INSS',
      content: data.content,
      status: data.status || 'NOVA',
      scraping_source: data.scrapingSource || 'DJE-SP',
      caderno: data.caderno || '3',
      instancia: data.instancia || '1',
      local: data.local || 'Capital',
      parte: data.parte || '1',
    }

    if (data.publicationDate) createData.publication_date = data.publicationDate
    if (data.lawyers) createData.lawyers = data.lawyers
    if (data.grossValue) createData.gross_value = data.grossValue
    if (data.netValue) createData.net_value = data.netValue
    if (data.interestValue) createData.interest_value = data.interestValue
    if (data.attorneyFees) createData.attorney_fees = data.attorneyFees
    if (data.extractionMetadata) createData.extraction_metadata = data.extractionMetadata

    const publication = await this.prisma.publication.create({
      data: createData
    })

    return this.toDomain(publication)
  }

  async findMany(params: FindPublicationsParams): Promise<PublicationResult> {
    const { page = 1, limit = 30, status, startDate, endDate, searchTerm } = params
    const skip = (page - 1) * limit

    const where: any = {}

    if (status) {
      where.status = status
    }

    if (startDate || endDate) {
      where.availability_date = {}
      if (startDate) where.availability_date.gte = startDate
      if (endDate) where.availability_date.lte = endDate
    }

    if (searchTerm) {
      where.OR = [
        { process_number: { contains: searchTerm, mode: 'insensitive' } },
        { authors: { hasSome: [searchTerm] } },
        { content: { contains: searchTerm, mode: 'insensitive' } },
        {
          lawyers: {
            path: ['$[*]', 'name'],
            string_contains: searchTerm
          }
        },
      ]
    }

    const [publications, total] = await Promise.all([
      this.prisma.publication.findMany({
        where,
        skip,
        take: limit,
        orderBy: [
          { status: 'asc' }, // NOVA first
          { created_at: 'desc' }
        ],
      }),
      this.prisma.publication.count({ where }),
    ])

    return {
      publications: publications.map(p => this.toDomain(p)),
      total,
      page,
      totalPages: Math.ceil(total / limit),
    }
  }

  async updateStatus(id: string, status: PublicationEntity['status']): Promise<PublicationEntity> {
    const updated = await this.prisma.publication.update({
      where: { id },
      data: {
        status,
        updated_at: new Date(),
      },
    })

    return this.toDomain(updated)
  }

  async search(query: string): Promise<PublicationEntity[]> {
    const publications = await this.prisma.publication.findMany({
      where: {
        OR: [
          { process_number: { contains: query, mode: 'insensitive' } },
          { authors: { hasSome: [query] } },
          { content: { contains: query, mode: 'insensitive' } },
          {
            lawyers: {
              path: ['$[*]', 'name'],
              string_contains: query
            }
          },
        ],
      },
      take: 100, // Limit search results
      orderBy: [
        { status: 'asc' },
        { created_at: 'desc' }
      ],
    })

    return publications.map(p => this.toDomain(p))
  }

  private toDomain(publication: any): PublicationEntity {
    return {
      id: publication.id,
      processNumber: publication.process_number,
      publicationDate: publication.publication_date,
      availabilityDate: publication.availability_date,
      authors: publication.authors,
      defendant: publication.defendant,
      lawyers: publication.lawyers as Array<{ name: string; oab: string }>,
      grossValue: publication.gross_value,
      netValue: publication.net_value,
      interestValue: publication.interest_value,
      attorneyFees: publication.attorney_fees,
      content: publication.content,
      status: publication.status,
      createdAt: publication.created_at,
      updatedAt: publication.updated_at,
    }
  }
}
