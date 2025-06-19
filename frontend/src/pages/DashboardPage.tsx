import { useState } from 'react'
import { Scale, X } from 'lucide-react'
import { TbClockCog } from 'react-icons/tb'
import { Navbar } from '@/components/Navbar'
import { SearchFiltersComponent } from '@/components/SearchFilters'
import { KanbanBoard } from '@/components/KanbanBoard'
import type { SearchFilters } from '@/types'

export function DashboardPage() {
  const [filters, setFilters] = useState<SearchFilters>({
    search: '',
    startDate: '',
    endDate: '',
  })
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
  }

  return (
    <div className="min-h-screen bg-background min-w-[1000px]">
      {/* Navbar fixa */}
      <Navbar />

      {/* Conteúdo principal */}
      <main className="pt-16"> {/* pt-16 para compensar a navbar fixa */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header da página */}
          <div className="mb-8 flex flex-col md:flex-row md:justify-between md:items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <Scale className="h-6 w-6 text-secondary" />
              <h1 className="text-3xl font-semibold text-secondary">
                Publicações
              </h1>
            </div>

            {/* Filtros de busca */}
            <SearchFiltersComponent onFiltersChange={handleFiltersChange} />
          </div>

          {/* Board Kanban */}
          <div className="min-h-72"> {/* Altura fixa para o kanban */}
            <KanbanBoard filters={filters} />
          </div>

          {/* Botão tipo aba no canto direito */}
          <div className="fixed right-0 top-1/2 transform -translate-y-1/2 z-10">
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="bg-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-l-lg p-4 border border-r-0 border-gray-200 hover:translate-x-1 cursor-pointer"
              title="Configurações"
            >
              <TbClockCog size={24} className="text-primary" />
            </button>
          </div>
        </div>
      </main>

      {/* Drawer */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Overlay */}
          <div
            className="absolute inset-0 bg-black/45 transition-opacity"
            onClick={() => setIsDrawerOpen(false)}
          />

          {/* Drawer content */}
          <div className="absolute right-0 top-0 h-full w-96 bg-white shadow-xl transform transition-transform">
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <TbClockCog size={20} className="text-primary" />
                  <h2 className="text-lg font-semibold text-gray-900">
                    Configurações
                  </h2>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X size={20} className="text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 p-6 overflow-y-auto">
                <p className="text-gray-600">
                  Configurações de tempo e agendamentos serão implementadas aqui.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}