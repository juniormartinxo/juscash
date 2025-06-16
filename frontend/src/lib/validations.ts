import { z } from "zod"

// Schema para login
export const loginSchema = z.object({
    email: z
        .string()
        .min(1, "E-mail é obrigatório")
        .email("Formato de e-mail inválido"),
    password: z
        .string()
        .min(1, "Senha é obrigatória")
})

// Schema para cadastro
export const signupSchema = z.object({
    name: z
        .string()
        .min(1, "Nome é obrigatório")
        .min(2, "Nome deve ter pelo menos 2 caracteres"),
    email: z
        .string()
        .min(1, "E-mail é obrigatório")
        .email("Formato de e-mail inválido"),
    password: z
        .string()
        .min(8, "A senha deve ter no mínimo 8 caracteres")
        .regex(/[A-Z]/, "A senha deve conter pelo menos uma letra maiúscula")
        .regex(/[a-z]/, "A senha deve conter pelo menos uma letra minúscula")
        .regex(/[0-9]/, "A senha deve conter pelo menos um número")
        .regex(/[!@#$%^&*(),.?":{}|<>]/, "A senha deve conter pelo menos um caractere especial"),
    confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
    message: "A confirmação de senha não corresponde",
    path: ["confirmPassword"],
})

// Schema para filtros de busca
export const searchFiltersSchema = z.object({
    search: z.string().optional(),
    startDate: z.string().optional(),
    endDate: z.string().optional(),
    status: z.enum(["NOVA", "LIDA", "ENVIADA_PARA_ADV", "CONCLUIDA"]).optional()
})

// Tipos inferidos dos schemas
export type LoginFormData = z.infer<typeof loginSchema>
export type SignupFormData = z.infer<typeof signupSchema>
export type SearchFiltersData = z.infer<typeof searchFiltersSchema>