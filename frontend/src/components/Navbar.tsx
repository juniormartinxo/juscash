import { LogOut } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import Logo from './Logo'

export function Navbar() {
  const { logout } = useAuth()
  const { toast } = useToast()

  const handleLogout = async () => {
    try {
      await logout()
      toast({
        title: "Logout realizado",
        description: "Você foi desconectado com sucesso",
      })
    } catch (error) {
      toast({
        title: "Erro no logout",
        description: "Ocorreu um erro ao fazer logout",
        variant: "destructive",
      })
    }
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo JusCash à esquerda */}
          <div className="flex items-center">
            <div className="flex items-center space-x-2">
              <Logo />
            </div>
          </div>

          {/* Botão de logout à direita */}
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="flex items-center space-x-2 text-secondary cursor-pointer relative w-20"
            >
              <span className="absolute flex flex-row items-center opacity-100 hover:opacity-0 transition-opacity duration-300">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sair</span>
              </span>

              <span className="absolute flex flex-row items-center hover:animate-ping opacity-0 hover:opacity-100 transition-opacity duration-300 p-3">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sair</span>
              </span>

            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}