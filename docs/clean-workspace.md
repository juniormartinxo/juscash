# Script de Limpeza do Workspace

Este script foi desenvolvido para limpar automaticamente arquivos e diretórios temporários ou de dependências do projeto, ajudando a manter o workspace organizado e liberar espaço em disco.

## Localização

O script está localizado em:

```bash
scripts/clean-workspace.sh
```

## O que o script remove

O script remove os seguintes itens:

1. **Arquivos de backup do .env**
   - Remove todos os arquivos que seguem o padrão `.env.backup.*` na raiz do projeto
   - Exemplo: `.env.backup.2024-03-20`

2. **Pastas node_modules**
   - Remove todas as pastas `node_modules` encontradas em qualquer diretório do projeto
   - Isso inclui as pastas `node_modules` do frontend, backend e quaisquer outros módulos

3. **Arquivos pnpm-lock.yaml**
   - Remove todos os arquivos `pnpm-lock.yaml` encontrados no projeto
   - Estes são arquivos de lock do gerenciador de pacotes pnpm

4. **Ambiente virtual Python do scraper**
   - Remove a pasta `venv` localizada em `backend/scraper/venv`
   - Esta é a pasta do ambiente virtual Python usado pelo scraper

## Como usar

1. Certifique-se de que o script tem permissão de execução:

   ```bash
   chmod +x scripts/clean-workspace.sh
   ```

2. Execute o script:

   ```bash
   ./scripts/clean-workspace.sh
   ```

## Observações importantes

- O script é seguro para executar, pois remove apenas arquivos e diretórios específicos
- Todas as operações são realizadas de forma recursiva, garantindo que todos os itens sejam removidos
- O script exibe mensagens informativas durante a execução para acompanhamento do progresso
- Após a execução, você precisará reinstalar as dependências do projeto:
  - Para Node.js: `pnpm install`
  - Para Python (scraper): Recriar o ambiente virtual e instalar as dependências

## Quando usar

Recomenda-se executar este script quando:

- Houver problemas com dependências corrompidas
- Necessidade de liberar espaço em disco
- Antes de fazer um novo clone do repositório
- Após mudanças significativas nas dependências do projeto
