#!/bin/bash

# Script para conversão automática da documentação JusCash para PDF
# Autor: Equipe JusCash
# Data: Janeiro 2024

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir mensagens coloridas
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $BLUE "🔄 Iniciando conversão da documentação JusCash para PDF..."

# Verificar se pandoc está instalado
if ! command -v pandoc &> /dev/null; then
    print_message $RED "❌ Pandoc não encontrado!"
    print_message $YELLOW "📥 Instale o pandoc primeiro:"
    print_message $YELLOW "   Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex texlive-fonts-recommended"
    print_message $YELLOW "   macOS: brew install pandoc && brew install --cask mactex"
    print_message $YELLOW "   Windows: choco install pandoc miktex"
    exit 1
fi

print_message $GREEN "✅ Pandoc encontrado: $(pandoc --version | head -n1)"

# Verificar se XeLaTeX está disponível
if ! command -v xelatex &> /dev/null; then
    print_message $YELLOW "⚠️  XeLaTeX não encontrado. Usando motor PDF padrão."
    PDF_ENGINE="--pdf-engine=pdflatex"
else
    PDF_ENGINE="--pdf-engine=xelatex"
    print_message $GREEN "✅ XeLaTeX encontrado"
fi

# Criar pasta de saída
mkdir -p pdfs
print_message $BLUE "📁 Pasta 'pdfs' criada/verificada"

# Verificar existência dos arquivos fonte
files_to_check=(
    "Manual-de-Produto-JusCash.md"
    "Documentacao-Tecnica-JusCash.md"
    "Documentacao-Tecnica-JusCash-Parte2.md"
    "Documentacao-Tecnica-JusCash-Parte3.md"
)

for file in "${files_to_check[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_message $RED "❌ Arquivo não encontrado: $file"
        exit 1
    fi
done

print_message $GREEN "✅ Todos os arquivos fonte encontrados"

# Função para converter com tratamento de erro
convert_with_retry() {
    local input_files="$1"
    local output_file="$2"
    local doc_type="$3"
    local font_size="$4"
    
    print_message $BLUE "📋 Convertendo $doc_type..."
    
    # Tentar com XeLaTeX primeiro, depois fallback para pdflatex
    if ! pandoc $input_files \
        -o "pdfs/$output_file" \
        $PDF_ENGINE \
        --variable geometry:margin=2cm \
        --variable fontsize=$font_size \
        --variable documentclass=article \
        --variable papersize=a4 \
        --toc \
        --toc-depth=3 \
        --number-sections \
        --highlight-style=github \
        --listings \
        --standalone \
        --metadata title="$doc_type" \
        --metadata author="Equipe JusCash" \
        --metadata date="$(date '+%B %Y')" \
        2>/dev/null; then
        
        print_message $YELLOW "⚠️  Tentativa com $PDF_ENGINE falhou. Tentando com pdflatex..."
        
        if ! pandoc $input_files \
            -o "pdfs/$output_file" \
            --pdf-engine=pdflatex \
            --variable geometry:margin=2cm \
            --variable fontsize=$font_size \
            --variable documentclass=article \
            --variable papersize=a4 \
            --toc \
            --toc-depth=3 \
            --number-sections \
            --highlight-style=github \
            --standalone \
            --metadata title="$doc_type" \
            --metadata author="Equipe JusCash" \
            --metadata date="$(date '+%B %Y')"; then
            
            print_message $RED "❌ Falha na conversão de $doc_type"
            return 1
        fi
    fi
    
    print_message $GREEN "✅ $doc_type convertido com sucesso!"
    return 0
}

# Converter Manual de Produto
if convert_with_retry \
    "Manual-de-Produto-JusCash.md" \
    "Manual de Produto - JusCash.pdf" \
    "Manual de Produto JusCash" \
    "11pt"; then
    
    manual_size=$(du -h "pdfs/Manual de Produto - JusCash.pdf" | cut -f1)
    print_message $GREEN "📄 Manual de Produto: $manual_size"
fi

# Converter Documentação Técnica (combinando todas as partes)
if convert_with_retry \
    "Documentacao-Tecnica-JusCash.md Documentacao-Tecnica-JusCash-Parte2.md Documentacao-Tecnica-JusCash-Parte3.md" \
    "Documentacao Tecnica - JusCash.pdf" \
    "Documentação Técnica JusCash" \
    "10pt"; then
    
    doc_size=$(du -h "pdfs/Documentacao Tecnica - JusCash.pdf" | cut -f1)
    print_message $GREEN "📄 Documentação Técnica: $doc_size"
fi

# Converter documentações individuais (opcional)
print_message $BLUE "📋 Criando versões individuais da documentação técnica..."

# Parte 1
if convert_with_retry \
    "Documentacao-Tecnica-JusCash.md" \
    "Documentacao Tecnica - Parte 1 - Arquitetura e API.pdf" \
    "Documentação Técnica - Parte 1" \
    "10pt"; then
    print_message $GREEN "✅ Parte 1 convertida"
fi

# Parte 2
if convert_with_retry \
    "Documentacao-Tecnica-JusCash-Parte2.md" \
    "Documentacao Tecnica - Parte 2 - Scraping e Frontend.pdf" \
    "Documentação Técnica - Parte 2" \
    "10pt"; then
    print_message $GREEN "✅ Parte 2 convertida"
fi

# Parte 3
if convert_with_retry \
    "Documentacao-Tecnica-JusCash-Parte3.md" \
    "Documentacao Tecnica - Parte 3 - Infraestrutura e DevOps.pdf" \
    "Documentação Técnica - Parte 3" \
    "10pt"; then
    print_message $GREEN "✅ Parte 3 convertida"
fi

# Listar arquivos gerados
print_message $BLUE "📂 Arquivos PDF gerados:"
ls -la pdfs/*.pdf | while read -r line; do
    filename=$(echo "$line" | awk '{print $9}')
    size=$(echo "$line" | awk '{print $5}')
    print_message $GREEN "   $(basename "$filename") ($size bytes)"
done

# Calcular tamanho total
total_size=$(du -sh pdfs/ | cut -f1)
file_count=$(ls -1 pdfs/*.pdf | wc -l)

print_message $GREEN "✅ Conversão concluída com sucesso!"
print_message $BLUE "📊 Resumo:"
print_message $BLUE "   • $file_count arquivos PDF gerados"
print_message $BLUE "   • Tamanho total: $total_size"
print_message $BLUE "   • Localização: $(pwd)/pdfs/"

# Verificar integridade dos PDFs
print_message $BLUE "🔍 Verificando integridade dos PDFs..."
all_valid=true

for pdf in pdfs/*.pdf; do
    if [[ -f "$pdf" ]]; then
        # Verificar se o arquivo não está vazio e tem header PDF
        if [[ $(file "$pdf" | grep -c "PDF") -eq 1 ]]; then
            print_message $GREEN "✅ $(basename "$pdf") - OK"
        else
            print_message $RED "❌ $(basename "$pdf") - Arquivo corrompido"
            all_valid=false
        fi
    fi
done

if $all_valid; then
    print_message $GREEN "🎉 Todos os PDFs foram gerados corretamente!"
else
    print_message $YELLOW "⚠️  Alguns PDFs podem estar corrompidos. Verifique manualmente."
fi

print_message $BLUE "📖 Para visualizar os PDFs:"
print_message $BLUE "   • Manual de Produto: pdfs/Manual de Produto - JusCash.pdf"
print_message $BLUE "   • Documentação Técnica: pdfs/Documentacao Tecnica - JusCash.pdf"

print_message $GREEN "�� Script concluído!" 