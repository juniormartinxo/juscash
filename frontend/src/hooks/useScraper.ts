import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { ScraperStatus, ScrapingRequest } from '@/types'
import { useToast } from './use-toast'

// Keys para as queries do scraper
export const scraperKeys = {
    all: ['scraper'] as const,
    status: () => [...scraperKeys.all, 'status'] as const,
}

// Hook para buscar status do scraper
export function useScraperStatus() {
    return useQuery({
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