// Versão melhorada da função formatCurrency para suportar JSONs diretos do scraper
// Substitua essa função em frontend/src/lib/utils.ts

export function formatCurrency(value: any): string {
    if (value === null || value === undefined) return 'N/A'

    try {
        let numericValue: number;

        // Se for um objeto superjson (vem da API), deserializar
        if (value && typeof value === 'object' && value.json !== undefined && value.meta !== undefined) {
            const deserializedValue = superjson.deserialize(value)
            numericValue = typeof deserializedValue === 'bigint' 
                ? Number(deserializedValue) 
                : Number(deserializedValue)
        }
        // Se for string (vem dos JSONs diretos do scraper), converter para número
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