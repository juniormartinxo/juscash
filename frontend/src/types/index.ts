import { ReactNode } from 'react'

// Tipos baseados no schema Prisma
export interface User {
    id: string
    name: string
    email: string
    created_at: string
    updated_at: string
}

export enum PublicationStatus {
    NOVA = 'NOVA',
    LIDA = 'LIDA',
    ENVIADA_PARA_ADV = 'ENVIADA_PARA_ADV',
    CONCLUIDA = 'CONCLUIDA'
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
    gross_value?: number // Valor em centavos
    net_value?: number // Valor em centavos
    interest_value?: number // Valor em centavos
    attorney_fees?: number // Valor em centavos
    content: string
    status: PublicationStatus
    created_at: string
    updated_at: string
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