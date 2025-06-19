import { cn, formatDate, getTimeAgo } from "@/lib/utils"
import type { Publication } from "@/types"
import { Clock } from "lucide-react"

interface PublicationCardProps {
	publication: Publication
	onClick: () => void
	isDragging?: boolean
}

export function PublicationCard({
	publication,
	onClick,
	isDragging,
}: PublicationCardProps) {
	return (
		<div
			className={cn(
				"kanban-card bg-background-kanban rounded-lg border border-gray-200 p-4 shadow-sm cursor-pointer",
				isDragging ? "rotate-2 shadow-lg" : "hover:shadow-md",
				"flex flex-col gap-2"
			)}
			onClick={onClick}
		>
			{/* Número do processo */}
			<div className="font-normal text-secondary/85 text-xs">
				{publication.process_number}
			</div>

			{/* Datas */}
			<div className="flex flex-row gap-8">
				{/* Data de atualização */}
				<div className="flex flex-row items-center text-xs text-secondary/75">
					<Clock className="h-2 w-2 mr-1" />
					<span>{getTimeAgo(publication?.publication_date ?? '')}</span>
					{/* Tempo desde a criação */}
				</div>

				{/* Data de disponibilização */}
				<div className="flex flex-row items-center text-xs text-secondary/75">
					<svg
						className="h-3 w-3 mr-1"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<rect
							x="3"
							y="4"
							width="18"
							height="18"
							rx="2"
							ry="2"
							strokeWidth="2"
						/>
						<line x1="16" y1="2" x2="16" y2="6" strokeWidth="2" />
						<line x1="8" y1="2" x2="8" y2="6" strokeWidth="2" />
						<line x1="3" y1="10" x2="21" y2="10" strokeWidth="2" />
					</svg>
					<span>{formatDate(publication.availability_date)}</span>
				</div>
			</div>
		</div>
	)
}
