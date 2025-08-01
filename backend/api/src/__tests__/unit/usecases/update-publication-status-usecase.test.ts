import { beforeEach, describe, expect, it, jest } from '@jest/globals'
import { UpdatePublicationStatusUseCase } from '@/application/usecases/publications/update-publication-status.usecase'
import { PublicationJsonEntity } from '@/domain/entities/publication.entity'
import { PublicationRepository } from '@/domain/repositories/publication.repository'

const mockPublicationRepository: jest.Mocked<PublicationRepository> = {
  findById: jest.fn(),
  findByProcessNumber: jest.fn(),
  findMany: jest.fn(),
  updateStatus: jest.fn(),
  search: jest.fn(),
  create: jest.fn(),
  upsert: jest.fn(),
}

describe('UpdatePublicationStatusUseCase', () => {
  let useCase: UpdatePublicationStatusUseCase

  beforeEach(() => {
    jest.clearAllMocks()
    useCase = new UpdatePublicationStatusUseCase(mockPublicationRepository)
  })

  const mockPublication: PublicationJsonEntity = {
    id: 'pub-123',
    process_number: '1234567-89.2024.8.26.0100',
    availability_date: new Date('2024-03-17'),
    authors: ['João Silva'],
    defendant: 'Instituto Nacional do Seguro Social - INSS',
    content: 'Test content',
    status: 'NOVA',
    scraping_source: 'DJE-SP',
    caderno: '3',
    instancia: '1',
    local: 'Capital',
    parte: '1',
    gross_value: null,
    net_value: null,
    interest_value: null,
    attorney_fees: null,
    publication_date: null,
    lawyers: null,
    extraction_metadata: null,
    createdAt: new Date(),
    updatedAt: new Date(),
  }

  describe('Valid transitions', () => {
    it('should allow NOVA -> LIDA transition', async () => {
      // Arrange
      mockPublicationRepository.findById.mockResolvedValue(mockPublication)
      mockPublicationRepository.updateStatus.mockResolvedValue({
        ...mockPublication,
        status: 'LIDA',
      })

      // Act
      const result = await useCase.execute({
        publicationId: 'pub-123',
        newStatus: 'LIDA',
      })

      // Assert
      expect(result.status).toBe('LIDA')
      expect(mockPublicationRepository.updateStatus).toHaveBeenCalledWith('pub-123', 'LIDA')
    })

    it('should allow LIDA -> ENVIADA_PARA_ADV transition', async () => {
      // Arrange
      const lidaPublication = { ...mockPublication, status: 'LIDA' as const }
      mockPublicationRepository.findById.mockResolvedValue(lidaPublication)
      mockPublicationRepository.updateStatus.mockResolvedValue({
        ...lidaPublication,
        status: 'ENVIADA_PARA_ADV',
      })

      // Act
      const result = await useCase.execute({
        publicationId: 'pub-123',
        newStatus: 'ENVIADA_PARA_ADV',
      })

      // Assert
      expect(result.status).toBe('ENVIADA_PARA_ADV')
    })

    it('should allow ENVIADA_PARA_ADV -> LIDA reverse transition', async () => {
      // Arrange
      const enviadaPublication = { ...mockPublication, status: 'ENVIADA_PARA_ADV' as const }
      mockPublicationRepository.findById.mockResolvedValue(enviadaPublication)
      mockPublicationRepository.updateStatus.mockResolvedValue({
        ...enviadaPublication,
        status: 'LIDA',
      })

      // Act
      const result = await useCase.execute({
        publicationId: 'pub-123',
        newStatus: 'LIDA',
      })

      // Assert
      expect(result.status).toBe('LIDA')
    })
  })

  describe('Invalid transitions', () => {
    it('should reject NOVA -> CONCLUIDA transition', async () => {
      // Arrange
      mockPublicationRepository.findById.mockResolvedValue(mockPublication)

      // Act & Assert
      await expect(useCase.execute({
        publicationId: 'pub-123',
        newStatus: 'CONCLUIDA',
      })).rejects.toThrow('Invalid status transition from NOVA to CONCLUIDA')
    })

    it('should reject CONCLUIDA -> any transition', async () => {
      // Arrange
      const concluidaPublication = { ...mockPublication, status: 'CONCLUIDA' as const }
      mockPublicationRepository.findById.mockResolvedValue(concluidaPublication)

      // Act & Assert
      await expect(useCase.execute({
        publicationId: 'pub-123',
        newStatus: 'LIDA',
      })).rejects.toThrow('Invalid status transition from CONCLUIDA to LIDA')
    })
  })

  describe('Error cases', () => {
    it('should throw error when publication not found', async () => {
      // Arrange
      mockPublicationRepository.findById.mockResolvedValue(null)

      // Act & Assert
      await expect(useCase.execute({
        publicationId: 'non-existent',
        newStatus: 'LIDA',
      })).rejects.toThrow('Publication not found')
    })
  })
})
