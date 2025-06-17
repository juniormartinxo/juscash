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

class ApiService {
    private baseURL: string
    private isLoggingOut = false

    constructor() {
        this.baseURL = API_BASE_URL
    }

    private getToken(): string | null {
        const token = localStorage.getItem('accessToken')
        console.log('[API Service] Getting token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null')
        return token
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}/api${endpoint}`
        const token = this.getToken()

        console.log('[API Service] Making request to:', url)
        console.log('[API Service] Token available:', !!token)

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        }

        if (token) {
            headers.Authorization = `Bearer ${token}`
            console.log('[API Service] Authorization header added')
        } else {
            console.log('[API Service] No token available - Authorization header NOT added')
        }

        console.log('[API Service] Final headers:', headers)

        const config: RequestInit = {
            ...options,
            headers,
        }

        try {
            console.log('[API Service] Sending request with config:', config)
            const response = await fetch(url, config)

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))

                if (response.status === 401 && !endpoint.includes('/auth/login') && !this.isLoggingOut) {
                    this.isLoggingOut = true
                    await this.logout()
                    window.location.href = '/login'
                }

                throw new Error(errorData.message || `HTTP error! status: ${response.status}`)
            }

            return await response.json()
        } catch (error) {
            console.error('API request failed:', error)
            throw error
        }
    }

    // Métodos de autenticação
    async login(credentials: LoginForm): Promise<AuthResponse> {
        const response = await this.request<ApiResponse<AuthResponse>>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        })

        console.log('[API Service] Login response:', response)
        console.log('[API Service] Access token received:', response.data.tokens?.accessToken ? `${response.data.tokens.accessToken.substring(0, 20)}...` : 'null')

        localStorage.setItem('accessToken', response.data.tokens.accessToken)
        localStorage.setItem('refreshToken', response.data.tokens.refreshToken)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        console.log('[API Service] Token saved to localStorage')
        console.log('[API Service] Verifying saved token:', localStorage.getItem('accessToken') ? 'Token exists' : 'Token NOT saved')

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

    // Métodos de publicações
    async getPublications(
        page: number = 1,
        limit: number = 30,
        filters?: SearchFilters
    ): Promise<PaginatedResponse<Publication>> {
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

        const response = await this.request<ApiResponse<PaginatedResponse<Publication>>>(
            `/publications?${params.toString()}`
        )

        return response.data
    }

    async getPublicationById(id: string): Promise<Publication> {
        const response = await this.request<ApiResponse<Publication>>(`/publications/${id}`)
        return response.data
    }

    async updatePublicationStatus(
        id: string,
        status: PublicationStatus
    ): Promise<Publication> {
        const response = await this.request<ApiResponse<Publication>>(
            `/publications/${id}/status`,
            {
                method: 'PUT',
                body: JSON.stringify({ status }),
            }
        )
        return response.data
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