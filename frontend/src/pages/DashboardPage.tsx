import { useState, useEffect } from 'react'
import { Scale, X, Calendar, Play, Loader2, AlertCircle, CheckCircle, RefreshCw, StopCircle } from 'lucide-react'
import { TbClockCog } from 'react-icons/tb'
import { Navbar } from '@/components/Navbar'
import { SearchFiltersComponent } from '@/components/SearchFilters'
import { KanbanBoard } from '@/components/KanbanBoard'
import { useToast } from '@/hooks/use-toast'
import type { SearchFilters } from '@/types'

interface ScraperStatus {
  status: {
    monitor: boolean
    scraping: boolean
  }
  pids: Record<string, string[]>
  script_directory: string
  python_executable: string
}

export function DashboardPage() {
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    startDate: '',
    endDate: '',
  })
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  // Estados do formulário de scraping
  const [isScrapingLoading, setIsScrapingLoading] = useState(false)
  const [useCurrentDate, setUseCurrentDate] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Estados do status do scraper
  const [scraperStatus, setScraperStatus] = useState<ScraperStatus | null>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(false)
  const [statusPollingInterval, setStatusPollingInterval] = useState<NodeJS.Timeout | null>(null)

  // Estados para parada forçada
  const [isForceStoppingLoading, setIsForceStoppingLoading] = useState(false)

  const { toast } = useToast()

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
  }

  const getCurrentDate = () => {
    const now = new Date()
    return now.toISOString().split('T')[0]
  }

  // Função para verificar o status do scraper
  const checkScraperStatus = async (showToast = false) => {
    try {
      setIsLoadingStatus(true)
      const response = await fetch('http://localhost:5000/status')

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`)
      }

      const status: ScraperStatus = await response.json()
      setScraperStatus(status)

      if (showToast) {
        toast({
          title: "Status atualizado",
          description: status.status.scraping
            ? "Scraping está em execução"
            : "Scraping não está rodando",
        })
      }

      return status
    } catch (error) {
      console.error('Erro ao verificar status:', error)
      if (showToast) {
        toast({
          title: "Erro ao verificar status",
          description: error instanceof Error ? error.message : "Erro desconhecido",
          variant: "destructive",
        })
      }
      return null
    } finally {
      setIsLoadingStatus(false)
    }
  }

  // Verificar status quando o drawer abre
  useEffect(() => {
    if (isDrawerOpen) {
      checkScraperStatus()
    }
  }, [isDrawerOpen])

  // Polling do status quando scraping está rodando
  useEffect(() => {
    if (scraperStatus?.status.scraping) {
      const interval = setInterval(() => {
        checkScraperStatus()
      }, 5000) // Verifica a cada 5 segundos

      setStatusPollingInterval(interval)

      return () => {
        clearInterval(interval)
        setStatusPollingInterval(null)
      }
    } else if (statusPollingInterval) {
      clearInterval(statusPollingInterval)
      setStatusPollingInterval(null)
    }
  }, [scraperStatus?.status.scraping])

  // Limpar polling quando componente desmonta
  useEffect(() => {
    return () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
      }
    }
  }, [])

  const handleStartScraping = async () => {
    try {
      // Verificar status primeiro
      const currentStatus = await checkScraperStatus()

      if (currentStatus?.status.scraping) {
        toast({
          title: "Scraping já em execução",
          description: "Aguarde o scraping atual terminar antes de iniciar outro.",
          variant: "destructive",
        })
        return
      }

      setIsScrapingLoading(true)

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

      const response = await fetch('http://localhost:5000/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: finalStartDate,
          end_date: finalEndDate,
          headless: true
        }),
      })

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`)
      }

      const result = await response.json()

      toast({
        title: "Scraping iniciado com sucesso!",
        description: `Período: ${finalStartDate} até ${finalEndDate}`,
      })

      // Limpar o formulário
      setStartDate('')
      setEndDate('')
      setUseCurrentDate(false)

      // Verificar status novamente para atualizar a UI
      setTimeout(() => checkScraperStatus(), 2000)

    } catch (error) {
      console.error('Erro ao iniciar scraping:', error)
      toast({
        title: "Erro ao iniciar scraping",
        description: error instanceof Error ? error.message : "Erro desconhecido",
        variant: "destructive",
      })
    } finally {
      setIsScrapingLoading(false)
    }
  }

  const handleForceStopScraping = async () => {
    try {
      setIsForceStoppingLoading(true)

      const response = await fetch('http://localhost:5000/force-stop-scraping', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`)
      }

      const result = await response.json()

      if (result.status === 'success') {
        toast({
          title: "Scraping parado com sucesso!",
          description: result.message,
        })
      } else if (result.status === 'partial') {
        toast({
          title: "Parada parcial",
          description: result.message,
          variant: "destructive",
        })
      } else {
        toast({
          title: "Erro na parada forçada",
          description: result.message,
          variant: "destructive",
        })
      }

      // Verificar status novamente para atualizar a UI
      setTimeout(() => checkScraperStatus(), 2000)

    } catch (error) {
      console.error('Erro ao forçar parada do scraping:', error)
      toast({
        title: "Erro ao forçar parada",
        description: error instanceof Error ? error.message : "Erro desconhecido",
        variant: "destructive",
      })
    } finally {
      setIsForceStoppingLoading(false)
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
            onClick={() => checkScraperStatus(true)}
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
      isScrapingLoading ||
      isForceStoppingLoading ||
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
              onClick={() => setIsDrawerOpen(true)}
              className="bg-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-l-lg p-4 border border-r-0 border-gray-200 hover:translate-x-1 cursor-pointer relative"
              title="Configurações"
            >
              <TbClockCog size={24} className="text-primary" />
              {/* Indicador de status quando scraping está rodando */}
              {scraperStatus?.status.scraping && (
                <div className="absolute -top-1 -left-1 w-3 h-3 bg-orange-500 rounded-full animate-pulse"></div>
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
            className="absolute inset-0 bg-black/45 transition-opacity"
            onClick={() => setIsDrawerOpen(false)}
          />

          {/* Drawer content */}
          <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl transform transition-transform">
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <TbClockCog size={20} className="text-primary" />
                  <h2 className="text-lg font-semibold text-gray-900">
                    Iniciar Scraping
                  </h2>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
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
                          <Loader2 className="w-4 h-4 text-orange-600 animate-spin" />
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
                        disabled={isForceStoppingLoading}
                        className="w-full bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                      >
                        {isForceStoppingLoading ? (
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
                          disabled={isForceStoppingLoading}
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
                                disabled={isForceStoppingLoading}
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
                                disabled={isForceStoppingLoading}
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
                              Scraping será executado para a data de hoje: <strong>{getCurrentDate()}</strong>
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
                        {isScrapingLoading ? (
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