import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
import { signupSchema, type SignupFormData } from '@/lib/validations'
import Logo from '@/components/Logo'

export function SignupPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { signup } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  })

  const password = watch('password')

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true)
    try {
      await signup(data)
      toast({
        title: "Conta criada com sucesso",
        description: "Bem-vindo ao JusCash!",
      })
      navigate('/dashboard')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'

      if (errorMessage.includes('email') || errorMessage.includes('já registrado')) {
        toast({
          title: "E-mail já cadastrado",
          description: "Este e-mail já está em uso. Tente fazer login.",
          variant: "destructive",
        })
      } else {
        toast({
          title: "Erro no cadastro",
          description: "Ocorreu um problema. Tente novamente mais tarde.",
          variant: "destructive",
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  const getPasswordStrength = (password: string) => {
    const requirements = [
      password.length >= 8,
      /[A-Z]/.test(password),
      /[a-z]/.test(password),
      /[0-9]/.test(password),
      /[!@#$%^&*(),.?":{}|<>]/.test(password),
    ]
    return requirements.filter(Boolean).length
  }

  const passwordStrength = password ? getPasswordStrength(password) : 0

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center justify-center shadow-xl min-h-screen w-lg p-16 bg-white">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="text-center">
            <div className="flex justify-center items-center mb-10">
              <Logo size={250} />
            </div>
          </div>

          {/* Formulário */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Campo Nome */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-secondary">
                Seu nome completo: <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                type="text"
                {...register('name')}
                error={!!errors.name}
                className="w-full h-8 rounded-sm border border-border-input px-3 focus:border-primary focus:ring-primary"
                autoComplete="name"
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>

            {/* Campo E-mail */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-secondary">
                E-mail: <span className="text-red-500">*</span>
              </Label>
              <Input
                id="email"
                type="email"
                {...register('email')}
                error={!!errors.email}
                className="w-full h-8 rounded-sm border border-border-input px-3 focus:border-primary focus:ring-primary"
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Campo Senha */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-secondary">
                Senha: <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...register('password')}
                  error={!!errors.password}
                  className="w-full h-8 rounded-sm border border-border-input px-3 pr-10 focus:border-primary focus:ring-primary"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>

              {/* Indicador de força da senha */}
              {password && (
                <div className="space-y-1">
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className={`h-1 flex-1 rounded ${passwordStrength >= level
                          ? 'bg-primary-500'
                          : 'bg-gray-200'
                          }`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-gray-500">
                    Força da senha: {
                      passwordStrength < 3 ? 'Fraca' :
                        passwordStrength < 5 ? 'Média' : 'Forte'
                    }
                  </p>
                </div>
              )}

              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>

            {/* Campo Confirmar Senha */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-secondary">
                Confirme sua senha: <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  {...register('confirmPassword')}
                  error={!!errors.confirmPassword}
                  className="w-full h-8 rounded-sm border border-border-input px-3 pr-10 focus:border-primary focus:ring-primary"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 flex items-center pr-3"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
              )}
            </div>
            {/* Link para login */}
            <div className="text-right">
              <p className="text-sm text-gray-500">
                <Link
                  to="/login"
                  className="text-secondary hover:underline font-bold"
                >
                  Já possui uma conta? Fazer o login
                </Link>
              </p>
            </div>

            <div className="flex flex-col items-center justify-center">
              {/* Botão Criar Conta */}
              <Button
                type="submit"
                className="px-6 h-8 bg-primary hover:bg-primary/90 text-white font-bold rounded-md mt-6 cursor-pointer"
                loading={isLoading}
                disabled={isLoading}
              >
                Criar conta
              </Button>
            </div>

          </form>
        </div>
      </div>
    </div>
  )
}