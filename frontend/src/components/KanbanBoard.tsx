import { useState, useEffect, useCallback } from 'react'
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
  CONCLUIDA: { title: <span className="flex flex-row items-center gap-1 text-primary"><CheckSquare className="inline-block -mt-1 mr-1" size={16} /> Concluído</span>, color: 'bg-kanban-background border-transparent' },
}

const ITEMS_PER_PAGE = 30

export function KanbanBoard({ filters }: KanbanBoardProps) {
  const [columns, setColumns] = useState<KanbanColumn[]>([])
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState<Record<PublicationStatus, boolean>>({
    NOVA: false,
    LIDA: false,
    ENVIADA_PARA_ADV: false,
    CONCLUIDA: false,
  })
  const [hasMore, setHasMore] = useState<Record<PublicationStatus, boolean>>({
    NOVA: true,
    LIDA: true,
    ENVIADA_PARA_ADV: true,
    CONCLUIDA: true,
  })
  const [currentPage, setCurrentPage] = useState<Record<PublicationStatus, number>>({
    NOVA: 1,
    LIDA: 1,
    ENVIADA_PARA_ADV: 1,
    CONCLUIDA: 1,
  })

  const { toast } = useToast()

  const loadPublications = useCallback(async (status: PublicationStatus, page: number = 1, reset: boolean = false) => {
    if (page === 1) {
      setLoading(true)
    } else {
      setLoadingMore(prev => ({ ...prev, [status]: true }))
    }

    try {
      const response = await apiService.getPublications(page, ITEMS_PER_PAGE, {
        ...filters,
        status,
      })

      setColumns(prev => {
        const newColumns = [...prev]
        const columnIndex = newColumns.findIndex(col => col.id === status)

        if (columnIndex >= 0) {
          const existingPublications = reset ? [] : newColumns[columnIndex].publications
          newColumns[columnIndex] = {
            ...newColumns[columnIndex],
            publications: [...existingPublications, ...response.data],
            count: response.total,
          }
        } else {
          newColumns.push({
            id: status,
            title: COLUMN_CONFIG[status].title,
            publications: response.data,
            count: response.total,
          })
        }

        return newColumns
      })

      setHasMore(prev => ({
        ...prev,
        [status]: response.page < response.totalPages,
      }))

      setCurrentPage(prev => ({
        ...prev,
        [status]: response.page,
      }))

    } catch (error) {
      toast({
        title: "Erro ao carregar publicações",
        description: "Não foi possível carregar as publicações. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setLoadingMore(prev => ({ ...prev, [status]: false }))
    }
  }, [filters, toast])

  // Carregar dados iniciais
  useEffect(() => {
    const loadAllColumns = async () => {
      setLoading(true)
      setColumns([])
      setCurrentPage({
        NOVA: 1,
        LIDA: 1,
        ENVIADA_PARA_ADV: 1,
        CONCLUIDA: 1,
      })

      // Carregar todas as colunas em paralelo
      await Promise.all([
        loadPublications(PublicationStatus.NOVA, 1, true),
        loadPublications(PublicationStatus.LIDA, 1, true),
        loadPublications(PublicationStatus.ENVIADA_PARA_ADV, 1, true),
        loadPublications(PublicationStatus.CONCLUIDA, 1, true),
      ])
    }

    loadAllColumns()
  }, [filters])

  const loadMoreItems = (status: PublicationStatus) => {
    if (!hasMore[status] || loadingMore[status]) return

    const nextPage = currentPage[status] + 1
    loadPublications(status, nextPage, false)
  }

  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result

    if (!destination) return

    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return
    }

    const sourceStatus = source.droppableId as PublicationStatus
    const destStatus = destination.droppableId as PublicationStatus

    // Validar movimentos permitidos
    if (!isValidMove(sourceStatus, destStatus)) {
      toast({
        title: "Movimento não permitido",
        description: "Este movimento entre colunas não é permitido.",
        variant: "destructive",
      })
      return
    }

    // Encontrar a publicação
    const sourceColumn = columns.find(col => col.id === sourceStatus)
    const publication = sourceColumn?.publications.find(pub => pub.id === draggableId)

    if (!publication) return

    // Atualizar estado local otimisticamente
    setColumns(prev => {
      const newColumns = [...prev]

      // Remover da coluna origem
      const sourceIndex = newColumns.findIndex(col => col.id === sourceStatus)
      if (sourceIndex >= 0) {
        newColumns[sourceIndex] = {
          ...newColumns[sourceIndex],
          publications: newColumns[sourceIndex].publications.filter(pub => pub.id !== draggableId),
        }
      }

      // Adicionar na coluna destino
      const destIndex = newColumns.findIndex(col => col.id === destStatus)
      if (destIndex >= 0) {
        const updatedPublication = { ...publication, status: destStatus }
        const destPublications = [...newColumns[destIndex].publications]
        destPublications.splice(destination.index, 0, updatedPublication)

        newColumns[destIndex] = {
          ...newColumns[destIndex],
          publications: destPublications,
        }
      }

      return newColumns
    })

    // Atualizar no backend
    try {
      await apiService.updatePublicationStatus(publication.id, destStatus)
    } catch (error) {
      // Reverter em caso de erro
      toast({
        title: "Erro ao atualizar status",
        description: "Não foi possível atualizar o status da publicação.",
        variant: "destructive",
      })

      // Recarregar dados
      loadPublications(sourceStatus, 1, true)
      loadPublications(destStatus, 1, true)
    }
  }

  const isValidMove = (from: PublicationStatus, to: PublicationStatus): boolean => {
    const validMoves: Record<PublicationStatus, PublicationStatus[]> = {
      NOVA: [PublicationStatus.NOVA],
      LIDA: [PublicationStatus.ENVIADA_PARA_ADV],
      ENVIADA_PARA_ADV: [PublicationStatus.CONCLUIDA, PublicationStatus.LIDA], // Permite voltar para LIDA
      CONCLUIDA: [], // Não pode mover para nenhuma
    }

    return validMoves[from].includes(to)
  }

  const handleCardClick = (publication: Publication) => {
    setSelectedPublication(publication)
    setIsModalOpen(true)
  }

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
          {Object.values(PublicationStatus).map((status) => {
            const column = columns.find(col => col.id === status) || {
              id: status,
              title: COLUMN_CONFIG[status].title,
              publications: [],
              count: 0,
            }

            return (
              <div key={status} className="flex flex-col h-full">
                {/* Header da coluna */}
                <div className={`rounded-t-lg border border-gray-200 bg-kanban-background p-4 flex flex-row justify-start items-center gap-4`}>
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
                        if (scrollTop + clientHeight >= scrollHeight - 5) {
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

                        {/* Loading indicator */}
                        {loadingMore[status] && (
                          <div className="flex justify-center py-4">
                            <div className="spinner" />
                          </div>
                        )}

                        {/* Empty state */}
                        {column.publications.length === 0 && !loadingMore[status] && (
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

      {/* Modal de detalhes */}
      <PublicationModal
        publication={selectedPublication}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  )
}