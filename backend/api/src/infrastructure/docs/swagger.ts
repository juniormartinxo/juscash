import express from 'express'
import swaggerJsdoc from 'swagger-jsdoc'
import swaggerUi from 'swagger-ui-express'

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'DJE Management API',
      version: '1.0.0',
      description: 'API para gerenciamento de publicações do Diário da Justiça Eletrônico de São Paulo',
      contact: {
        name: 'Junior Martins',
        email: 'amjr.box@gmail.com',
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT',
      },
    },
    servers: [
      {
        url: 'http://localhost:3001',
        description: 'Desenvolvimento',
      },
      {
        url: 'https://api.dje-management.com',
        description: 'Produção',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
          description: 'Token JWT obtido no endpoint de login',
        },
      },
      schemas: {
        User: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              format: 'uuid',
              description: 'ID único do usuário',
            },
            name: {
              type: 'string',
              description: 'Nome completo do usuário',
            },
            email: {
              type: 'string',
              format: 'email',
              description: 'Email do usuário',
            },
            isActive: {
              type: 'boolean',
              description: 'Status ativo do usuário',
            },
            createdAt: {
              type: 'string',
              format: 'date-time',
              description: 'Data de criação',
            },
            updatedAt: {
              type: 'string',
              format: 'date-time',
              description: 'Data de última atualização',
            },
          },
        },
        Publication: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              format: 'uuid',
              description: 'ID único da publicação',
            },
            processNumber: {
              type: 'string',
              description: 'Número do processo judicial',
              example: '1234567-89.2024.8.26.0100',
            },
            publicationDate: {
              type: 'string',
              format: 'date',
              description: 'Data de publicação',
            },
            availabilityDate: {
              type: 'string',
              format: 'date',
              description: 'Data de disponibilização no DJE',
            },
            authors: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'Lista de autores do processo',
            },
            defendant: {
              type: 'string',
              description: 'Réu do processo',
              default: 'Instituto Nacional do Seguro Social - INSS',
            },
            lawyers: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: {
                    type: 'string',
                    description: 'Nome do advogado',
                  },
                  oab: {
                    type: 'string',
                    description: 'Número da OAB',
                  },
                },
              },
            },
            grossValue: {
              type: 'integer',
              description: 'Valor bruto em centavos',
              example: 150000,
            },
            netValue: {
              type: 'integer',
              description: 'Valor líquido em centavos',
              example: 135000,
            },
            interestValue: {
              type: 'integer',
              description: 'Valor dos juros em centavos',
            },
            attorneyFees: {
              type: 'integer',
              description: 'Valor dos honorários em centavos',
            },
            content: {
              type: 'string',
              description: 'Conteúdo completo da publicação',
            },
            status: {
              type: 'string',
              enum: ['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA'],
              description: 'Status atual da publicação',
            },
            createdAt: {
              type: 'string',
              format: 'date-time',
              description: 'Data de criação',
            },
            updatedAt: {
              type: 'string',
              format: 'date-time',
              description: 'Data de última atualização',
            },
          },
        },
        RegisterRequest: {
          type: 'object',
          required: ['name', 'email', 'password'],
          properties: {
            name: {
              type: 'string',
              minLength: 2,
              description: 'Nome completo do usuário',
              example: 'João Silva Santos',
            },
            email: {
              type: 'string',
              format: 'email',
              description: 'Email válido',
              example: 'joao@exemplo.com',
            },
            password: {
              type: 'string',
              minLength: 8,
              description: 'Senha com pelo menos 8 caracteres, incluindo maiúscula, minúscula, número e caractere especial',
              example: 'MinhaSenh@123',
            },
          },
        },
        LoginRequest: {
          type: 'object',
          required: ['email', 'password'],
          properties: {
            email: {
              type: 'string',
              format: 'email',
              description: 'Email do usuário',
              example: 'joao@exemplo.com',
            },
            password: {
              type: 'string',
              description: 'Senha do usuário',
              example: 'MinhaSenh@123',
            },
          },
        },
        AuthResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              example: true,
            },
            data: {
              type: 'object',
              properties: {
                user: {
                  $ref: '#/components/schemas/User',
                },
                tokens: {
                  type: 'object',
                  properties: {
                    accessToken: {
                      type: 'string',
                      description: 'JWT token para autenticação',
                    },
                    refreshToken: {
                      type: 'string',
                      description: 'Token para renovação do access token',
                    },
                  },
                },
              },
            },
          },
        },
        PublicationsResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              example: true,
            },
            data: {
              type: 'object',
              properties: {
                publications: {
                  type: 'array',
                  items: {
                    $ref: '#/components/schemas/Publication',
                  },
                },
                pagination: {
                  type: 'object',
                  properties: {
                    current: {
                      type: 'integer',
                      description: 'Página atual',
                      example: 1,
                    },
                    total: {
                      type: 'integer',
                      description: 'Total de páginas',
                      example: 10,
                    },
                    count: {
                      type: 'integer',
                      description: 'Total de registros',
                      example: 150,
                    },
                    perPage: {
                      type: 'integer',
                      description: 'Registros por página',
                      example: 30,
                    },
                  },
                },
              },
            },
          },
        },
        UpdateStatusRequest: {
          type: 'object',
          required: ['status'],
          properties: {
            status: {
              type: 'string',
              enum: ['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA'],
              description: 'Novo status da publicação',
            },
          },
        },
        ErrorResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              example: false,
            },
            error: {
              type: 'string',
              description: 'Mensagem de erro',
            },
            details: {
              type: 'object',
              description: 'Detalhes adicionais do erro',
            },
          },
        },
        HealthResponse: {
          type: 'object',
          properties: {
            success: {
              type: 'boolean',
              example: true,
            },
            data: {
              type: 'object',
              properties: {
                status: {
                  type: 'string',
                  example: 'ok',
                },
                timestamp: {
                  type: 'string',
                  format: 'date-time',
                },
                version: {
                  type: 'string',
                  example: '1.0.0',
                },
                uptime: {
                  type: 'number',
                  description: 'Tempo de execução em segundos',
                },
                database: {
                  type: 'string',
                  enum: ['connected', 'disconnected'],
                },
              },
            },
          },
        },
      },
    },
    paths: {
      '/health': {
        get: {
          summary: 'Health check do serviço',
          description: 'Verifica se a API está funcionando corretamente',
          tags: ['Health'],
          responses: {
            200: {
              description: 'Serviço funcionando normalmente',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/HealthResponse',
                  },
                },
              },
            },
          },
        },
      },
      '/api/auth/register': {
        post: {
          summary: 'Cadastrar novo usuário',
          description: 'Cria uma nova conta de usuário com validação de senha segura',
          tags: ['Authentication'],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/RegisterRequest',
                },
              },
            },
          },
          responses: {
            201: {
              description: 'Usuário criado com sucesso',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/AuthResponse',
                  },
                },
              },
            },
            400: {
              description: 'Dados inválidos ou usuário já existe',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
          },
        },
      },
      '/api/auth/login': {
        post: {
          summary: 'Fazer login',
          description: 'Autentica o usuário e retorna tokens JWT',
          tags: ['Authentication'],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/LoginRequest',
                },
              },
            },
          },
          responses: {
            200: {
              description: 'Login realizado com sucesso',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/AuthResponse',
                  },
                },
              },
            },
            401: {
              description: 'Credenciais inválidas',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
          },
        },
      },
      '/api/publications': {
        get: {
          summary: 'Listar publicações',
          description: 'Retorna lista paginada de publicações com filtros opcionais',
          tags: ['Publications'],
          security: [
            {
              bearerAuth: [],
            },
          ],
          parameters: [
            {
              name: 'page',
              in: 'query',
              description: 'Número da página (padrão: 1)',
              schema: {
                type: 'integer',
                minimum: 1,
                default: 1,
              },
            },
            {
              name: 'limit',
              in: 'query',
              description: 'Itens por página (padrão: 30, máximo: 100)',
              schema: {
                type: 'integer',
                minimum: 1,
                maximum: 100,
                default: 30,
              },
            },
            {
              name: 'status',
              in: 'query',
              description: 'Filtrar por status',
              schema: {
                type: 'string',
                enum: ['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA'],
              },
            },
            {
              name: 'startDate',
              in: 'query',
              description: 'Data inicial (ISO 8601)',
              schema: {
                type: 'string',
                format: 'date-time',
              },
            },
            {
              name: 'endDate',
              in: 'query',
              description: 'Data final (ISO 8601)',
              schema: {
                type: 'string',
                format: 'date-time',
              },
            },
            {
              name: 'search',
              in: 'query',
              description: 'Termo de busca (processo, autor, conteúdo)',
              schema: {
                type: 'string',
              },
            },
          ],
          responses: {
            200: {
              description: 'Lista de publicações',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/PublicationsResponse',
                  },
                },
              },
            },
            401: {
              description: 'Token de autenticação inválido',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
          },
        },
      },
      '/api/publications/{id}': {
        get: {
          summary: 'Obter publicação específica',
          description: 'Retorna detalhes completos de uma publicação',
          tags: ['Publications'],
          security: [
            {
              bearerAuth: [],
            },
          ],
          parameters: [
            {
              name: 'id',
              in: 'path',
              required: true,
              description: 'ID da publicação',
              schema: {
                type: 'string',
                format: 'uuid',
              },
            },
          ],
          responses: {
            200: {
              description: 'Detalhes da publicação',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      success: {
                        type: 'boolean',
                        example: true,
                      },
                      data: {
                        $ref: '#/components/schemas/Publication',
                      },
                    },
                  },
                },
              },
            },
            404: {
              description: 'Publicação não encontrada',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
          },
        },
      },
      '/api/publications/{id}/status': {
        put: {
          summary: 'Atualizar status da publicação',
          description: 'Altera o status de uma publicação (transições do Kanban)',
          tags: ['Publications'],
          security: [
            {
              bearerAuth: [],
            },
          ],
          parameters: [
            {
              name: 'id',
              in: 'path',
              required: true,
              description: 'ID da publicação',
              schema: {
                type: 'string',
                format: 'uuid',
              },
            },
          ],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/UpdateStatusRequest',
                },
              },
            },
          },
          responses: {
            200: {
              description: 'Status atualizado com sucesso',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      success: {
                        type: 'boolean',
                        example: true,
                      },
                      data: {
                        $ref: '#/components/schemas/Publication',
                      },
                    },
                  },
                },
              },
            },
            400: {
              description: 'Transição de status inválida',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
            404: {
              description: 'Publicação não encontrada',
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/ErrorResponse',
                  },
                },
              },
            },
          },
        },
      },
    },
    tags: [
      {
        name: 'Health',
        description: 'Endpoints de saúde do sistema',
      },
      {
        name: 'Authentication',
        description: 'Endpoints de autenticação e autorização',
      },
      {
        name: 'Publications',
        description: 'Gerenciamento de publicações do DJE',
      },
    ],
  },
  apis: ['./src/infrastructure/web/routes/*.ts'],
}

const specs = swaggerJsdoc(options)

export function setupSwagger(app: express.Application): void {
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs, {
    explorer: true,
    customCss: `
      .swagger-ui .topbar { display: none; }
      .swagger-ui .info { margin: 20px 0; }
      .swagger-ui .info .title { color: #1f2937; }
    `,
    customSiteTitle: 'DJE Management API Documentation',
    customfavIcon: '/favicon.ico',
  }))

  // Endpoint para download do spec
  app.get('/swagger.json', (req: express.Request, res: express.Response) => {
    res.setHeader('Content-Type', 'application/json')
    res.send(specs)
  })
}
