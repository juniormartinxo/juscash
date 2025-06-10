# 🗄️ Integração com Banco de Dados - Scraper DJE

## 📋 Visão Geral

Esta implementação fornece uma conexão robusta e bem estruturada entre o Scraper Python e o banco de dados PostgreSQL, seguindo os princípios da **Arquitetura Hexagonal** e **Clean Code**.

## 🏗️ Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Publication   │    │  PublicationRepository (Port)  │ │
│  │    (Entity)     │    │        (Interface)             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              DatabaseService                            │ │
│  │           (Use Cases & Business Logic)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│               INFRASTRUCTURE LAYER                          │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   SQLAlchemy    │    │   PostgreSQLRepository         │ │
│  │    Models       │    │      (Adapter)                 │ │
│  │                 │    │                                 │ │
│  │ ┌─────────────┐ │    │ ┌─────────────────────────────┐ │ │
│  │ │ Publication │ │    │ │    DatabaseConfig           │ │ │
│  │ │   Model     │ │    │ │  ConnectionManager          │ │ │
│  │ └─────────────┘ │    │ └─────────────────────────────┘ │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌─────────────────────┐
                    │    PostgreSQL       │
                    │     Database        │
                    └─────────────────────┘
```

## 📁 Estrutura de Arquivos

```
src/
├── domain/
│   ├── entities/
│   │   └── publication.py          # Entidade de domínio
│   └── repositories/
│       └── publication_repository.py # Interface (Port)
├── application/
│   └── services/
│       └── database_service.py     # Serviços de aplicação
└── infrastructure/
    └── database/
        ├── config.py              # Configuração do banco
        ├── models.py              # Modelos SQLAlchemy
        ├── connection_manager.py  # Gerenciador de conexão
        └── repositories/
            └── publication_repository_impl.py # Implementação (Adapter)
```

## 🔧 Componentes Principais

### 1. **Domain Layer** - Camada de Domínio

#### **Publication Entity** (`src/domain/entities/publication.py`)
- Entidade pura de domínio sem dependências externas
- Contém toda a lógica de negócio das publicações
- Validações automáticas e regras de transição de status
- Manipulação de valores monetários (conversão real/centavos)

#### **PublicationRepository Interface** (`src/domain/repositories/publication_repository.py`)
- **Port** da Arquitetura Hexagonal
- Define contratos para persistência sem implementação
- Permite inversão de dependência

### 2. **Application Layer** - Camada de Aplicação

#### **DatabaseService** (`src/application/services/database_service.py`)
- Orquestra casos de uso de banco de dados
- Converte dados de entrada em entidades de domínio
- Usa repositórios através da interface (não implementação concreta)
- Tratamento de erros e logging

### 3. **Infrastructure Layer** - Camada de Infraestrutura

#### **Database Configuration** (`src/infrastructure/database/config.py`)
```python
# Configuração robusta com:
- Pool de conexões configurado
- Context manager para transações automáticas
- Tratamento de erros e rollback
- Teste de conectividade
```

#### **SQLAlchemy Models** (`src/infrastructure/database/models.py`)
```python
# Modelos alinhados com schema Prisma:
- Campos com tipos corretos (UUID, ARRAY, JSON)
- Índices otimizados para performance
- Enums para status e logs
- Relacionamentos configurados
```

#### **Repository Implementation** (`src/infrastructure/database/repositories/publication_repository_impl.py`)
- **Adapter** da Arquitetura Hexagonal
- Implementação concreta usando PostgreSQL/SQLAlchemy
- Conversão entre entidades de domínio e modelos de banco
- Queries otimizadas com filtros e paginação

#### **Connection Manager** (`src/infrastructure/database/connection_manager.py`)
```python
# Funcionalidades:
- Aguarda banco estar disponível (retry automático)
- Cria tabelas automaticamente
- Verifica integridade do schema
- Monitora informações do banco
```

## 🚀 Como Usar

### 1. **Configuração do Ambiente**

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Configure as variáveis (mínimo obrigatório)
DATABASE_URL=postgresql://juscash_user:juscash_password@postgres:5432/juscash_dje
```

### 2. **Inicialização do Sistema**

```python
# src/main.py
from src.infrastructure.database.connection_manager import connection_manager
from src.application.services.database_service import DatabaseService

# Inicializa banco automaticamente
connection_manager.initialize_database()

# Usa o serviço
db_service = DatabaseService()
```

### 3. **Salvando Publicações**

```python
# Dados extraídos do scraping
publication_data = {
    "process_number": "1234567-89.2025.8.26.0001",
    "availability_date": "2025-03-17",  # Ou date object
    "authors": ["João da Silva", "Maria Santos"],
    "content": "Conteúdo completo da publicação...",
    "lawyers": [
        {"name": "Dr. Pedro Advogado", "oab": "SP123456"},
        {"name": "Dra. Ana Advocacia", "oab": "SP654321"}
    ],
    "gross_value": 5000.50,  # Em reais (convertido automaticamente)
    "net_value": 4500.30,
    "interest_value": 300.20,
    "attorney_fees": 200.00
}

# Salva no banco (com validação automática de duplicatas)
try:
    publication = db_service.save_publication(publication_data)
    logger.info(f"Publicação salva: {publication.id}")
except ValueError as e:
    logger.warning(f"Publicação já existe: {e}")
```

### 4. **Buscando Publicações**

```python
# Busca por número de processo
publication = db_service.get_publication_by_process_number("1234567-89.2025.8.26.0001")

# Busca com filtros e paginação
publications = db_service.get_publications(
    limit=50,
    offset=0,
    filters={
        "status": "NOVA",
        "availability_date_from": date(2025, 3, 1),
        "search_term": "aposentadoria"
    }
)

# Conta publicações
total = db_service.count_publications(filters={"status": "NOVA"})
```

### 5. **Atualizando Status**

```python
# Atualiza status da publicação
success = db_service.update_publication_status(publication_id, "LIDA")
if success:
    logger.info("Status atualizado com sucesso")
```

## 💰 Tratamento de Valores Monetários

O sistema trata valores monetários de forma robusta:

```python
# Entrada flexível (aceita diferentes formatos)
values = {
    "gross_value": 1500.50,        # Float em reais
    "net_value": "R$ 1.200,30",    # String formatada brasileira
    "interest_value": 15000,       # Int já em centavos
    "attorney_fees": "200.75"      # String numérica
}

# Armazenamento sempre em centavos (int)
# gross_value: 150050 centavos = R$ 1.500,50

# Recuperação em reais
monetary_values = publication.get_monetary_values_in_reais()
# {"gross_value": 1500.50, "net_value": 1200.30, ...}
```

## 🔍 Validações Implementadas

### **Entidade de Domínio**
- ✅ Número do processo obrigatório e não vazio
- ✅ Pelo menos um autor válido
- ✅ Conteúdo da publicação obrigatório
- ✅ Status válido (NOVA, LIDA, PROCESSADA)
- ✅ Transições de status permitidas
- ✅ Dados de advogado (nome e OAB obrigatórios)

### **Repositório**
- ✅ Verificação de duplicatas por número de processo
- ✅ Validação de integridade referencial
- ✅ Transações atômicas (rollback automático em erro)

### **Serviço**
- ✅ Validação de campos obrigatórios antes de criar entidade
- ✅ Conversão automática de tipos de dados
- ✅ Tratamento de erros com logging detalhado

## 🧪 Testes

### **Executar Testes Unitários**
```bash
# Testes unitários (com mocks)
python -m pytest tests/test_database_integration.py -v -m "not integration"
```

### **Executar Testes de Integração**
```bash
# Requer banco de teste configurado
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/test_juscash"
python -m pytest tests/test_database_integration.py -v -m integration
```

### **Cobertura de Testes**
- ✅ Criação e validação de entidades
- ✅ Salvamento e busca de publicações
- ✅ Tratamento de duplicatas
- ✅ Conversão de valores monetários
- ✅ Filtros e paginação
- ✅ Gerenciamento de conexão
- ✅ Transições de status

## 🔒 Segurança e Performance

### **Segurança**
- Pool de conexões configurado (evita esgotamento)
- Transações atômicas (consistência de dados)
- Parametrização de queries (prevenção SQL injection)
- Sanitização de inputs na camada de domínio

### **Performance**
- Índices otimizados nas colunas mais consultadas
- Paginação em todas as consultas de listagem
- Pool de conexões para reutilização
- Lazy loading de relacionamentos

### **Monitoramento**
- Logs estruturados com níveis apropriados
- Métricas de conexão e performance
- Health checks automáticos
- Retry automático com backoff

## 🐛 Troubleshooting

### **Problemas Comuns**

#### **Erro de Conexão**
```bash
# Verifique se o PostgreSQL está rodando
docker-compose ps postgres

# Teste conectividade
python -c "from src.infrastructure.database.config import db_config; print(db_config.test_connection())"
```

#### **Erro de Schema**
```bash
# Recrie as tabelas
python -c "from src.infrastructure.database.connection_manager import connection_manager; connection_manager.create_tables()"
```

#### **Publicação Duplicada**
```python
# Erro esperado - publicação já existe
# O sistema automaticamente retorna a existente
```

#### **Valores Monetários Incorretos**
```python
# Verifique se os valores estão sendo convertidos corretamente
publication = db_service.get_publication_by_process_number("123")
print(publication.get_monetary_values_in_reais())
```

## 📈 Próximos Passos

1. **Implementar Cache Redis** para consultas frequentes
2. **Adicionar Métricas** com Prometheus
3. **Configurar Backup Automático** do banco
4. **Implementar Soft Delete** para auditoria
5. **Adicionar Testes de Carga** com pytest-benchmark

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `./logs/scraper_*.log`
2. Execute os testes para validar a instalação
3. Consulte a documentação do schema Prisma para detalhes das tabelas