import { z } from 'zod'

// Auth schemas
export const registerSchema = z.object({
  name: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres'),
  email: z.string().email('Email inválido'),
  password: z.string()
    .min(8, 'Senha deve ter pelo menos 8 caracteres')
    .regex(/[A-Z]/, 'Senha deve conter pelo menos uma letra maiúscula')
    .regex(/[a-z]/, 'Senha deve conter pelo menos uma letra minúscula')
    .regex(/\d/, 'Senha deve conter pelo menos um número')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Senha deve conter pelo menos um caractere especial'),
})

export const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'Senha é obrigatória'),
})

// Publication schemas
export const updatePublicationStatusSchema = z.object({
  status: z.enum(['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA']),
})

export const getPublicationsQuerySchema = z.object({
  page: z.string().regex(/^\d+$/).transform(Number).optional(),
  limit: z.string().regex(/^\d+$/).transform(Number).optional(),
  status: z.enum(['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA']).optional(),
  startDate: z.string().datetime().transform(date => new Date(date)).optional(),
  endDate: z.string().datetime().transform(date => new Date(date)).optional(),
  search: z.string().optional(),
})