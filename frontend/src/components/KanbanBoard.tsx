import { useState, useEffect, useCallback, useMemo } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import { CheckSquare } from 'lucide-react'
import { PublicationCard } from './PublicationCard'
import { PublicationModal } from './PublicationModal'
import { useToast } from '@/hooks/use-toast'
import { apiService } from '@/services/api'
import { Publication, PublicationStatus, SearchFilters, KanbanColumn } from '@/types'

interface KanbanBoardProps {
  filters: SearchFilters
}

const COLUMN_CONFIG: Record<PublicationStatus, { title: React.ReactNode; color: string }> = {
  NOVA: { title: 'Nova Publicação', color: 'bg-kanban-background border-transparent' },
  LIDA: { title: 'Publicação Lida', color: 'bg-kanban-background border-transparent' },
  ENVIADA_PARA_ADV: { title: 'Enviar para Advogado Responsável', color: 'bg-kanban-background border-transparent' },
  CONCLUIDA: { 
    title: (
      <span className="flex flex-row items-center gap-1 text-primary">
        <CheckSquare className="inline-block -mt-1 mr-1" size={16} /> 
        Concluído
      </span>
    ), 
    color: 'bg-kanban-background border-transparent' 
  },
}

const ITEMS_PER_PAGE = 30

// Regras de movimentação entre colunas
const VALID_MOVES: Record<PublicationStatus, PublicationStatus[]> = {
  NOVA: [PublicationStatus.LIDA],
  LIDA: [PublicationStatus.ENVIADA_PARA_ADV],
  ENVIADA_PARA_ADV: [PublicationStatus.CONCLUIDA, PublicationStatus.LIDA],
  CONCLUIDA: [],
}

export function KanbanBoard({ filters }: KanbanBoardProps) {
  const [columns, setColumns] = useState<Map<PublicationStatus, KanbanColumn>>(new Map())
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState<Set<PublicationStatus>>(new Set())
  const [hasMore, setHasMore] = useState<Map<PublicationStatus, boolean>>(new Map())
  const [currentPage, setCurrentPage] = useState<Map<PublicationStatus, number>>(new Map())

  const { toast } = useToast()

  // Memoizar configurações das colunas
  const columnOrder = useMemo(() => [
    PublicationStatus.NOVA,
    PublicationStatus.LIDA,
    PublicationStatus.ENVIADA_PARA_ADV,
    PublicationStatus.CONCLUIDA,
  ], [])

  const loadPublications = useCallback(async (
    status: PublicationStatus, 
    page: number = 1, 
    reset: boolean = false
  ) => {
    if (page === 1) {
      setLoading(true)
    } else {
      setLoadingMore(prev => new Set(prev).add(status))
    }

    try {
      const response = await apiService.getPublications(page, ITEMS_PER_PAGE, {
        ...filters,
        status,
      })

      // Verificação de segurança para garantir que data seja um array
      const publications = Array.isArray(response.data) ? response.data : []

      setColumns(prev => {
        const newColumns = new Map(prev)
        const existingColumn = newColumns.get(status)
        const existingPublications = reset ? [] : existingColumn?.publications || []

        newColumns.set(status, {
          id: status,
          title: COLUMN_CONFIG[status].title,
          publications: [...existingPublications, ...publications],
          count: response.total || 0,
        })

        return newColumns
      })

      setHasMore(prev => new Map(prev).set(status, response.page < response.totalPages))
      setCurrentPage(prev => new Map(prev).set(status, response.page))

    } catch (error) {
      console.error('Erro ao carregar publicações:', error)
      toast({
        title: "Erro ao carregar publicações",
        description: "Não foi possível carregar as publicações. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setLoadingMore(prev => {
        const newSet = new Set(prev)
        newSet.delete(status)
        return newSet
      })
    }
  }, [filters, toast])

  // Carregar dados iniciais sequencialmente para evitar rate limiting
  useEffect(() => {
    const loadAllColumns = async () => {
      setLoading(true)
      setColumns(new Map())
      setCurrentPage(new Map(columnOrder.map(status => [status, 1])))
      setHasMore(new Map(columnOrder.map(status => [status, true])))

      // Carregar sequencialmente para evitar rate limiting
      for (const status of columnOrder) {
        await loadPublications(status, 1, true)
      }
    }

    loadAllColumns()
  }, [filters, columnOrder, loadPublications])

  const loadMoreItems = useCallback((status: PublicationStatus) => {
    const hasMoreItems = hasMore.get(status)
    const isLoading = loadingMore.has(status)
    
    if (!hasMoreItems || isLoading) return

    const nextPage = (currentPage.get(status) || 1) + 1
    loadPublications(status, nextPage, false)
  }, [hasMore, loadingMore, currentPage, loadPublications])

  const isValidMove = useCallback((from: PublicationStatus, to: PublicationStatus): boolean => {
    return VALID_MOVES[from]?.includes(to) || false
  }, [])

  const handleDragEnd = useCallback(async (result: DropResult) => {
    const { destination, source, draggableId } = result

    if (!destination || (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    )) {
      return
    }

    const sourceStatus = source.droppableId as PublicationStatus
    const destStatus = destination.droppableId as PublicationStatus

    if (!isValidMove(sourceStatus, destStatus)) {
      toast({
        title: "Movimento não permitido",
        description: "Este movimento entre colunas não é permitido.",
        variant: "destructive",
      })
      return
    }

    const sourceColumn = columns.get(sourceStatus)
    const publication = sourceColumn?.publications.find(pub => pub.id === draggableId)

    if (!publication) return

    // Atualização otimística
    setColumns(prev => {
      const newColumns = new Map(prev)

      // Remover da origem
      const sourceCol = newColumns.get(sourceStatus)
      if (sourceCol) {
        newColumns.set(sourceStatus, {
          ...sourceCol,
          publications: sourceCol.publications.filter(pub => pub.id !== draggableId),
        })
      }

      // Adicionar no destino
      const destCol = newColumns.get(destStatus)
      if (destCol) {
        const updatedPublication = { ...publication, status: destStatus }
        const destPublications = [...destCol.publications]
        destPublications.splice(destination.index, 0, updatedPublication)

        newColumns.set(destStatus, {
          ...destCol,
          publications: destPublications,
        })
      }

      return newColumns
    })

    try {
      await apiService.updatePublicationStatus(publication.id, destStatus)
    } catch (error) {
      console.error('Erro ao atualizar status:', error)
      toast({
        title: "Erro ao atualizar status",
        description: "Não foi possível atualizar o status da publicação.",
        variant: "destructive",
      })

      // Recarregar em caso de erro
      await Promise.allSettled([
        loadPublications(sourceStatus, 1, true),
        loadPublications(destStatus, 1, true),
      ])
    }
  }, [columns, isValidMove, toast, loadPublications])

  const handleCardClick = useCallback((publication: Publication) => {
    setSelectedPublication(publication)
    setIsModalOpen(true)
  }, [])

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false)
    setSelectedPublication(null)
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="h-full">
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-4 gap-6 h-full">
          {columnOrder.map((status) => {
            const column = columns.get(status) || {
              id: status,
              title: COLUMN_CONFIG[status].title,
              publications: [],
              count: 0,
            }

            const isLoadingMore = loadingMore.has(status)

            return (
              <div key={status} className="flex flex-col h-full">
                {/* Header da coluna */}
                <div className="rounded-t-lg border border-gray-200 bg-kanban-background p-4 flex flex-row justify-start items-center gap-4">
                  <h3 className="font-semibold text-sm text-secondary">
                    {column.title}
                  </h3>
                  <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-1">
                    {column.publications.length}
                  </span>
                </div>

                {/* Conteúdo da coluna */}
                <Droppable droppableId={status}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      className={`
                        kanban-column flex-1 p-4 border-l-2 border-r-2 border-b-2 rounded-b-lg
                        ${COLUMN_CONFIG[status].color}
                        ${snapshot.isDraggingOver ? 'bg-opacity-50' : ''}
                        overflow-y-auto scrollbar-hide
                      `}
                      style={{ minHeight: '500px' }}
                      onScroll={(e) => {
                        const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
                        if (scrollTop + clientHeight >= scrollHeight - 10) {
                          loadMoreItems(status)
                        }
                      }}
                    >
                      <div className="space-y-3">
                        {column.publications.map((publication, index) => (
                          <Draggable
                            key={publication.id}
                            draggableId={publication.id}
                            index={index}
                          >
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                              >
                                <PublicationCard
                                  publication={publication}
                                  onClick={() => handleCardClick(publication)}
                                  isDragging={snapshot.isDragging}
                                />
                              </div>
                            )}
                          </Draggable>
                        ))}

                        {isLoadingMore && (
                          <div className="flex justify-center py-4">
                            <div className="spinner" />
                          </div>
                        )}

                        {column.publications.length === 0 && !isLoadingMore && (
                          <div className="text-center py-8 text-gray-500 text-sm">
                            Nenhum card encontrado
                          </div>
                        )}
                      </div>
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            )
          })}
        </div>
      </DragDropContext>

      <PublicationModal
        publication={selectedPublication}
        isOpen={isModalOpen}
        onClose={handleModalClose}
      />
    </div>
  )
}