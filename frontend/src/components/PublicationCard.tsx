import { formatDate } from "@/lib/utils";
import type { Publication } from "@/types";
import { Clock } from "lucide-react";

interface PublicationCardProps {
	publication: Publication;
	onClick: () => void;
	isDragging?: boolean;
}

export function PublicationCard({
	publication,
	onClick,
	isDragging,
}: PublicationCardProps) {
	return (
		<div
			className={`
        kanban-card 
        bg-white 
        rounded-lg 
        border 
        border-gray-200 
        p-4 
        shadow-sm 
        cursor-pointer
        ${isDragging ? "rotate-2 shadow-lg" : "hover:shadow-md"}
      `}
			onClick={onClick}
		>
			{/* Número do processo */}
			<div className="font-semibold text-secondary text-sm mb-3">
				{publication.process_number}
			</div>

			{/* Datas */}
			<div className="space-y-2">
				{/* Data de atualização */}
				<div className="flex items-center text-xs text-gray-500">
					<Clock className="h-3 w-3 mr-1" />
					<span>3h</span>{" "}
					{/* Tempo desde a última atualização - simplificado */}
				</div>

				{/* Data de disponibilização */}
				<div className="flex items-center text-xs text-gray-600">
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

			{/* Status visual - pequena barra colorida */}
			<div className="mt-3 pt-3 border-t border-gray-100">
				<div
					className={`
            h-1 w-full rounded-full
            ${publication.status === "NOVA" ? "bg-blue-400" : ""}
            ${publication.status === "LIDA" ? "bg-yellow-400" : ""}
            ${publication.status === "ENVIADA_PARA_ADV" ? "bg-orange-400" : ""}
            ${publication.status === "CONCLUIDA" ? "bg-green-400" : ""}
          `}
				/>
			</div>
		</div>
	);
}
