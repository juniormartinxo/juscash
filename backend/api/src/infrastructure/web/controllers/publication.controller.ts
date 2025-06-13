import { GetPublicationByIdUseCase } from '../../../application/usecases/publications/get-publication-by-id.usecase.js'
import { GetPublicationsUseCase } from '../../../application/usecases/publications/get-publications.usecase.js'
import { SearchPublicationsUseCase } from '../../../application/usecases/publications/search-publications.usecase.js'
import { UpdatePublicationStatusUseCase } from '../../../application/usecases/publications/update-ublication-status.usecase.js'

export class PublicationController {
  constructor(
    private getPublicationsUseCase: GetPublicationsUseCase,
    private getPublicationByIdUseCase: GetPublicationByIdUseCase,
    private updatePublicationStatusUseCase: UpdatePublicationStatusUseCase,
    private searchPublicationsUseCase: SearchPublicationsUseCase
  ) { }

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

    const result = await this.getPublicationByIdUseCase.execute({ id })

    res.json(ApiResponseBuilder.success(result))
  });

  updateStatus = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params
    const { status } = req.body

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
