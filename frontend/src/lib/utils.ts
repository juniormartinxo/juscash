import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

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
export function formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value / 100) // Valor em centavos
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