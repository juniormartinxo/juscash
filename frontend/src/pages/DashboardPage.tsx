import { useState, useEffect } from 'react'
import { Scale, X, Calendar, Play, Loader2, AlertCircle, CheckCircle, RefreshCw, StopCircle } from 'lucide-react'
import { TbClockCog } from 'react-icons/tb'
import { Navbar } from '@/components/Navbar'
import { SearchFiltersComponent } from '@/components/SearchFilters'
import { KanbanBoard } from '@/components/KanbanBoard'
import { useToast } from '@/hooks/use-toast'
import { useScraperStatus, useStartScraping, useStopScraping, useRefreshScraperStatus } from '@/hooks/useScraper'
import type { SearchFilters, ScrapingRequest } from '@/types'

export function DashboardPage() {
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    startDate: '',
    endDate: '',
  })
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isDrawerAnimating, setIsDrawerAnimating] = useState(false)

  // Estados do formulário de scraping
  const [useCurrentDate, setUseCurrentDate] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const { toast } = useToast()

  // Hooks do React Query para o scraper
  const { data: scraperStatus, isLoading: isLoadingStatus, error: statusError } = useScraperStatus()
  const startScrapingMutation = useStartScraping()
  const stopScrapingMutation = useStopScraping()
  const refreshStatus = useRefreshScraperStatus()

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
  }

  const getCurrentDate = () => {
    const now = new Date()
    return now.toISOString().split('T')[0]
  }

  const formatDateToBrazilian = (dateString: string) => {
    // Converte YYYY-MM-DD para DD/MM/YYYY
    const [year, month, day] = dateString.split('-')
    return `${day}/${month}/${year}`
  }

  const handleOpenDrawer = () => {
    setIsDrawerOpen(true)
    setIsDrawerAnimating(true)
    // Pequeno delay para iniciar a animação após o elemento estar no DOM
    requestAnimationFrame(() => {
      setTimeout(() => setIsDrawerAnimating(false), 10)
    })
  }

  const handleCloseDrawer = () => {
    setIsDrawerAnimating(true)
    // Aguarda a animação completar antes de remover o drawer do DOM
    setTimeout(() => {
      setIsDrawerOpen(false)
      setIsDrawerAnimating(false)
    }, 350) // 350ms duração da animação + buffer
  }

  // Fechar drawer com ESC
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isDrawerOpen && !isDrawerAnimating) {
        handleCloseDrawer()
      }
    }

    if (isDrawerOpen) {
      document.addEventListener('keydown', handleEscKey)
      return () => document.removeEventListener('keydown', handleEscKey)
    }
  }, [isDrawerOpen, isDrawerAnimating])

  const handleStartScraping = async () => {
    try {
      // Verificar se scraping já está rodando
      if (scraperStatus?.status.scraping) {
        toast({
          title: "Scraping já em execução",
          description: "Aguarde o scraping atual terminar antes de iniciar outro.",
          variant: "destructive",
        })
        return
      }

      let finalStartDate = startDate
      let finalEndDate = endDate

      if (useCurrentDate) {
        const currentDate = getCurrentDate()
        finalStartDate = currentDate
        finalEndDate = currentDate
      } else {
        // Validação das datas quando não usar data atual
        if (!startDate || !endDate) {
          toast({
            title: "Erro de validação",
            description: "Por favor, preencha ambas as datas.",
            variant: "destructive",
          })
          return
        }

        if (new Date(startDate) > new Date(endDate)) {
          toast({
            title: "Erro de validação",
            description: "A data inicial não pode ser posterior à data final.",
            variant: "destructive",
          })
          return
        }
      }

      const request: ScrapingRequest = {
        start_date: finalStartDate,
        end_date: finalEndDate,
        headless: true
      }

      await startScrapingMutation.mutateAsync(request)

      // Limpar o formulário
      setStartDate('')
      setEndDate('')
      setUseCurrentDate(false)

    } catch (error) {
      // Erro já tratado no hook
    }
  }

  const handleForceStopScraping = async () => {
    try {
      await stopScrapingMutation.mutateAsync()
    } catch (error) {
      // Erro já tratado no hook
    }
  }

  const getStatusDisplay = () => {
    if (!scraperStatus) return null

    const isScrapingRunning = scraperStatus.status.scraping
    const isMonitorRunning = scraperStatus.status.monitor

    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">Status dos Serviços</h3>
          <button
            onClick={() => refreshStatus()}
            disabled={isLoadingStatus}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title="Atualizar status"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoadingStatus ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Scraping:</span>
            <div className="flex items-center space-x-2">
              {isScrapingRunning ? (
                <>
                  <Loader2 className="w-4 h-4 text-orange-500 animate-spin" />
                  <span className="font-medium text-orange-600">Em execução</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium text-green-600">Parado</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-gray-600">Monitor:</span>
            <div className="flex items-center space-x-2">
              {isMonitorRunning ? (
                <>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium text-green-600">Ativo</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-gray-400" />
                  <span className="font-medium text-gray-500">Inativo</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const isScrapingDisabled = () => {
    return (
      startScrapingMutation.isPending ||
      stopScrapingMutation.isPending ||
      scraperStatus?.status.scraping ||
      (!useCurrentDate && (!startDate || !endDate))
    )
  }

  return (
    <div className="min-h-screen bg-background min-w-[1000px]">
      {/* Navbar fixa */}
      <Navbar />

      {/* Conteúdo principal */}
      <main className="pt-16"> {/* pt-16 para compensar a navbar fixa */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header da página */}
          <div className="mb-8 flex flex-col md:flex-row md:justify-between md:items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <Scale className="h-6 w-6 text-secondary" />
              <h1 className="text-3xl font-semibold text-secondary">
                Publicações
              </h1>
            </div>

            {/* Filtros de busca */}
            <SearchFiltersComponent onFiltersChange={handleFiltersChange} />
          </div>

          {/* Board Kanban */}
          <div className="min-h-72"> {/* Altura fixa para o kanban */}
            <KanbanBoard filters={filters} />
          </div>

          {/* Botão tipo aba no canto direito */}
          <div className="fixed right-0 top-1/2 transform -translate-y-1/2 z-10">
            <button
              onClick={handleOpenDrawer}
              className="bg-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-l-lg p-4 border border-r-0 border-gray-200 hover:translate-x-1 cursor-pointer relative"
              title="Configurações"
            >
              <TbClockCog size={24} className="text-primary" />
              {/* Indicador de status quando scraping está rodando */}
              {scraperStatus?.status.scraping && (
                <span className="relative -top-11 -left-5  flex size-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange-400 opacity-75"></span>
                  <span className="relative inline-flex size-3 rounded-full bg-orange-500"></span>
                </span>
              )}
            </button>
          </div>
        </div>
      </main>

      {/* Drawer */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Overlay */}
          <div
            className={`absolute inset-0 bg-black/45 transition-all duration-300 ease-out ${isDrawerAnimating ? 'opacity-0' : 'opacity-100'
              }`}
            onClick={handleCloseDrawer}
          />

          {/* Drawer content */}
          <div
            className={`absolute right-0 top-0 h-full w-96 bg-white shadow-2xl transform transition-all duration-300 ease-out ${isDrawerAnimating ? 'translate-x-full opacity-95' : 'translate-x-0 opacity-100'
              }`}
            style={{
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 10px 20px -6px rgba(0, 0, 0, 0.1)'
            }}
          >
            <div className={`flex flex-col h-full transition-all duration-300 delay-75 ${isDrawerAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
              }`}>
              {/* Header */}
              <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <TbClockCog size={20} className="text-primary" />
                  <h2 className="text-lg font-semibold text-gray-900">
                    Iniciar Scraping
                  </h2>
                </div>
                <button
                  onClick={handleCloseDrawer}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                >
                  <X size={20} className="text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="space-y-6">
                  {/* Status dos serviços */}
                  {getStatusDisplay()}

                  {/* Conteúdo condicional: Se scraping está rodando, mostra botão de parada; senão, mostra formulário */}
                  {scraperStatus?.status.scraping ? (
                    /* Seção de parada quando scraping está rodando */
                    <div className="space-y-4">
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-orange-800 font-medium">
                            Scraping em execução
                          </span>
                        </div>
                        <p className="text-sm text-orange-700 mt-1">
                          O scraping está coletando dados. Você pode aguardar a conclusão ou forçar a parada.
                        </p>
                      </div>

                      {/* Botão para forçar parada */}
                      <button
                        onClick={handleForceStopScraping}
                        disabled={stopScrapingMutation.isPending}
                        className="w-full bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                      >
                        {stopScrapingMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Parando...</span>
                          </>
                        ) : (
                          <>
                            <StopCircle className="w-4 h-4" />
                            <span>Forçar Parada</span>
                          </>
                        )}
                      </button>
                    </div>
                  ) : (
                    /* Seção do formulário quando scraping não está rodando */
                    <div className="space-y-6">
                      {/* Checkbox para usar data atual */}
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          id="useCurrentDate"
                          checked={useCurrentDate}
                          onChange={(e) => setUseCurrentDate(e.target.checked)}
                          disabled={startScrapingMutation.isPending}
                          className="w-4 h-4 text-primary bg-gray-100 border-gray-300 rounded focus:ring-primary focus:ring-2 disabled:opacity-50"
                        />
                        <label htmlFor="useCurrentDate" className="text-sm font-medium text-gray-700">
                          Usar data atual (hoje)
                        </label>
                      </div>

                      {/* Campos de data - aparecem apenas quando checkbox não está marcado */}
                      {!useCurrentDate && (
                        <>
                          <div className="space-y-2">
                            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
                              Data Inicial
                            </label>
                            <div className="relative">
                              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                              <input
                                type="date"
                                id="startDate"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                disabled={startScrapingMutation.isPending}
                                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:bg-gray-50"
                                required
                              />
                            </div>
                          </div>

                          <div className="space-y-2">
                            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
                              Data Final
                            </label>
                            <div className="relative">
                              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                              <input
                                type="date"
                                id="endDate"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                disabled={startScrapingMutation.isPending}
                                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:bg-gray-50"
                                required
                              />
                            </div>
                          </div>
                        </>
                      )}

                      {/* Informação sobre a data atual quando checkbox está marcado */}
                      {useCurrentDate && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-center space-x-2">
                            <Calendar className="w-4 h-4 text-blue-600" />
                            <span className="text-sm text-blue-800">
                              Scraping será executado para a data de hoje: <strong>{formatDateToBrazilian(getCurrentDate())}</strong>
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Configurações adicionais */}
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Configurações</h3>
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex items-center justify-between">
                            <span>Modo Headless:</span>
                            <span className="font-medium text-green-600">Ativado</span>
                          </div>
                        </div>
                      </div>

                      {/* Botão de iniciar */}
                      <button
                        onClick={handleStartScraping}
                        disabled={isScrapingDisabled()}
                        className="w-full bg-primary text-white py-3 px-4 rounded-lg font-medium hover:bg-primary/90 focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2 cursor-pointer"
                      >
                        {startScrapingMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Iniciando...</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            <span>Iniciar Scraping</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}