import { ReactNode } from 'react'

// Tipos baseados no schema Prisma
export interface User {
    id: string
    name: string
    email: string
    createdAt: string
    updatedAt: string
}

export enum PublicationStatus {
    NOVA = 'NOVA',
    LIDA = 'LIDA',
    ENVIADA_PARA_ADV = 'ENVIADA_PARA_ADV',
    CONCLUIDA = 'CONCLUIDA'
}

export const PublicationStatusName = {
    [PublicationStatus.NOVA]: 'Nova',
    [PublicationStatus.LIDA]: 'Lida',
    [PublicationStatus.ENVIADA_PARA_ADV]: 'Enviada para Advogado',
    [PublicationStatus.CONCLUIDA]: 'Concluída'
}

export interface Lawyer {
    name: string
    oab: string
}

export interface Publication {
    id: string
    process_number: string
    publication_date?: string
    availability_date: string
    authors: string[]
    defendant: string
    lawyers?: Lawyer[]
    gross_value?: any // Valor serializado pelo superjson (BigInt)
    net_value?: any // Valor serializado pelo superjson (BigInt)
    interest_value?: any // Valor serializado pelo superjson (BigInt) 
    attorney_fees?: any // Valor serializado pelo superjson (BigInt)
    content: string
    status: PublicationStatus
    createdAt: string
    updatedAt: string
}

// Tipos para formulários
export interface LoginForm {
    email: string
    password: string
}

export interface SignupForm {
    name: string
    email: string
    password: string
    confirmPassword: string
}

// Tipos para filtros e busca
export interface SearchFilters {
    search?: string
    startDate?: string
    endDate?: string
    status?: PublicationStatus
}

// Tipos para API responses
export interface ApiResponse<T> {
    data: T
    message?: string
    success: boolean
}

export interface PaginatedResponse<T> {
    data: T[]
    total: number
    page: number
    limit: number
    totalPages: number
}

export interface AuthResponse {
    user: User
    tokens: {
        accessToken: string
        refreshToken: string
    }
}

// Tipos para o Kanban
export interface KanbanColumn {
    id: PublicationStatus
    title: ReactNode
    publications: Publication[]
    count: number
}

// Tipos para drag and drop
export interface DragResult {
    draggableId: string
    type: string
    source: {
        droppableId: string
        index: number
    }
    destination?: {
        droppableId: string
        index: number
    }
}

// Estados de loading
export interface LoadingStates {
    login: boolean
    signup: boolean
    publications: boolean
    updateStatus: boolean
}

// Tipos para erros
export interface ApiError {
    message: string
    field?: string
    code?: string
}

export interface FormErrors {
    [key: string]: string | undefined
}

export interface ScraperStatus {
    status: {
        monitor: boolean
        scraping: boolean
    }
    pids: Record<string, string[]>
    script_directory: string
    python_executable: string
}

export interface ScrapingRequest {
    start_date: string
    end_date: string
    headless?: boolean
}