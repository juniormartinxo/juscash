import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
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
const PRELOAD_THRESHOLD = 0.8 // Carregar quando 80% do scroll for atingido
const SCROLL_THROTTLE_MS = 150

// Regras de movimentação entre colunas
const VALID_MOVES: Record<PublicationStatus, PublicationStatus[]> = {
  NOVA: [PublicationStatus.LIDA],
  LIDA: [PublicationStatus.ENVIADA_PARA_ADV],
  ENVIADA_PARA_ADV: [PublicationStatus.CONCLUIDA, PublicationStatus.LIDA],
  CONCLUIDA: [],
}

// Hook personalizado para throttling
function useThrottle<T extends (...args: any[]) => any>(callback: T, delay: number) {
  const lastCall = useRef<number>(0)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  return useCallback((...args: Parameters<T>) => {
    const now = Date.now()

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    if (now - lastCall.current >= delay) {
      lastCall.current = now
      callback(...args)
    } else {
      timeoutRef.current = setTimeout(() => {
        lastCall.current = Date.now()
        callback(...args)
      }, delay - (now - lastCall.current))
    }
  }, [callback, delay])
}

export function KanbanBoard({ filters }: KanbanBoardProps) {
  const [columns, setColumns] = useState<Map<PublicationStatus, KanbanColumn>>(new Map())
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState<Set<PublicationStatus>>(new Set())
  const [hasMore, setHasMore] = useState<Map<PublicationStatus, boolean>>(new Map())
  const [currentPage, setCurrentPage] = useState<Map<PublicationStatus, number>>(new Map())
  const [preloadingColumns, setPreloadingColumns] = useState<Set<PublicationStatus>>(new Set())
  const [scrollDetected, setScrollDetected] = useState<Set<PublicationStatus>>(new Set())

  const { toast } = useToast()

  // Debug: verificar autenticação
  console.log('🔐 Authentication status:', {
    isAuthenticated: apiService.isAuthenticated(),
    currentUser: apiService.getCurrentUser(),
    token: localStorage.getItem('accessToken') ? 'Present' : 'Missing'
  })

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
    reset: boolean = false,
    isPreload: boolean = false
  ) => {
    if (page === 1 && !isPreload) {
      setLoading(true)
    } else if (!isPreload) {
      setLoadingMore(prev => new Set(prev).add(status))
    } else {
      setPreloadingColumns(prev => new Set(prev).add(status))
    }

    try {
      console.log(`🔄 API call for ${status}, page ${page}, filters:`, filters)
      const response = await apiService.getPublications(page, ITEMS_PER_PAGE, {
        ...filters,
        status,
      })

      console.log(`📦 Raw API response for ${status}:`, response)

      // Verificação de segurança para garantir que data seja um array
      const publications = Array.isArray(response.data) ? response.data : []
      console.log(`✅ Processed ${publications.length} publications for ${status}, total: ${response.total}`)

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
      console.error(`❌ Erro ao carregar publicações para ${status}:`, error)

      // Log detalhado do erro
      if (error instanceof Error) {
        console.error(`Error message: ${error.message}`)
        console.error(`Error stack:`, error.stack)
      }

      if (!isPreload) {
        toast({
          title: "Erro ao carregar publicações",
          description: `Erro ao carregar ${status}: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
          variant: "destructive",
        })
      }
    } finally {
      setLoading(false)
      setLoadingMore(prev => {
        const newSet = new Set(prev)
        newSet.delete(status)
        return newSet
      })
      setPreloadingColumns(prev => {
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
        console.log(`Loading initial data for ${status}`)
        await loadPublications(status, 1, true)
      }
    }

    loadAllColumns()
  }, [filters, columnOrder, loadPublications])

  const loadMoreItems = useCallback((status: PublicationStatus, isPreload: boolean = false) => {
    const hasMoreItems = hasMore.get(status)
    const isLoading = loadingMore.has(status)
    const isPreloading = preloadingColumns.has(status)

    if (!hasMoreItems || isLoading || isPreloading) return

    const nextPage = (currentPage.get(status) || 1) + 1
    loadPublications(status, nextPage, false, isPreload)
  }, [hasMore, loadingMore, preloadingColumns, currentPage, loadPublications])

  // Função de scroll otimizada com throttling e pre-loading
  const handleColumnScroll = useCallback((status: PublicationStatus, event: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight

    console.log(`Scroll em ${status}:`, {
      scrollTop,
      scrollHeight,
      clientHeight,
      scrollPercentage,
      hasMore: hasMore.get(status),
      isLoading: loadingMore.has(status),
      isPreloading: preloadingColumns.has(status)
    })

    // Pre-loading inteligente quando atinge 80% do scroll
    if (scrollPercentage >= PRELOAD_THRESHOLD && scrollPercentage < 0.95) {
      console.log(`Triggering preload for ${status}`)
      loadMoreItems(status, true)
    }

    // Carregamento normal quando chega ao final
    if (scrollTop + clientHeight >= scrollHeight - 10) {
      console.log(`Triggering load more for ${status}`)
      loadMoreItems(status, false)
    }
  }, [hasMore, loadingMore, preloadingColumns, loadMoreItems])

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

    if (!publication) {
      console.warn(`Publicação não encontrada: ${draggableId}`)
      return
    }

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

      // Reverter mudanças e recarregar em caso de erro
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
        <div className="ml-4">
          <p>Carregando publicações...</p>
          {process.env.NODE_ENV === 'development' && (
            <button
              onClick={() => {
                console.log('🔧 Debug: Clearing auth and redirecting to login')
                apiService.clearCache()
                localStorage.clear()
                window.location.href = '/login'
              }}
              className="mt-2 px-3 py-1 bg-red-500 text-white rounded text-xs"
            >
              🔧 Reset Auth (Debug)
            </button>
          )}
        </div>
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
            const isPreloading = preloadingColumns.has(status)

            return (
              <div key={status} className="flex flex-col h-full">
                {/* Header da coluna */}
                <div className="rounded-t-lg border border-gray-200 bg-kanban-background p-4 flex flex-row justify-start items-center gap-4">
                  <h3 className="font-semibold text-sm text-secondary">
                    {column.title}
                  </h3>
                  <span className="text-xs text-gray-500 bg-gray-100 rounded-full px-2 py-1">
                    {column.publications.length}
                    {column.count > column.publications.length &&
                      <span className="text-gray-400">/{column.count}</span>
                    }
                  </span>
                  {isPreloading && (
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"
                      title="Pré-carregando..." />
                  )}
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
                      style={{
                        minHeight: '500px',
                        maxHeight: '70vh', // Garantir que tenha scroll
                        overflowY: 'auto' // Forçar scroll
                      }}
                      onScroll={(e) => {
                        const { scrollTop, scrollHeight, clientHeight } = e.currentTarget

                        // Indicar visualmente que o scroll foi detectado
                        setScrollDetected(prev => new Set(prev).add(status))
                        setTimeout(() => {
                          setScrollDetected(prev => {
                            const newSet = new Set(prev)
                            newSet.delete(status)
                            return newSet
                          })
                        }, 500)

                        // Verificar se está próximo do final (100px de margem)
                        const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100

                        if (isNearBottom && hasMore.get(status) && !loadingMore.has(status)) {
                          console.log(`🔄 Loading more for ${status}`)
                          loadMoreItems(status, false)
                        }
                      }}
                    >
                      <div className="space-y-3">
                        {column.publications
                          .filter(publication => publication && publication.id)
                          .map((publication, index) => (
                            <Draggable
                              key={`${status}-${publication.id}`}
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
                            <span className="ml-2 text-sm text-gray-500">
                              Carregando mais cards...
                            </span>
                          </div>
                        )}

                        {column.publications.length === 0 && !isLoadingMore && (
                          <div className="text-center py-8 text-secondary/75 text-sm">
                            Nenhum card encontrado
                          </div>
                        )}

                        {/* Debug Info - Simples */}
                        {process.env.NODE_ENV === 'development' && (
                          <div className="text-center py-1 text-xs text-gray-500 border-t">
                            {column.publications.length}/{column.count} | P:{currentPage.get(status) || 1} |
                            {hasMore.get(status) ? '📄 Tem mais' : '🔚 Fim'} |
                            {scrollDetected.has(status) && '📜 Scroll OK'}
                            {hasMore.get(status) && (
                              <button
                                onClick={() => loadMoreItems(status, false)}
                                className="ml-2 px-1 py-0 bg-blue-500 text-white rounded text-xs"
                                disabled={loadingMore.has(status)}
                              >
                                +
                              </button>
                            )}
                          </div>
                        )}

                        {/* Indicador de fim dos dados */}
                        {!hasMore.get(status) && column.publications.length > 0 && (
                          <div className="text-center py-4 text-xs text-gray-400 border-t border-gray-200">
                            Todos os cards foram carregados
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