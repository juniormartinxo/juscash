import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiService } from '@/services/api'
import type { User, LoginForm, SignupForm } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (credentials: LoginForm) => Promise<void>
  signup: (userData: SignupForm) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar se o usuário está logado ao inicializar
    const initAuth = () => {
      try {
        const token = localStorage.getItem('accessToken')
        const userData = localStorage.getItem('user')
        
        if (token && userData) {
          const parsedUser = JSON.parse(userData)
          setUser(parsedUser)
          apiService.setToken(token)
        }
      } catch (error) {
        console.error('Erro ao inicializar autenticação:', error)
        // Limpar dados corrompidos
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (credentials: LoginForm) => {
    try {
      const response = await apiService.login(credentials)
      setUser(response.user)
    } catch (error) {
      console.error('Erro no login:', error)
      throw error
    }
  }

  const signup = async (userData: SignupForm) => {
    try {
      const response = await apiService.signup(userData)
      setUser(response.user)
    } catch (error) {
      console.error('Erro no cadastro:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await apiService.logout()
    } catch (error) {
      console.error('Erro no logout:', error)
    } finally {
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
}