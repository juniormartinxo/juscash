import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { ScraperStatus, ScrapingRequest } from '@/types'
import { useToast } from './use-toast'
import { publicationKeys } from './usePublications'
import { useEffect, useRef } from 'react'

// Keys para as queries do scraper
export const scraperKeys = {
    all: ['scraper'] as const,
    status: () => [...scraperKeys.all, 'status'] as const,
}

// Hook para buscar status do scraper
export function useScraperStatus() {
    const queryClient = useQueryClient()
    const wasScrapingRef = useRef<boolean>(false)

    const query = useQuery({
        queryKey: scraperKeys.status(),
        queryFn: () => apiService.getScraperStatus(),
        staleTime: 1000 * 30, // 30 segundos
        refetchInterval: 5000, // Polling a cada 5 segundos
        refetchIntervalInBackground: true,
        refetchOnWindowFocus: true,
        refetchOnMount: true,
        retry: (failureCount, error: any) => {
            // Não fazer retry para erros de autenticação
            if (error?.message?.includes('401') || error?.message?.includes('403')) {
                return false
            }
            // Fazer retry até 3 vezes para outros erros
            return failureCount < 3
        },
    })

    // Detectar quando o scraping termina e invalidar queries das publicações
    useEffect(() => {
        const currentlyScrapingStatus = query.data?.status?.scraping
        const wasScrapingStatus = wasScrapingRef.current

        // Se estava rodando e agora parou, invalidar queries das publicações
        if (wasScrapingStatus && !currentlyScrapingStatus) {
            console.log('🔄 [useScraperStatus] Scraping finished, invalidating publication queries')

            // Invalidar todas as queries de publicações
            queryClient.invalidateQueries({ queryKey: publicationKeys.all })

            // Forçar refetch dos contadores
            queryClient.refetchQueries({ queryKey: publicationKeys.counts() })

            // Limpar cache do API service
            apiService.clearCache()
        }

        // Atualizar ref para próxima verificação
        wasScrapingRef.current = currentlyScrapingStatus || false
    }, [query.data?.status?.scraping, queryClient])

    return query
}

// Hook para iniciar scraping
export function useStartScraping() {
    const queryClient = useQueryClient()
    const { toast } = useToast()

    return useMutation({
        mutationFn: (request: ScrapingRequest) => {
            console.log('🚀 [useStartScraping] Starting scraping:', request)
            return apiService.startScraping(request)
        },

        onSuccess: (data, variables) => {
            console.log('✅ [useStartScraping] Scraping started successfully')

            // Invalidar e refetch do status
            queryClient.invalidateQueries({ queryKey: scraperKeys.status() })

            // Também invalidar queries das publicações para preparar para novos dados
            queryClient.invalidateQueries({ queryKey: publicationKeys.all })

            const formatDate = (dateStr: string) => {
                const [year, month, day] = dateStr.split('-')
                return `${day}/${month}/${year}`
            }

            toast({
                title: "Scraping iniciado com sucesso!",
                description: `Período: ${formatDate(variables.start_date)} até ${formatDate(variables.end_date)}`,
            })
        },

        onError: (error: any) => {
            console.error('❌ [useStartScraping] Error:', error)
            toast({
                title: "Erro ao iniciar scraping",
                description: error instanceof Error ? error.message : "Erro desconhecido",
                variant: "destructive",
            })
        },
    })
}

// Hook para parar scraping
export function useStopScraping() {
    const queryClient = useQueryClient()
    const { toast } = useToast()

    return useMutation({
        mutationFn: () => {
            console.log('🛑 [useStopScraping] Stopping scraping')
            return apiService.stopScraping()
        },

        onSuccess: (data) => {
            console.log('✅ [useStopScraping] Scraping stopped successfully')

            // Invalidar e refetch do status
            queryClient.invalidateQueries({ queryKey: scraperKeys.status() })

            if (data.status === 'success') {
                toast({
                    title: "Scraping parado com sucesso!",
                    description: data.message,
                })
            } else if (data.status === 'partial') {
                toast({
                    title: "Parada parcial",
                    description: data.message,
                    variant: "destructive",
                })
            } else {
                toast({
                    title: "Erro na parada forçada",
                    description: data.message,
                    variant: "destructive",
                })
            }
        },

        onError: (error: any) => {
            console.error('❌ [useStopScraping] Error:', error)
            toast({
                title: "Erro ao forçar parada",
                description: error instanceof Error ? error.message : "Erro desconhecido",
                variant: "destructive",
            })
        },
    })
}

// Hook para iniciar scraping do dia atual
export function useStartScrapingToday() {
    const queryClient = useQueryClient()
    const { toast } = useToast()

    return useMutation({
        mutationFn: (headless: boolean = true) => {
            console.log('📅 [useStartScrapingToday] Starting today scraping')
            return apiService.startScrapingToday(headless)
        },

        onSuccess: () => {
            console.log('✅ [useStartScrapingToday] Today scraping started successfully')

            // Invalidar e refetch do status
            queryClient.invalidateQueries({ queryKey: scraperKeys.status() })

            const today = new Date().toLocaleDateString('pt-BR')
            toast({
                title: "Scraping iniciado com sucesso!",
                description: `Executando para hoje: ${today}`,
            })
        },

        onError: (error: any) => {
            console.error('❌ [useStartScrapingToday] Error:', error)
            toast({
                title: "Erro ao iniciar scraping de hoje",
                description: error instanceof Error ? error.message : "Erro desconhecido",
                variant: "destructive",
            })
        },
    })
}

// Hook para refresh manual do status
export function useRefreshScraperStatus() {
    const queryClient = useQueryClient()

    return () => {
        console.log('🔄 [useRefreshScraperStatus] Manual refresh triggered')
        queryClient.invalidateQueries({ queryKey: scraperKeys.status() })
        queryClient.refetchQueries({ queryKey: scraperKeys.status() })
    }
}

// Hook para detectar quando há novas publicações (usado pelo KanbanBoard)
export function useScrapingCompletionDetector() {
    const queryClient = useQueryClient()
    const { toast } = useToast()
    const wasScrapingRef = useRef<boolean>(false)

    const { data: scraperStatus } = useQuery({
        queryKey: scraperKeys.status(),
        queryFn: () => apiService.getScraperStatus(),
        staleTime: 1000 * 30,
        refetchInterval: 5000,
        refetchIntervalInBackground: true,
    })

    // Detectar quando o scraping termina
    useEffect(() => {
        const currentlyScrapingStatus = scraperStatus?.status?.scraping
        const wasScrapingStatus = wasScrapingRef.current

        // Se estava rodando e agora parou, mostrar notificação
        if (wasScrapingStatus && !currentlyScrapingStatus) {
            console.log('🎉 [useScrapingCompletionDetector] Scraping completed!')

            toast({
                title: "🎉 Scraping concluído!",
                description: "Novas publicações podem estar disponíveis. Os dados serão atualizados automaticamente.",
                duration: 5000,
            })

            // Invalidar todas as queries de publicações
            queryClient.invalidateQueries({ queryKey: publicationKeys.all })
            queryClient.refetchQueries({ queryKey: publicationKeys.counts() })
            apiService.clearCache()
        }

        wasScrapingRef.current = currentlyScrapingStatus || false
    }, [scraperStatus?.status?.scraping, queryClient, toast])

    return {
        isScrapingRunning: scraperStatus?.status?.scraping || false,
        scraperStatus
    }
} 