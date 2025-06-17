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

4. Parar o monitoramento:

    ```bash
    curl -X POST http://localhost:8000/stop/monitor
    ```
