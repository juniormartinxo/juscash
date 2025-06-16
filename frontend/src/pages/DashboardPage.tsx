import { useState } from 'react'
import { Scale } from 'lucide-react'
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

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navbar fixa */}
      <Navbar />
      
      {/* Conteúdo principal */}
      <main className="pt-16"> {/* pt-16 para compensar a navbar fixa */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header da página */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-2">
              <Scale className="h-6 w-6 text-primary-500" />
              <h1 className="text-2xl font-bold text-secondary-500">
                Publicações
              </h1>
            </div>
            <p className="text-gray-600 text-sm">
              Gerencie e acompanhe as publicações do Diário da Justiça Eletrônico
            </p>
          </div>

          {/* Filtros de busca */}
          <SearchFiltersComponent 
            onFiltersChange={handleFiltersChange}
          />

          {/* Board Kanban */}
          <div className="h-[calc(100vh-300px)]"> {/* Altura fixa para o kanban */}
            <KanbanBoard filters={filters} />
          </div>
        </div>
      </main>
    </div>
  )
}