import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog"
import { formatCurrency, formatDate } from "@/lib/utils"
import type { Publication } from "@/types"

interface PublicationModalProps {
	publication: Publication | null
	isOpen: boolean
	onClose: () => void
}

export function PublicationModal({
	publication,
	isOpen,
	onClose,
}: PublicationModalProps) {
	if (!publication) return null

	return (
		<Dialog open={isOpen} onOpenChange={onClose}>
			<DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="text-md font-bold text-secondary mb-4">
						Publicação - {publication.process_number}
					</DialogTitle>
					<DialogDescription className="sr-only">
						Detalhes da publicação do processo {publication.process_number}
					</DialogDescription>
				</DialogHeader>

				<div className="space-y-6">
					{/* Data de publicação no DJE */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Data de publicação no DJE
						</h3>
						<p className="text-sm text-secondary/75">
							{publication.publication_date
								? formatDate(publication.publication_date)
								: formatDate(publication.availability_date)}
						</p>
					</div>

					{/* Autor(es) */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Autor (es)
						</h3>
						<ul className="list-disc list-inside text-sm space-y-1 text-secondary/75">
							{publication.authors.map((author, index) => (
								<li key={index}>{author}</li>
							))}
						</ul>
					</div>

					{/* Réu */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">Réu</h3>
						<ul className="list-disc list-inside text-sm text-secondary/75">
							<li>{publication.defendant}</li>
						</ul>
					</div>

					{/* Advogado(s) */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Advogado(s)
						</h3>
						{publication.lawyers && publication.lawyers.length > 0 ? (
							<ul className="list-disc list-inside text-sm space-y-1 text-secondary/75">
								{publication.lawyers.map((lawyer, index) => (
									<li key={index}>
										{lawyer.name} (OAB: {lawyer.oab})
									</li>
								))}
							</ul>
						) : (
							<p className="text-sm text-gray-500">Não informado</p>
						)}
					</div>

					{/* Valor principal bruto/líquido */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Valor principal bruto/líquido
						</h3>
						<div className="text-sm space-y-1 text-secondary/75">
							{publication.gross_value && (
								<p>Bruto: {formatCurrency(publication.gross_value)}</p>
							)}
							{publication.net_value && (
								<p>Líquido: {formatCurrency(publication.net_value)}</p>
							)}
							{!publication.gross_value && !publication.net_value && (
								<p className="text-gray-500">Não informado</p>
							)}
						</div>
					</div>

					{/* Valor dos juros moratórios */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Valor dos juros moratórios
						</h3>
						<p className="text-sm text-secondary/75">
							{publication.interest_value
								? formatCurrency(publication.interest_value)
								: "Não informado"}
						</p>
					</div>

					{/* Valor dos honorários advocatícios */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-1">
							Valor dos honorários advocatícios
						</h3>
						<p className="text-sm text-secondary/75">
							{publication.attorney_fees
								? formatCurrency(publication.attorney_fees)
								: "N/A"}
						</p>
					</div>

					{/* Conteúdo da Publicação */}
					<div>
						<h3 className="font-medium text-sm text-secondary/75 mb-2">
							Conteúdo da Publicação
						</h3>
						<div className="rounded-md max-h-60 overflow-y-auto text-secondary/75">
							<p className="text-sm whitespace-pre-wrap leading-relaxed">
								{publication.content}
							</p>
						</div>
					</div>
				</div>
			</DialogContent>
		</Dialog>
	)
}
