import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { debounce } from "@/lib/utils";
import type { SearchFilters } from "@/types";
import { Search } from "lucide-react";
import { useCallback, useState } from "react";

interface SearchFiltersProps {
	onFiltersChange: (filters: SearchFilters) => void;
	isLoading?: boolean;
}

export function SearchFiltersComponent({
	onFiltersChange,
	isLoading,
}: SearchFiltersProps) {
	const [filters, setFilters] = useState<SearchFilters>({
		search: "",
		startDate: "",
		endDate: "",
	});

	// Debounce para otimizar as buscas
	const debouncedSearch = useCallback(
		debounce((newFilters: SearchFilters) => {
			onFiltersChange(newFilters);
		}, 300),
		[onFiltersChange],
	);

	const handleFilterChange = (key: keyof SearchFilters, value: string) => {
		const newFilters = { ...filters, [key]: value };
		setFilters(newFilters);

		// Para campos de data, aplicar imediatamente
		if (key === "startDate" || key === "endDate") {
			onFiltersChange(newFilters);
		} else {
			// Para busca por texto, usar debounce
			debouncedSearch(newFilters);
		}
	};

	const handleSearch = () => {
		onFiltersChange(filters);
	};

	const handleClearFilters = () => {
		const clearedFilters: SearchFilters = {
			search: "",
			startDate: "",
			endDate: "",
		};
		setFilters(clearedFilters);
		onFiltersChange(clearedFilters);
	};

	return (
		<div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-6">
			<div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-end">
				{/* Campo de busca */}
				<div className="lg:col-span-6">
					<Label htmlFor="search" className="text-sm font-medium">
						Pesquisar
					</Label>
					<div className="relative mt-1">
						<Input
							id="search"
							type="text"
							placeholder="Digite o número do processo ou nome das partes envolvidas"
							value={filters.search}
							onChange={(e) => handleFilterChange("search", e.target.value)}
							className="pl-10"
						/>
						<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
					</div>
				</div>

				{/* Data do diário - De */}
				<div className="lg:col-span-2">
					<Label htmlFor="startDate" className="text-sm font-medium">
						Data do diário
					</Label>
					<div className="mt-1">
						<Label htmlFor="startDate" className="text-xs text-gray-500">
							De:
						</Label>
						<Input
							id="startDate"
							type="date"
							value={filters.startDate}
							onChange={(e) => handleFilterChange("startDate", e.target.value)}
							placeholder="DD/MM/AAAA"
						/>
					</div>
				</div>

				{/* Data do diário - Até */}
				<div className="lg:col-span-2">
					<div className="mt-1">
						<Label htmlFor="endDate" className="text-xs text-gray-500">
							Até:
						</Label>
						<Input
							id="endDate"
							type="date"
							value={filters.endDate}
							onChange={(e) => handleFilterChange("endDate", e.target.value)}
							placeholder="DD/MM/AAAA"
						/>
					</div>
				</div>

				{/* Botões */}
				<div className="lg:col-span-2 flex space-x-2">
					<Button
						type="button"
						onClick={handleSearch}
						className="flex-1"
						disabled={isLoading}
					>
						<Search className="h-4 w-4" />
					</Button>
					<Button
						type="button"
						variant="outline"
						onClick={handleClearFilters}
						disabled={isLoading}
						className="px-3"
					>
						Limpar
					</Button>
				</div>
			</div>
		</div>
	);
}
