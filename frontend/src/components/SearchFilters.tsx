import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { debounce } from "@/lib/utils"
import type { SearchFilters } from "@/types"
import { Search } from "lucide-react"
import { useCallback, useState } from "react"

interface SearchFiltersProps {
	onFiltersChange: (filters: SearchFilters) => void
	isLoading?: boolean
}

export function SearchFiltersComponent({
	onFiltersChange,
	isLoading,
}: SearchFiltersProps) {
	const [filters, setFilters] = useState<SearchFilters>({
		search: "",
		startDate: "",
		endDate: "",
	})

	// Debounce para otimizar as buscas
	const debouncedSearch = useCallback(
		debounce((newFilters: SearchFilters) => {
			onFiltersChange(newFilters)
		}, 300),
		[onFiltersChange],
	)

	const handleFilterChange = (key: keyof SearchFilters, value: string) => {
		const newFilters = { ...filters, [key]: value }
		setFilters(newFilters)

		// Para campos de data, aplicar imediatamente
		if (key === "startDate" || key === "endDate") {
			onFiltersChange(newFilters)
		} else {
			// Para busca por texto, usar debounce
			debouncedSearch(newFilters)
		}
	}

	const handleSearch = () => {
		onFiltersChange(filters)
	}

	const handleClearFilters = () => {
		const clearedFilters: SearchFilters = {
			search: "",
			startDate: "",
			endDate: "",
		}
		setFilters(clearedFilters)
		onFiltersChange(clearedFilters)
	}

	return (
		<div className="py-2">
			<div className="flex flex-col md:flex-row md:items-end gap-4">
				{/* Campo de busca */}
				<div className="flex flex-col items-start">
					<Label htmlFor="search" className="text-sm font-medium text-secondary">
						Pesquisar
					</Label>
					<div className="relative mt-1">
						<Input
							id="search"
							type="text"
							placeholder="Digite o número do processo ou nome das partes envolvidas"
							value={filters.search}
							onChange={(e) => handleFilterChange("search", e.target.value)}
							className="border-border-input h-8 rounded-sm w-[400px] text-xs"
						/>
					</div>
				</div>

				<div className="flex flex-col items-start">
					{/* Data do diário - De */}
					<Label htmlFor="startDate" className="text-sm font-medium text-secondary">
						Data do diário
					</Label>
					<div className="flex flex-row items-center gap-2">
						<div className="flex flex-col items-start gap-2">
							<div className="mt-1 flex flex-row items-center gap-2">
								<Label htmlFor="startDate" className="text-xs text-gray-500">
									De:
								</Label>
								<Input
									id="startDate"
									type="date"
									value={filters.startDate}
									onChange={(e) => handleFilterChange("startDate", e.target.value)}
									placeholder="DD/MM/AAAA"
									className="border-border-input h-8 rounded-sm w-36"
								/>
							</div>
						</div>

						{/* Data do diário - Até */}
						<div className="flex flex-col items-end gap-2">
							<div className="mt-1 flex flex-row items-center gap-2">
								<Label htmlFor="endDate" className="text-xs text-gray-500">
									Até:
								</Label>
								<Input
									id="endDate"
									type="date"
									value={filters.endDate}
									onChange={(e) => handleFilterChange("endDate", e.target.value)}
									placeholder="DD/MM/AAAA"
									className="border-border-input h-8 rounded-sm w-36"
								/>
							</div>
						</div>

						{/* Botões */}
						<div className="flex flex-row items-center mt-1">
							<Button
								type="button"
								variant="default"
								onClick={handleSearch}
								className="flex-1 text-white bg-primary rounded-sm p-2 h-8"
								disabled={isLoading}
							>
								<Search className="h-4 w-4" />
							</Button>
						</div>
					</div>
				</div>
			</div>
		</div>
	)
}
