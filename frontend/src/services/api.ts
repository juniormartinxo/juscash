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
    private token: string | null = null

    constructor() {
        this.baseURL = API_BASE_URL
        this.token = localStorage.getItem('accessToken')
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}/api${endpoint}`

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        }

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`
        }

        const config: RequestInit = {
            ...options,
            headers,
        }

        try {
            const response = await fetch(url, config)

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
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

        this.token = response.data.accessToken
        localStorage.setItem('accessToken', response.data.accessToken)
        localStorage.setItem('refreshToken', response.data.refreshToken)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return response.data
    }

    async signup(userData: SignupForm): Promise<AuthResponse> {
        const response = await this.request<ApiResponse<AuthResponse>>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        })

        this.token = response.data.accessToken
        localStorage.setItem('accessToken', response.data.accessToken)
        localStorage.setItem('refreshToken', response.data.refreshToken)
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return response.data
    }

    async logout(): Promise<void> {
        try {
            await this.request('/auth/logout', {
                method: 'POST',
            })
        } catch (error) {
            console.error('Logout failed, but cleaning local data anyway.', error)
        } finally {
            this.token = null
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
            localStorage.removeItem('user')
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

        if (filters?.search) {
            params.append('search', filters.search)
        }
        if (filters?.startDate) {
            params.append('startDate', filters.startDate)
        }
        if (filters?.endDate) {
            params.append('endDate', filters.endDate)
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
        return !!this.token
    }

    // Método para obter o usuário atual
    getCurrentUser(): User | null {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
    }

    // Método para atualizar o token
    setToken(token: string): void {
        this.token = token
        localStorage.setItem('accessToken', token)
    }
}

export const apiService = new ApiService()