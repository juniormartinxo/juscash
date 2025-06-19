import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService } from '@/services/api'
import { PublicationStatus, PublicationStatusName, SearchFilters } from '@/types'
import { useToast } from './use-toast'

// Keys para as queries
export const publicationKeys = {
    all: ['publications'] as const,
    lists: () => [...publicationKeys.all, 'list'] as const,
    list: (filters: SearchFilters & { status?: PublicationStatus }, page: number, limit: number) =>
        [...publicationKeys.lists(), { filters, page, limit }] as const,
    counts: () => [...publicationKeys.all, 'counts'] as const,
    count: (status: PublicationStatus, filters: SearchFilters) =>
        [...publicationKeys.counts(), { status, filters }] as const,
}

// Hook para buscar publicações por status
export function usePublications(
    status: PublicationStatus,
    page: number = 1,
    limit: number = 30,
    filters: SearchFilters = {}
) {
    return useQuery({
        queryKey: publicationKeys.list({ ...filters, status }, page, limit),
        queryFn: () => apiService.getPublications(page, limit, { ...filters, status }),
        staleTime: 1000 * 60 * 2, // 2 minutos
        refetchInterval: 30000, // Voltando para 30 segundos para evitar sobrecarga
        refetchIntervalInBackground: true, // Continuar fazendo polling mesmo em background
    })
}

// Hook para buscar contagem de publicações por status
export function usePublicationCount(status: PublicationStatus, filters: SearchFilters = {}) {
    return useQuery({
        queryKey: publicationKeys.count(status, filters),
        queryFn: async () => {
            // Removendo logs excessivos que causam poluição
            const response = await apiService.getPublications(1, 1, { ...filters, status })
            return response.total
        },
        staleTime: 0, // Sempre buscar dados frescos
        gcTime: 1000 * 60 * 5, // 5 minutos para garbage collection
        refetchOnWindowFocus: true,
        refetchOnMount: true,
        refetchInterval: 30000, // Reduzindo para 30 segundos para evitar sobrecarga
        refetchIntervalInBackground: true, // Continuar fazendo polling mesmo em background
    })
}

// Hook para atualizar status de publicação
export function useUpdatePublicationStatus() {
    const queryClient = useQueryClient()
    const { toast } = useToast()

    return useMutation({
        mutationFn: ({ publicationId, newStatus }: { publicationId: string, newStatus: PublicationStatus }) => {
            console.log(`🔄 [useUpdatePublicationStatus] Updating ${publicationId} to ${newStatus}`)
            return apiService.updatePublicationStatus(publicationId, newStatus)
        },

        onSuccess: async (_, { newStatus }) => {
            console.log(`✅ [useUpdatePublicationStatus] Success! Status updated to ${newStatus}`)

            // Invalidar TODAS as queries de publicações e contadores
            await queryClient.invalidateQueries({ queryKey: publicationKeys.all })

            // Forçar refetch imediato dos contadores
            await queryClient.refetchQueries({ queryKey: publicationKeys.counts() })

            // Limpar cache do API service também
            apiService.clearCache()

            console.log(`🔄 [useUpdatePublicationStatus] All queries invalidated and refetched`)

            const statusName = PublicationStatusName[newStatus]

            toast({
                title: "Status atualizado",
                description: `Publicação movida para "${statusName}"`,
                duration: 3000,
            })
        },

        onError: async (error) => {
            console.error('❌ [useUpdatePublicationStatus] Error:', error)
            toast({
                title: "Erro ao atualizar status",
                description: "Não foi possível atualizar o status da publicação.",
                variant: "destructive",
            })

            // Invalidar queries para garantir consistência
            await queryClient.invalidateQueries({ queryKey: publicationKeys.all })
            await queryClient.refetchQueries({ queryKey: publicationKeys.counts() })
        },
    })
}

// Hook para invalidar todas as queries de publicação (útil para refresh manual)
export function useRefreshPublications() {
    const queryClient = useQueryClient()

    return async () => {
        console.log('🔄 [useRefreshPublications] Manual refresh triggered')
        await queryClient.invalidateQueries({ queryKey: publicationKeys.all })
        await queryClient.refetchQueries({ queryKey: publicationKeys.counts() })
        apiService.clearCache()
    }
} 