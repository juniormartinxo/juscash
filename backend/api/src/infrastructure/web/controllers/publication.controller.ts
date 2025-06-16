import { GetPublicationByIdUseCase } from '@/application/usecases/publications/get-publication-by-id.usecase'
import { GetPublicationsUseCase } from '@/application/usecases/publications/get-publications.usecase'
import { SearchPublicationsUseCase } from '@/application/usecases/publications/search-publications.usecase'
import { UpdatePublicationStatusUseCase } from '@/application/usecases/publications/update-publication-status.usecase'
import { CreatePublicationUseCase, ValidationError } from '@/application/usecases/publications/create-publication.usecase'
import { asyncHandler } from '@/shared/utils/async-handler'
import { ApiResponseBuilder } from '@/shared/utils/api-response'
import { ConflictError } from '@/shared/utils/error-handler'
import { Request, Response } from 'express'

export class PublicationController {
  constructor(
    private getPublicationsUseCase: GetPublicationsUseCase,
    private getPublicationByIdUseCase: GetPublicationByIdUseCase,
    private updatePublicationStatusUseCase: UpdatePublicationStatusUseCase,
    private searchPublicationsUseCase: SearchPublicationsUseCase,
    private createPublicationUseCase: CreatePublicationUseCase
  ) { }

  createPublication = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    try {
      const result = await this.createPublicationUseCase.execute(req.body)
      res.status(201).json(ApiResponseBuilder.success(result))
    } catch (error) {
      if (error instanceof ValidationError) {
        res.status(400).json(ApiResponseBuilder.error(error.message))
        return
      }
      if (error instanceof ConflictError) {
        res.status(409).json(ApiResponseBuilder.error(error.message))
        return
      }
      throw error
    }
  });

  /**
   * Método específico para criação de publicações via scraper
   * Usa a mesma lógica do createPublication, mas com logs específicos para auditoria
   */
  createPublicationFromScraper = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    try {
      // Log específico para identificar origem do scraper
      console.log('Publication creation from SCRAPER:', {
        processNumber: req.body.processNumber,
        source: 'SCRAPER',
        timestamp: new Date().toISOString(),
        ip: req.ip,
        userAgent: req.get('User-Agent')
      })

      const result = await this.createPublicationUseCase.execute(req.body)

      // Log de sucesso específico para scraper
      console.log('Publication created successfully from SCRAPER:', {
        publicationId: result.publication.id,
        processNumber: result.publication.processNumber,
        source: 'SCRAPER'
      })

      res.status(201).json(ApiResponseBuilder.success(result))
    } catch (error) {
      // Log de erro específico para scraper
      console.error('Publication creation failed from SCRAPER:', {
        error: error instanceof Error ? error.message : 'Unknown error',
        processNumber: req.body?.processNumber,
        source: 'SCRAPER',
        ip: req.ip
      })

      if (error instanceof ValidationError) {
        res.status(400).json(ApiResponseBuilder.error(error.message))
        return
      }
      if (error instanceof ConflictError) {
        // Para o scraper, tratar duplicatas como sucesso (200) ao invés de conflito
        console.log('Publication already exists (SCRAPER):', {
          processNumber: req.body?.processNumber,
          message: 'Publication skipped - already exists',
          source: 'SCRAPER'
        })
        res.status(200).json(ApiResponseBuilder.success({
          message: 'Publication already exists',
          processNumber: req.body?.processNumber,
          skipped: true
        }))
        return
      }
      throw error
    }
  });

  getPublications = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { page, limit, status, startDate, endDate, search } = req.query as any

    const result = await this.getPublicationsUseCase.execute({
      page,
      limit,
      status,
      startDate,
      endDate,
      searchTerm: search,
    })

    res.json(ApiResponseBuilder.success(result))
  });

  getPublicationById = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params

    if (!id) {
      res.status(400).json(ApiResponseBuilder.error('ID is required'))
      return
    }

    const result = await this.getPublicationByIdUseCase.execute({ id })

    res.json(ApiResponseBuilder.success(result))
  });

  updateStatus = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params
    const { status } = req.body

    if (!id) {
      res.status(400).json(ApiResponseBuilder.error('ID is required'))
      return
    }

    const result = await this.updatePublicationStatusUseCase.execute({
      publicationId: id,
      newStatus: status,
    })

    res.json(ApiResponseBuilder.success(result))
  });

  search = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { q: query } = req.query as { q: string }

    if (!query) {
      res.status(400).json(ApiResponseBuilder.error('Query parameter "q" is required'))
      return
    }

    const result = await this.searchPublicationsUseCase.execute({ query })

    res.json(ApiResponseBuilder.success(result))
  });
}
