export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  details?: any
}

export class ApiResponseBuilder {
  static success<T>(data: T): ApiResponse<T> {
    return {
      success: true,
      data,
    }
  }

  static error(message: string, details?: any): ApiResponse {
    return {
      success: false,
      error: message,
      ...(details && { details }),
    }
  }

  static validationError(errors: Array<{ field: string; message: string }>): ApiResponse {
    return {
      success: false,
      error: 'Validation failed',
      details: errors,
    }
  }
}