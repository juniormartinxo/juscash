# 📚 Documentação JusCash

Esta pasta contém a documentação completa do sistema JusCash, organizada em dois documentos principais:

## 📋 Documentos Disponíveis

### 1. Manual de Produto (`Manual-de-Produto-JusCash.md`)
**Público-alvo**: Usuários finais, advogados, gestores  
**Conteúdo**:
- Introdução ao sistema
- Guia de uso da interface
- Fluxo de trabalho recomendado
- FAQ e solução de problemas
- Informações de suporte

### 2. Documentação Técnica (Partes 1, 2 e 3)
**Público-alvo**: Desenvolvedores, administradores de sistema, equipe técnica  
**Conteúdo**:
- **Parte 1** (`Documentacao-Tecnica-JusCash.md`): Arquitetura, tecnologias, estrutura da API, banco de dados
- **Parte 2** (`Documentacao-Tecnica-JusCash-Parte2.md`): Sistema de scraping, frontend React, hooks customizados
- **Parte 3** (`Documentacao-Tecnica-JusCash-Parte3.md`): Infraestrutura, segurança, instalação, guias de desenvolvimento

## 🔄 Como Converter para PDF

### Opção 1: Usando Pandoc (Recomendado)

#### Pré-requisitos:
```bash
# Ubuntu/Debian
sudo apt-get install pandoc texlive-xetex texlive-fonts-recommended texlive-latex-recommended

# macOS
brew install pandoc
brew install --cask mactex

# Windows (usando Chocolatey)
choco install pandoc miktex
```

#### Conversão do Manual de Produto:
```bash
cd docs

# Manual de Produto
pandoc Manual-de-Produto-JusCash.md \
  -o "Manual de Produto - JusCash.pdf" \
  --pdf-engine=xelatex \
  --variable geometry:margin=2cm \
  --variable fontsize=11pt \
  --variable documentclass=article \
  --variable papersize=a4 \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --highlight-style=github \
  --include-in-header=header.tex
```

#### Conversão da Documentação Técnica:
```bash
# Combinar todas as partes em um único PDF
pandoc \
  Documentacao-Tecnica-JusCash.md \
  Documentacao-Tecnica-JusCash-Parte2.md \
  Documentacao-Tecnica-JusCash-Parte3.md \
  -o "Documentacao Tecnica - JusCash.pdf" \
  --pdf-engine=xelatex \
  --variable geometry:margin=2cm \
  --variable fontsize=10pt \
  --variable documentclass=article \
  --variable papersize=a4 \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --highlight-style=github \
  --listings \
  --include-in-header=header.tex
```

### Opção 2: Usando Markdown to PDF (VS Code)

1. Instale a extensão "Markdown PDF" no VS Code
2. Abra cada arquivo `.md`
3. Pressione `Ctrl+Shift+P` e digite "Markdown PDF: Export (pdf)"
4. Selecione a opção desejada

### Opção 3: Usando Typora

1. Instale o Typora (editor Markdown)
2. Abra cada arquivo `.md`
3. Vá em `File > Export > PDF`
4. Configure as opções de exportação

### Opção 4: Script Automatizado

Crie um script `convert-to-pdf.sh`:

```bash
#!/bin/bash

echo "🔄 Convertendo documentação JusCash para PDF..."

# Verificar se pandoc está instalado
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc não encontrado. Instale o pandoc primeiro."
    exit 1
fi

# Criar pasta de saída
mkdir -p pdfs

# Converter Manual de Produto
echo "📋 Convertendo Manual de Produto..."
pandoc Manual-de-Produto-JusCash.md \
  -o "pdfs/Manual de Produto - JusCash.pdf" \
  --pdf-engine=xelatex \
  --variable geometry:margin=2cm \
  --variable fontsize=11pt \
  --variable documentclass=article \
  --variable papersize=a4 \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --highlight-style=github

# Converter Documentação Técnica
echo "🔧 Convertendo Documentação Técnica..."
pandoc \
  Documentacao-Tecnica-JusCash.md \
  Documentacao-Tecnica-JusCash-Parte2.md \
  Documentacao-Tecnica-JusCash-Parte3.md \
  -o "pdfs/Documentacao Tecnica - JusCash.pdf" \
  --pdf-engine=xelatex \
  --variable geometry:margin=2cm \
  --variable fontsize=10pt \
  --variable documentclass=article \
  --variable papersize=a4 \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --highlight-style=github \
  --listings

echo "✅ Conversão concluída! PDFs salvos na pasta 'pdfs/'"
```

## 🎨 Personalização de Estilo

### Arquivo de Header LaTeX (`header.tex`)

Crie um arquivo `header.tex` para personalizar o estilo:

```latex
% Configurações de fonte
\usepackage{fontspec}
\setmainfont{Arial}
\setmonofont{Courier New}

% Configurações de cor
\usepackage{xcolor}
\definecolor{primarycolor}{RGB}{59, 130, 246}
\definecolor{secondarycolor}{RGB}{107, 114, 128}

% Configurações de cabeçalho e rodapé
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\rhead{JusCash - Sistema de Gerenciamento DJE}
\lfoot{Confidencial}
\rfoot{\thepage}

% Configurações de código
\usepackage{listings}
\lstset{
    basicstyle=\ttfamily\footnotesize,
    backgroundcolor=\color{gray!10},
    frame=single,
    breaklines=true,
    numbers=left,
    numberstyle=\tiny\color{gray},
    keywordstyle=\color{blue},
    commentstyle=\color{green!50!black},
    stringstyle=\color{red}
}

% Configurações de links
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=primarycolor,
    urlcolor=primarycolor,
    pdftitle={JusCash - Documentação},
    pdfauthor={Equipe JusCash},
    pdfsubject={Sistema de Gerenciamento DJE},
    pdfkeywords={JusCash, DJE, Documentação}
}
```

## 📁 Estrutura Recomendada

```
docs/
├── README-Documentacao.md              # Este arquivo
├── Manual-de-Produto-JusCash.md        # Manual do usuário
├── Documentacao-Tecnica-JusCash.md     # Doc técnica parte 1
├── Documentacao-Tecnica-JusCash-Parte2.md  # Doc técnica parte 2
├── Documentacao-Tecnica-JusCash-Parte3.md  # Doc técnica parte 3
├── header.tex                          # Estilo LaTeX
├── convert-to-pdf.sh                   # Script conversão
└── pdfs/                              # PDFs gerados
    ├── Manual de Produto - JusCash.pdf
    └── Documentacao Tecnica - JusCash.pdf
```

## 🔧 Customizações Avançadas

### Adicionando Logo da Empresa

1. Salve o logo como `logo.png` na pasta `docs/`
2. Adicione ao `header.tex`:

```latex
\usepackage{graphicx}
\usepackage{eso-pic}

% Logo no cabeçalho
\AddToShipoutPictureBG*{
  \AtPageUpperLeft{
    \raisebox{-\height}{\includegraphics[width=3cm]{logo.png}}
  }
}
```

### Numeração Personalizada

Adicione ao comando pandoc:
```bash
--variable numbersections=true \
--variable secnumdepth=3 \
```

### Watermark (Marca d'água)

Adicione ao `header.tex`:
```latex
\usepackage{draftwatermark}
\SetWatermarkText{CONFIDENCIAL}
\SetWatermarkScale{1}
\SetWatermarkLightness{0.9}
```

## 🚀 Automação com GitHub Actions

Crie `.github/workflows/docs.yml`:

```yaml
name: Generate Documentation PDFs

on:
  push:
    paths:
      - 'docs/*.md'
    branches: [main]

jobs:
  generate-pdfs:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install Pandoc
      run: |
        sudo apt-get update
        sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended
    
    - name: Generate PDFs
      run: |
        cd docs
        chmod +x convert-to-pdf.sh
        ./convert-to-pdf.sh
    
    - name: Upload PDFs
      uses: actions/upload-artifact@v3
      with:
        name: documentation-pdfs
        path: docs/pdfs/*.pdf
```

## 📋 Checklist de Qualidade

Antes de finalizar os PDFs, verifique:

- [ ] ✅ Todos os links internos funcionam
- [ ] ✅ Imagens e diagramas estão visíveis
- [ ] ✅ Código está bem formatado
- [ ] ✅ Índice está correto e completo
- [ ] ✅ Numeração de páginas está correta
- [ ] ✅ Informações de contato estão atualizadas
- [ ] ✅ Versão e data estão corretas
- [ ] ✅ Não há erros de ortografia
- [ ] ✅ Formatação está consistente

## 🔄 Atualizações

### Processo de Atualização

1. **Edite os arquivos Markdown** conforme necessário
2. **Atualize as versões** nos documentos
3. **Execute o script de conversão**
4. **Revise os PDFs gerados**
5. **Distribua para as equipes**

### Controle de Versão

Mantenha um histórico de versões:

| Versão | Data | Mudanças | Responsável |
|--------|------|----------|-------------|
| 1.0 | Jan/2024 | Versão inicial | Equipe Dev |
| 1.1 | - | - | - |

## 📞 Suporte

Para dúvidas sobre a documentação:

- **Email**: docs@juscash.com
- **Slack**: #juscash-docs
- **GitHub Issues**: Para melhorias na documentação

---

**Última atualização**: Janeiro 2024  
**Responsável**: Equipe de Documentação JusCash 