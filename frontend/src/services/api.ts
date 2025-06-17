import type {
    ApiResponse,
    AuthResponse,
    LoginForm,
    PaginatedResponse,
    Publication,
    PublicationStatus,
    SearchFilters,
    SignupForm,
    User
} from "@/types"

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface QueuedRequest {
    resolve: (value: any) => void
    reject: (error: any) => void
    url: string
    config: RequestInit
}

interface RetryConfig {
    maxRetries: number
    baseDelay: number
    maxDelay: number
    backoffFactor: number
}

class ApiService {
    private baseURL: string
    private isLoggingOut = false
    private requestQueue: QueuedRequest[] = []
    private isProcessingQueue = false
    private readonly rateLimitDelay = 200 // ms entre requisições
    private readonly retryConfig: RetryConfig = {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        backoffFactor: 2
    }

    constructor() {
        this.baseURL = API_BASE_URL
    }

    private getToken(): string | null {
        const token = localStorage.getItem('accessToken')
        console.log('[API Service] Getting token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null')
        return token
    }

    private async sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    private calculateRetryDelay(attempt: number): number {
        const delay = Math.min(
            this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffFactor, attempt),
            this.retryConfig.maxDelay
        )
        // Adiciona jitter para evitar thundering herd
        return delay + Math.random() * 1000
    }

    private async processQueue(): Promise<void> {
        if (this.isProcessingQueue || this.requestQueue.length === 0) {
            return
        }

        this.isProcessingQueue = true

        while (this.requestQueue.length > 0) {
            const request = this.requestQueue.shift()
            if (!request) break

            try {
                const response = await fetch(request.url, request.config)
                const data = await response.json()

                if (!response.ok) {
                    throw new Error(data.message || `HTTP error! status: ${response.status}`)
                }

                request.resolve(data)
            } catch (error) {
                request.reject(error)
            }

            // Rate limiting - delay entre requisições
            if (this.requestQueue.length > 0) {
                await this.sleep(this.rateLimitDelay)
            }
        }

        this.isProcessingQueue = false
    }

    private async queueRequest<T>(url: string, config: RequestInit): Promise<T> {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ resolve, reject, url, config })
            this.processQueue()
        })
    }

    private async requestWithRetry<T>(
        endpoint: string,
        options: RequestInit = {},
        attempt: number = 0
    ): Promise<T> {
        const url = `${this.baseURL}/api${endpoint}`
        const token = this.getToken()

        console.log(`[API Service] Making request to: ${url} (attempt ${attempt + 1})`)

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        }

        if (token) {
            headers.Authorization = `Bearer ${token}`
        }

        const config: RequestInit = {
            ...options,
            headers,
        }

        try {
            // Para requisições GET, usar queue para rate limiting
            // Para outras requisições críticas (POST/PUT), fazer diretamente
            const response = options.method === 'GET' || !options.method
                ? await this.queueRequest<T>(url, config)
                : await fetch(url, config).then(async (res) => {
                    if (!res.ok) {
                        const errorData = await res.json().catch(() => ({}))
                        throw new Error(errorData.message || `HTTP error! status: ${res.status}`)
                    }
                    return await res.json()
                })

            return response
        } catch (error: any) {
            const isRetryableError = this.isRetryableError(error)
            const shouldRetry = attempt < this.retryConfig.maxRetries && isRetryableError

            if (shouldRetry) {
                const delay = this.calculateRetryDelay(attempt)
                console.warn(`[API Service] Request failed, retrying in ${delay}ms:`, error.message)
                await this.sleep(delay)
                return this.requestWithRetry<T>(endpoint, options, attempt + 1)
            }

            // Handle 401 errors for auth redirect
            if (error.message.includes('401') && !endpoint.includes('/auth/login') && !this.isLoggingOut) {
                this.isLoggingOut = true
                await this.logout()
                window.location.href = '/login'
            }

            console.error(`[API Service] Request failed after ${attempt + 1} attempts:`, error)
            throw error
        }
    }

    private isRetryableError(error: any): boolean {
        const message = error.message?.toLowerCase() || ''

        // Erros que devem ser retentados
        return message.includes('429') || // Rate limit
            message.includes('502') || // Bad Gateway
            message.includes('503') || // Service Unavailable
            message.includes('504') || // Gateway Timeout
            message.includes('network') ||
            message.includes('timeout') ||
            message.includes('fetch')
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        return this.requestWithRetry<T>(endpoint, options)
    }

    // Métodos de autenticação
    async login(credentials: LoginForm): Promise<AuthResponse> {
        const response = await this.request<ApiResponse<AuthResponse>>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        })

        console.log('[API Service] Login response received')

        localStorage.setItem('accessToken', response.data.tokens.accessToken)
        localStorage.setItem('refreshToken', response.data.tokens.refreshToken)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return response.data
    }

    async signup(userData: SignupForm): Promise<AuthResponse> {
        const response = await this.request<ApiResponse<AuthResponse>>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        })

        localStorage.setItem('accessToken', response.data.tokens.accessToken)
        localStorage.setItem('refreshToken', response.data.tokens.refreshToken)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return response.data
    }

    async logout(): Promise<void> {
        try {
            const refreshToken = localStorage.getItem('refreshToken')
            if (refreshToken) {
                await this.request('/auth/logout', {
                    method: 'POST',
                    body: JSON.stringify({ refreshToken }),
                })
            }
        } catch (error) {
            console.error('Logout failed on server, but cleaning local data anyway.', error)
        } finally {
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
            localStorage.removeItem('user')
            this.isLoggingOut = false
        }
    }

    // Métodos de publicações com cache simples
    private publicationsCache = new Map<string, { data: any; timestamp: number }>()
    private readonly cacheTimeout = 30000 // 30 segundos

    private getCacheKey(page: number, limit: number, filters?: SearchFilters): string {
        return `publications_${page}_${limit}_${JSON.stringify(filters || {})}`
    }

    private getFromCache<T>(key: string): T | null {
        const cached = this.publicationsCache.get(key)
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data
        }
        return null
    }

    private setCache(key: string, data: any): void {
        this.publicationsCache.set(key, {
            data,
            timestamp: Date.now()
        })
    }

    async getPublications(
        page: number = 1,
        limit: number = 30,
        filters?: SearchFilters
    ): Promise<PaginatedResponse<Publication>> {
        const cacheKey = this.getCacheKey(page, limit, filters)
        const cached = this.getFromCache<PaginatedResponse<Publication>>(cacheKey)

        if (cached) {
            console.log('[API Service] Returning cached publications')
            return cached
        }

        const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
        })

        if (filters?.search && filters.search.trim()) {
            params.append('search', filters.search.trim())
        }
        if (filters?.startDate && filters.startDate.trim()) {
            params.append('startDate', filters.startDate.trim())
        }
        if (filters?.endDate && filters.endDate.trim()) {
            params.append('endDate', filters.endDate.trim())
        }
        if (filters?.status) {
            params.append('status', filters.status)
        }

        // Backend retorna estrutura diferente, vamos converter
        const response = await this.request<ApiResponse<{
            publications: Publication[]
            pagination: {
                current: number
                total: number
                count: number
                perPage: number
            }
        }>>(`/publications?${params.toString()}`)

        // Converter para o formato esperado pelo frontend
        const convertedResponse: PaginatedResponse<Publication> = {
            data: response.data.publications || [],
            total: response.data.pagination.count || 0,
            page: response.data.pagination.current || page,
            limit: response.data.pagination.perPage || limit,
            totalPages: response.data.pagination.total || 1,
        }

        this.setCache(cacheKey, convertedResponse)
        return convertedResponse
    }

    async getPublicationById(id: string): Promise<Publication> {
        const response = await this.request<ApiResponse<Publication>>(`/publications/${id}`)
        return response.data
    }

    async updatePublicationStatus(
        id: string,
        status: PublicationStatus
    ): Promise<Publication> {
        // Limpar cache relacionado quando atualizar status
        this.publicationsCache.clear()

        const response = await this.request<ApiResponse<Publication>>(
            `/publications/${id}/status`,
            {
                method: 'PUT',
                body: JSON.stringify({ status }),
            }
        )
        return response.data
    }

    // Método para limpar cache manualmente
    clearCache(): void {
        this.publicationsCache.clear()
    }

    // Método para verificar se o usuário está autenticado
    isAuthenticated(): boolean {
        return !!this.getToken()
    }

    // Método para obter o usuário atual
    getCurrentUser(): User | null {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
    }

    // Método para atualizar o token
    setToken(token: string): void {
        localStorage.setItem('accessToken', token)
    }
}

export const apiService = new ApiService()