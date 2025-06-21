import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'
import { CheckSquare, RefreshCw, Wifi } from 'lucide-react'
import { PublicationCard } from './PublicationCard'
import { PublicationModal } from './PublicationModal'
import { useToast } from '@/hooks/use-toast'
import { usePublicationCount, useUpdatePublicationStatus } from '@/hooks/usePublications'
import { useScrapingCompletionDetector } from '@/hooks/useScraper'
import { apiService } from '@/services/api'
import { Publication, PublicationStatus, SearchFilters, KanbanColumn, PublicationStatusName } from '@/types'
import Spin from './Spin'

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
  const [preloadingColumns, setPreloadingColumns] = useState<Set<PublicationStatus>>(new Set())
  const [scrollDetected, setScrollDetected] = useState<Set<PublicationStatus>>(new Set())

  // Estado para controlar quando mostra indicador de polling
  const [lastPollingTime, setLastPollingTime] = useState<Date>(new Date())

  // UseRef para evitar loop infinito no useEffect
  const previousCountsRef = useRef<Map<PublicationStatus, number>>(new Map())

  const { toast } = useToast()

  // React Query hooks para buscar counts
  const novaCount = usePublicationCount(PublicationStatus.NOVA, filters)
  const lidaCount = usePublicationCount(PublicationStatus.LIDA, filters)
  const enviadaCount = usePublicationCount(PublicationStatus.ENVIADA_PARA_ADV, filters)
  const concluidaCount = usePublicationCount(PublicationStatus.CONCLUIDA, filters)

  // Hook para atualizar status
  const updateStatusMutation = useUpdatePublicationStatus()

  // Hook para detectar quando o scraping termina
  const { isScrapingRunning } = useScrapingCompletionDetector()

  // Detectar novos dados e mostrar notificação - CORRIGIDO para evitar loop infinito
  useEffect(() => {
    const currentCounts = new Map([
      [PublicationStatus.NOVA, novaCount.data ?? 0],
      [PublicationStatus.LIDA, lidaCount.data ?? 0],
      [PublicationStatus.ENVIADA_PARA_ADV, enviadaCount.data ?? 0],
      [PublicationStatus.CONCLUIDA, concluidaCount.data ?? 0],
    ])

    // Verificar se há novos dados (apenas após carregamento inicial)
    if (!loading && previousCountsRef.current.size > 0) {
      let hasNewData = false
      let newDataMessages: string[] = []

      currentCounts.forEach((currentCount, status) => {
        const previousCount = previousCountsRef.current.get(status) ?? 0
        if (currentCount > previousCount) {
          hasNewData = true
          const diff = currentCount - previousCount
          const statusName = PublicationStatusName[status]
          newDataMessages.push(`+${diff} em ${statusName}`)
        }
      })

      if (hasNewData) {
        toast({
          title: "📢 Novas publicações disponíveis!",
          description: newDataMessages.join(', '),
          duration: 4000,
        })
      }
    }

    // Atualizar ref sem causar re-render
    previousCountsRef.current = currentCounts
  }, [novaCount.data, lidaCount.data, enviadaCount.data, concluidaCount.data, loading, toast])

  // Atualizar timestamp do polling quando houver nova data
  useEffect(() => {
    if (novaCount.dataUpdatedAt || lidaCount.dataUpdatedAt || enviadaCount.dataUpdatedAt || concluidaCount.dataUpdatedAt) {
      setLastPollingTime(new Date())
    }
  }, [novaCount.dataUpdatedAt, lidaCount.dataUpdatedAt, enviadaCount.dataUpdatedAt, concluidaCount.dataUpdatedAt])

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
      const statusName = PublicationStatusName[status]
      console.error(`❌ Erro ao carregar publicações para ${status}:`, error)

      if (error instanceof Error) {
        console.error(`Error message: ${error.message}`)
        console.error(`Error stack:`, error.stack)
      }

      if (!isPreload) {
        toast({
          title: "Erro ao carregar publicações",
          description: `Erro ao carregar ${statusName}: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
          variant: "destructive",
          duration: 5000,
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

  // Handler de scroll otimizado
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>, status: PublicationStatus) => {
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
  }, [hasMore, loadingMore, loadMoreItems])

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
        duration: 4000,
      })
      return
    }

    const sourceColumn = columns.get(sourceStatus)
    const publication = sourceColumn?.publications.find(pub => pub.id === draggableId)

    if (!publication) {
      console.warn(`Publicação não encontrada: ${draggableId}`)
      return
    }

    console.log(`🚀 [KanbanBoard] Moving publication ${draggableId} from ${sourceStatus} to ${destStatus}`)

    // Atualização otimística APENAS das colunas (não dos contadores)
    setColumns(prev => {
      const newColumns = new Map(prev)

      const sourceCol = newColumns.get(sourceStatus)
      if (sourceCol) {
        newColumns.set(sourceStatus, {
          ...sourceCol,
          publications: sourceCol.publications.filter(pub => pub.id !== draggableId),
        })
      }

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
      await updateStatusMutation.mutateAsync({
        publicationId: publication.id,
        newStatus: destStatus
      })

      console.log(`✅ [KanbanBoard] Successfully moved publication ${draggableId}`)

    } catch (error) {
      console.error('❌ [KanbanBoard] Error moving publication:', error)

      // Reverter mudanças nas colunas em caso de erro
      await Promise.allSettled([
        loadPublications(sourceStatus, 1, true),
        loadPublications(destStatus, 1, true),
      ])
    }
  }, [columns, isValidMove, toast, updateStatusMutation, loadPublications])

  const handleCardClick = useCallback((publication: Publication) => {
    console.log('🖱️ [KanbanBoard] Card clicked:', publication.process_number)
    setSelectedPublication(publication)
    setIsModalOpen(true)
  }, [])

  const handleModalClose = useCallback(() => {
    console.log('❌ [KanbanBoard] Modal closing')
    setIsModalOpen(false)
    setSelectedPublication(null)
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="flex flex-row items-center gap-2">
          <Spin h={8} w={8} />
          <p>Carregando publicações...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-h-[calc(100vh-1000px)] mb-32 pb-32">
      {/* Indicador de scraping ativo */}
      {isScrapingRunning && (
        <div className="mb-4 bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-orange-800">
                Scraping em execução
              </span>
            </div>
            <span className="text-xs text-orange-600">
              Novas publicações serão exibidas automaticamente quando o processo for concluído
            </span>
          </div>
        </div>
      )}

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-4 gap-6 h-full">
          {columnOrder.map((status) => {
            const column = columns.get(status) || {
              id: status,
              title: COLUMN_CONFIG[status].title,
              publications: [],
              count: 0,
            }

            // Obter count atualizado diretamente do React Query
            const getColumnCount = () => {
              switch (status) {
                case PublicationStatus.NOVA:
                  return novaCount.data ?? 0
                case PublicationStatus.LIDA:
                  return lidaCount.data ?? 0
                case PublicationStatus.ENVIADA_PARA_ADV:
                  return enviadaCount.data ?? 0
                case PublicationStatus.CONCLUIDA:
                  return concluidaCount.data ?? 0
                default:
                  return 0
              }
            }

            const isLoadingMore = loadingMore.has(status)
            const isPreloading = preloadingColumns.has(status)

            // Verificar se o contador está carregando
            const isCountLoading = (() => {
              switch (status) {
                case PublicationStatus.NOVA:
                  return novaCount.isLoading || novaCount.isFetching
                case PublicationStatus.LIDA:
                  return lidaCount.isLoading || lidaCount.isFetching
                case PublicationStatus.ENVIADA_PARA_ADV:
                  return enviadaCount.isLoading || enviadaCount.isFetching
                case PublicationStatus.CONCLUIDA:
                  return concluidaCount.isLoading || concluidaCount.isFetching
                default:
                  return false
              }
            })()

            return (
              <div key={status} className="flex flex-col h-full">
                {/* Header da coluna */}
                <div className="rounded-t-lg border border-gray-200 bg-kanban-background p-4 flex flex-row justify-start items-center gap-4 h-16">
                  <h3 className="font-semibold text-sm text-secondary">
                    {column.title}
                  </h3>
                  <span className={`text-xs ${isCountLoading ? 'text-green-500 animate-pulse font-semibold' : 'text-gray-500'}`}>
                    {isCountLoading ? <Spin h={4} w={4} /> : getColumnCount()}
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
                        maxHeight: '70vh',
                        overflowY: 'auto'
                      }}
                      onScroll={(e) => handleScroll(e, status)}
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
                            <Spin h={4} w={4} />
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

                        {/* Indicador de fim dos dados */}
                        {!hasMore.get(status) && column.publications.length > 0 && (
                          <div className="text-center py-4 text-xs text-gray-400 border-t border-gray-200">
                            Todos os cards foram carregados {column.publications.length}/{getColumnCount()}
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