import { z } from 'zod'

const envSchema = z.object({
  API_CONTAINER_NAME: z.string().default('juscash-api'),
  API_HOST_PORT: z.string().transform(Number).default('8000'),
  API_PORT: z.string().transform(Number).default('8000'),
  DATABASE_URL: z.string().default('postgresql://localhost:5432/juscash_db'),
  CORS_ORIGIN: z.string().default('http://localhost:3000'),
  JWT_ACCESS_SECRET: z.string().default('dev-access-secret-key'),
  JWT_REFRESH_SECRET: z.string().default('dev-refresh-secret-key'),
  RATE_LIMIT_WINDOW_MS: z.string().transform(Number).default('900000'),
  RATE_LIMIT_MAX_REQUESTS: z.string().transform(Number).default('100'),
  MAX_REQUEST_SIZE: z.string().default('10mb'),
  ENABLE_SECURITY_MIDDLEWARE: z.string().transform((val) => val === 'true').default('true'),
  ENABLE_METRICS: z.string().transform((val) => val !== 'false').default('false'),
  METRICS_PATH: z.string().default('/admin/metrics'),
  LOG_LEVEL: z.string().default('info'),
  ENABLE_FILE_LOGGING: z.string().transform((val) => val !== 'false').default('true'),
  REDIS_URL: z.string().default('redis://localhost:6379'),
  SCRAPER_API_KEY: z.string().default('dev-scraper-api-key')
})

let env: z.infer<typeof envSchema>

try {
  env = envSchema.parse(process.env)
} catch (error) {
  console.error('❌ Erro na validação das variáveis de ambiente:')
  if (error instanceof z.ZodError) {
    error.errors.forEach((err) => {
      console.error(`  - ${err.path.join('.')}: ${err.message}`)
    })
  }
  console.error('💡 Dica: Crie um arquivo .env baseado no .env.example')
  process.exit(1)
}

export const config = {
  containerName: env.API_CONTAINER_NAME,
  hostPort: env.API_HOST_PORT,
  port: env.API_PORT,
  database: {
    url: env.DATABASE_URL,
  },
  jwt: {
    accessTokenSecret: env.JWT_ACCESS_SECRET,
    refreshTokenSecret: env.JWT_REFRESH_SECRET,
  },
  scraper: {
    apiKey: env.SCRAPER_API_KEY,
  },
  cors: {
    origin: env.CORS_ORIGIN,
  },
  rateLimit: {
    windowMs: env.RATE_LIMIT_WINDOW_MS,
    maxRequests: env.RATE_LIMIT_MAX_REQUESTS,
  },
  security: {
    maxRequestSize: env.MAX_REQUEST_SIZE,
    enableSecurityMiddleware: env.ENABLE_SECURITY_MIDDLEWARE,
  },
  monitoring: {
    enableMetrics: env.ENABLE_METRICS,
    metricsPath: env.METRICS_PATH,
  },
  logging: {
    level: env.LOG_LEVEL,
    enableFileLogging: env.ENABLE_FILE_LOGGING,
  },
  redis: {
    url: env.REDIS_URL,
  },
}

// Environment validation is now handled by Zod schema above
// For production, make sure to set proper values for:
// - DATABASE_URL
// - JWT_ACCESS_SECRET
// - JWT_REFRESH_SECRET
// - SCRAPER_API_KEY

export default config
