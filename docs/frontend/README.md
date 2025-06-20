# ⚛️ Frontend JusCash - React Application

> Interface moderna e intuitiva para gerenciamento de publicações DJE

## 🎯 Visão Geral

O frontend do JusCash é uma Single Page Application (SPA) desenvolvida em React que oferece uma interface visual tipo Kanban para gerenciar publicações do Diário da Justiça Eletrônico de São Paulo.

## 🛠️ Stack Tecnológica

- **React** 18+ - Library principal
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS
- **React Hook Form** - Gerenciamento de formulários
- **React Query/TanStack Query** - Estado do servidor
- **React Router** - Roteamento
- **Lucide React** - Ícones
- **date-fns** - Manipulação de datas

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── components/           # Componentes reutilizáveis
│   │   ├── ui/              # Componentes básicos de UI
│   │   ├── KanbanBoard.tsx  # Board principal
│   │   ├── PublicationCard.tsx
│   │   ├── PublicationModal.tsx
│   │   ├── SearchFilters.tsx
│   │   └── ...
│   ├── contexts/            # Contextos React
│   │   └── AuthContext.tsx
│   ├── hooks/               # Custom hooks
│   │   ├── usePublications.ts
│   │   └── use-toast.tsx
│   ├── pages/               # Páginas da aplicação
│   │   ├── DashboardPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── SignupPage.tsx
│   ├── services/            # Serviços e API
│   │   └── api.ts
│   ├── types/               # Definições de tipos
│   │   └── index.ts
│   ├── lib/                 # Utilitários
│   │   ├── utils.ts
│   │   └── validations.ts
│   └── assets/              # Recursos estáticos
├── public/                  # Arquivos públicos
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## 🚀 Instalação e Execução

### Desenvolvimento Local

```bash
# Navegar para o diretório
cd frontend

# Instalar dependências
npm install
# ou
pnpm install

# Iniciar servidor de desenvolvimento
npm run dev
# ou
pnpm dev

# Aplicação disponível em http://localhost:5173
```

### Build para Produção

```bash
# Build otimizado
npm run build

# Preview do build
npm run preview

# Lint do código
npm run lint

# Type checking
npm run type-check
```

## 🎨 Componentes Principais

### KanbanBoard

O componente central da aplicação que exibe as publicações em colunas organizadas por status.

**Funcionalidades:**
- Drag & drop entre colunas
- Carregamento lazy/paginado
- Filtros em tempo real
- Busca integrada

```typescript
// Uso básico
<KanbanBoard 
  publications={publications}
  onStatusChange={handleStatusChange}
  onPublicationClick={handlePublicationClick}
/>
```

### PublicationCard

Card individual de cada publicação no board.

**Props principais:**
- `publication` - Dados da publicação
- `onStatusChange` - Callback para mudança de status
- `onClick` - Callback para clique no card

### PublicationModal

Modal para visualização detalhada das publicações.

**Funcionalidades:**
- Exibição completa dos dados
- Histórico de alterações
- Ações de status
- Responsivo

### SearchFilters

Componente de filtros avançados.

**Filtros disponíveis:**
- Busca por texto
- Filtro por data
- Filtro por status
- Filtro por valor
- Filtro por número de processo

## 🔄 Gerenciamento de Estado

### Context API

**AuthContext** - Gerencia autenticação e usuário logado:

```typescript
const { user, login, logout, loading } = useAuth();
```

### Custom Hooks

**usePublications** - Gerencia estado das publicações:

```typescript
const {
  publications,
  loading,
  error,
  updateStatus,
  refetch
} = usePublications(filters);
```

### React Query

Usado para cache e sincronização do estado do servidor:

```typescript
// Exemplo de query
const { data: publications, isLoading } = useQuery({
  queryKey: ['publications', filters],
  queryFn: () => api.getPublications(filters),
  staleTime: 5 * 60 * 1000, // 5 minutos
});
```

## 🎮 Funcionalidades da Interface

### Board Kanban

#### Estados das Colunas

1. **📋 Nova Publicação** - Publicações recém-coletadas
2. **👀 Publicação Lida** - Analisadas pelo usuário
3. **📤 Enviar para Advogado** - Encaminhadas para ação
4. **✅ Concluído** - Finalizadas

#### Interações

- **Drag & Drop**: Arrastar cards entre colunas
- **Click**: Abrir modal com detalhes
- **Filtros**: Busca e filtros em tempo real
- **Paginação**: Carregamento sob demanda

### Sistema de Filtros

```typescript
interface Filters {
  search?: string;
  status?: PublicationStatus[];
  startDate?: Date;
  endDate?: Date;
  minValue?: number;
  maxValue?: number;
  processNumber?: string;
}
```

### Responsividade

- **Desktop**: Layout completo com todas as colunas
- **Tablet**: Colunas com scroll horizontal
- **Mobile**: Uma coluna por vez com navegação

## 🔐 Autenticação

### Fluxo de Login

1. **Login Page** - Formulário de autenticação
2. **JWT Storage** - Tokens salvos no localStorage
3. **Protected Routes** - Verificação automática
4. **Refresh Token** - Renovação automática

### Interceptadores de API

```typescript
// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para renovar token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken();
      return api.request(error.config);
    }
    throw error;
  }
);
```

## 🎨 Estilo e Design

### Tailwind CSS

Configuração customizada com tema do JusCash:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
        kanban: {
          nova: '#f1f5f9',
          lida: '#fef3c7', 
          enviar: '#fed7aa',
          concluido: '#dcfce7',
        }
      }
    }
  }
}
```

### Componentes de UI

Biblioteca de componentes básicos reutilizáveis:

- **Button** - Botões com variantes
- **Input** - Campos de entrada
- **Dialog** - Modais e overlays
- **Toast** - Notificações
- **Label** - Labels de formulário

## 🔧 Configurações

### Vite Config

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  }
});
```

### Variáveis de Ambiente

```bash
# .env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=JusCash
VITE_APP_VERSION=1.0.0
```

## 🧪 Testes

### Estrutura de Testes

```bash
# Executar testes
npm run test

# Coverage
npm run test:coverage

# Testes E2E (se configurado)
npm run test:e2e
```

### Exemplo de Teste

```typescript
import { render, screen } from '@testing-library/react';
import { PublicationCard } from './PublicationCard';

test('renders publication card', () => {
  const publication = {
    id: '1',
    processNumber: '1234567-89.2024.8.26.0100',
    status: 'NOVA',
    // ...outros campos
  };

  render(<PublicationCard publication={publication} />);
  
  expect(screen.getByText(publication.processNumber)).toBeInTheDocument();
});
```

## 📱 Performance

### Otimizações Implementadas

- **React.memo** - Memoização de componentes
- **useMemo/useCallback** - Memoização de valores/funções
- **Lazy Loading** - Carregamento sob demanda
- **Code Splitting** - Divisão de bundles
- **Virtual Scrolling** - Para listas grandes

### Bundle Analysis

```bash
# Analisar bundle
npm run build && npx vite-bundle-analyzer dist
```

## 🚨 Troubleshooting

Consulte o [Guia de Correções](./FIX-GUIDE.md) para problemas específicos do frontend.

### Problemas Comuns

1. **CORS Error** - Verificar configuração do backend
2. **Token Expired** - Implementar refresh automático
3. **Performance** - Otimizar re-renders

## 📚 Recursos Adicionais

- **[Guia de Correções](./FIX-GUIDE.md)** - Soluções para problemas conhecidos
- **[Componentes de UI](./COMPONENT-GUIDE.md)** - Documentação dos componentes
- **[API Documentation](../api/README.md)** - Endpoints disponíveis

---

**Desenvolvido com React e ❤️ para uma experiência de usuário excepcional** 