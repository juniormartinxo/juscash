import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/hooks/use-toast'
import { loginSchema, type LoginFormData } from '@/lib/validations'
import Logo from '@/components/Logo'

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    try {
      await login(data)
      toast({
        title: "Login realizado com sucesso",
        description: "Bem-vindo ao JusCash!",
      })
      navigate('/dashboard')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'

      if (errorMessage.includes('credential') || errorMessage.includes('senha')) {
        toast({
          title: "Credenciais inválidas",
          description: "Verifique o e-mail e a senha e tente novamente.",
          variant: "destructive",
        })
      } else {
        toast({
          title: "Erro no servidor",
          description: "Ocorreu um problema. Tente novamente mais tarde.",
          variant: "destructive",
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center justify-center shadow-xl min-h-screen w-lg p-16 bg-white">
        <div className="w-full max-w-lg space-y-8">
          {/* Logo */}
          <div className="text-center">
            <div className="flex justify-center items-center mb-10">
              <Logo size={250} />
            </div>
          </div>

          {/* Formulário */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Campo E-mail */}
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-bold text-secondary">
                E-mail:
              </label>
              <Input
                id="email"
                type="email"
                {...register('email')}
                error={!!errors.email}
                className="w-full rounded-sm border h-8 border-border-input px-3 focus:border-primary focus:ring-primary"
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Campo Senha */}
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-bold text-secondary">
                Senha:
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...register('password')}
                  error={!!errors.password}
                  className="w-full h-8 rounded-md border border-border-input px-3 pr-10 focus:border-primary focus:ring-primary"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>

            <div className="flex flex-col items-center justify-center">
              {/* Botão Login */}
              <Button
                type="submit"
                className="px-9 h-8 bg-primary hover:bg-primary/90 text-white font-bold rounded-md mt-6 cursor-pointer"
                loading={isLoading}
                disabled={isLoading}
              >
                Login
              </Button>
            </div>
            {/* Link para cadastro */}
            <div className="text-center mt-6">
              <p className="text-sm text-gray-600">
                <Link
                  to="/signup"
                  className="text-secondary hover:underline font-bold underline"
                >
                  Não possui uma conta? Cadastra-se
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}