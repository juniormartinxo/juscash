# API do Scraper

Esta API permite controlar o scraper e o serviço de monitoramento através de endpoints HTTP.

## Instalação

1. Instale as dependências adicionais:

```bash
pip install fastapi uvicorn
```

## Iniciando a API

Execute o seguinte comando na pasta raiz do scraper:

```bash
python start_api.py
```

A API estará disponível em `http://localhost:8000`.

## Documentação da API

A documentação interativa da API estará disponível em:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Executar Comandos

**POST** `/run`

Executa um comando do scraper em background.

Comandos disponíveis:

- `monitor`: Inicia o monitoramento de arquivos JSON
- `scraper`: Executa o scraper básico (scraper_cli.py run)
- `multi_date_scraper`: Executa o scraper para múltiplas datas
- `scraper_cli`: Executa o scraper via CLI (mesmo que 'scraper')

Exemplo de requisição para iniciar o monitoramento:

```json
{
    "command": "monitor",
    "args": {
        "api_endpoint": "http://localhost:8000"
    }
}
```

Exemplo de requisição para executar o scraper:

```json
{
    "command": "scraper",
    "args": {
        "date": "2025-06-15"
    }
}
```

Exemplo de requisição para executar o multi-date scraper:

```json
{
    "command": "multi_date_scraper",
    "args": {
        "start_date": "2025-06-15",
        "end_date": "2025-06-17"
    }
}
```

### Endpoints Específicos

**POST** `/run/multi-date-scraper`

Executa o scraper para múltiplas datas em background.

```json
{
    "args": {
        "start_date": "2025-06-15",
        "end_date": "2025-06-17"
    }
}
```

**POST** `/run/scraper-cli`

Executa o scraper CLI em background.

```json
{
    "args": {
        "date": "2025-06-15"
    }
}
```

### Verificar Status

**GET** `/status`

Retorna o status dos serviços do scraper.

Exemplo de resposta:

```json
{
    "monitor": true,
    "scraper": false
}
```

### Parar Serviços

**POST** `/stop/{service}`

Para um serviço específico. O parâmetro `service` pode ser:

- `monitor`: Para o serviço de monitoramento
- `scraper`: Para o scraper

## Exemplos de Uso com cURL

1. Iniciar o monitoramento:

    ```bash
    curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"command": "monitor", "args": {"api_endpoint": "http://localhost:8000"}}'
    ```

2. Executar o scraper:

    ```bash
    curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"command": "scraper", "args": {"date": "2025-06-15"}}'
    ```

3. Verificar status:

    ```bash
    curl http://localhost:8000/status
    ```

4. Executar o multi-date scraper:

    ```bash
    curl -X POST http://localhost:8000/run/multi-date-scraper \
    -H "Content-Type: application/json" \
    -d '{"args": {"start_date": "2025-06-15", "end_date": "2025-06-17"}}'
    ```

5. Executar o scraper CLI:

    ```bash
    curl -X POST http://localhost:8000/run/scraper-cli \
    -H "Content-Type: application/json" \
    -d '{"args": {"date": "2025-06-15"}}'
    ```

6. Parar o monitoramento:

    ```bash
    curl -X POST http://localhost:8000/stop/monitor
    ```

7. Parar o multi-date scraper:

    ```bash
    curl -X POST http://localhost:8000/stop/multi_date_scraper
    ```

## 🧪 Testes

O sistema de scraper possui uma suite completa de testes unitários e de integração.

### Executar Testes

```bash
cd backend/scraper

# Instalar dependências de teste
pip install -r tests/requirements-test.txt

# Executar todos os testes
python -m pytest tests/ -v

# Testes unitários apenas
python -m pytest tests/unit/ -v

# Testes de integração apenas
python -m pytest tests/integration/ -v

# Verificar setup do sistema
python scripts/verify-scraper-setup.py
```

### Documentação Completa

Para informações detalhadas sobre a estrutura de testes, cobertura e melhorias realizadas, consulte:

📖 **[Documentação Completa dos Testes](TESTES-AUDITORIA.md)**

---
