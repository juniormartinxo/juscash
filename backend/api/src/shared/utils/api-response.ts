export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  details?: any
}

/**
 * Converte BigInt para string recursivamente em um objeto
 * Necessário para serialização JSON, pois BigInt não é suportado nativamente
 */
function convertBigIntToString(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (typeof obj === 'bigint') {
    return obj.toString()
  }

  if (Array.isArray(obj)) {
    return obj.map(convertBigIntToString)
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    const converted: any = {}
    for (const [key, value] of Object.entries(obj)) {
      converted[key] = convertBigIntToString(value)
    }
    return converted
  }

  return obj
}

export class ApiResponseBuilder {
  static success<T>(data: T): ApiResponse<T> {
    return {
      success: true,
      data: convertBigIntToString(data),
    }
  }

  static error(message: string, details?: any): ApiResponse {
    return {
      success: false,
      error: message,
      ...(details && { details: convertBigIntToString(details) }),
    }
  }

  static validationError(errors: Array<{ field: string; message: string }>): ApiResponse {
    return {
      success: false,
      error: 'Validation failed',
      details: convertBigIntToString(errors),
    }
  }
}
