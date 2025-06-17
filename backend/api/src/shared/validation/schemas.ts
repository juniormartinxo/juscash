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
export const createPublicationSchema = z.object({
  processNumber: z.string().min(1, 'Número do processo é obrigatório'),
  publicationDate: z.string().datetime().transform(date => new Date(date)).optional(),
  availabilityDate: z.string().datetime().transform(date => new Date(date)),
  authors: z.array(z.string().min(1, 'Nome do autor não pode estar vazio')).min(1, 'Pelo menos um autor é obrigatório'),
  defendant: z.string().optional(),
  lawyers: z.array(z.object({
    name: z.string().min(1, 'Nome do advogado é obrigatório'),
    oab: z.string().min(1, 'OAB é obrigatória')
  })).optional(),
  grossValue: z.number().int().positive().optional(),
  netValue: z.number().int().positive().optional(),
  interestValue: z.number().int().positive().optional(),
  attorneyFees: z.number().int().positive().optional(),
  content: z.string().min(1, 'Conteúdo é obrigatório'),
  status: z.enum(['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA']).optional(),
  scrapingSource: z.string().optional(),
  caderno: z.string().optional(),
  instancia: z.string().optional(),
  local: z.string().optional(),
  parte: z.string().optional(),
  extractionMetadata: z.any().optional(),
})

export const updatePublicationStatusSchema = z.object({
  status: z.enum(['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA']),
})

export const getPublicationsQuerySchema = z.object({
  page: z.string().regex(/^\d+$/).transform(Number).optional(),
  limit: z.string().regex(/^\d+$/).transform(Number).optional(),
  status: z.enum(['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA']).optional(),
  startDate: z.string().min(1).regex(/^\d{4}-\d{2}-\d{2}$/).transform(date => new Date(date + 'T00:00:00.000Z')).optional(),
  endDate: z.string().min(1).regex(/^\d{4}-\d{2}-\d{2}$/).transform(date => new Date(date + 'T23:59:59.999Z')).optional(),
  search: z.string().optional(),
})
