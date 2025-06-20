import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import superjson from "superjson"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// Utilitário para debounce
export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout
    return (...args: Parameters<T>) => {
        clearTimeout(timeout)
        timeout = setTimeout(() => func(...args), wait)
    }
}

// Formatação de valores monetários
export function formatCurrency(value: any): string {
    if (value === null || value === undefined) return 'N/A'

    try {
        let numericValue: number

        // Se for um objeto superjson (vem da API), deserializar
        if (value && typeof value === 'object' && value.json !== undefined && value.meta !== undefined) {
            const deserializedValue = superjson.deserialize(value)
            numericValue = typeof deserializedValue === 'bigint'
                ? Number(deserializedValue)
                : Number(deserializedValue)
        }
        // Se for string (vem dos JSONs diretos do scraper ou da API como string), converter para número
        else if (typeof value === 'string') {
            numericValue = parseInt(value, 10)
        }
        // Se for número direto
        else if (typeof value === 'number') {
            numericValue = value
        }
        // Se for BigInt direto
        else if (typeof value === 'bigint') {
            numericValue = Number(value)
        }
        else {
            console.warn('Formato de valor monetário não reconhecido:', typeof value, value)
            return 'N/A'
        }

        // Verificar se é um número válido
        if (!Number.isFinite(numericValue) || isNaN(numericValue)) {
            console.warn('Valor monetário inválido:', numericValue)
            return 'N/A'
        }

        // Formatar como moeda brasileira (valor já está em centavos)
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(numericValue / 100)

    } catch (error) {
        console.warn('Erro ao formatar currency:', error, 'Value:', value)
        return 'N/A'
    }
}

// Formatação de datas
export function formatDate(date: string | Date): string {
    const d = new Date(date)
    return d.toLocaleDateString('pt-BR')
}

// Calcular tempo relativo desde a criação
export function getTimeAgo(date: string | Date): string {
    const now = new Date()
    const createdDate = new Date(date)
    const diffInMs = now.getTime() - createdDate.getTime()

    const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInDays > 0) {
        return diffInDays === 1 ? '1 dia' : `${diffInDays} dias`
    } else if (diffInHours > 0) {
        return diffInHours === 1 ? '1h' : `${diffInHours}h`
    } else if (diffInMinutes > 0) {
        return diffInMinutes === 1 ? '1 min' : `${diffInMinutes} min`
    } else {
        return 'agora'
    }
}

// Validação de email
export function isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
}

// Validação de senha
export function validatePassword(password: string): {
    isValid: boolean
    errors: string[]
} {
    const errors: string[] = []

    if (password.length < 8) {
        errors.push('Deve ter pelo menos 8 caracteres')
    }

    if (!/[A-Z]/.test(password)) {
        errors.push('Deve conter pelo menos uma letra maiúscula')
    }

    if (!/[a-z]/.test(password)) {
        errors.push('Deve conter pelo menos uma letra minúscula')
    }

    if (!/[0-9]/.test(password)) {
        errors.push('Deve conter pelo menos um número')
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        errors.push('Deve conter pelo menos um caractere especial')
    }

    return {
        isValid: errors.length === 0,
        errors
    }
}