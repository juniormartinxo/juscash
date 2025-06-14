import { z } from 'zod'

const envSchema = z.object({
  API_PORT: z.string().transform(Number),
  DATABASE_URL: z.string(),
  CORS_ORIGIN: z.string(),
  JWT_ACCESS_SECRET: z.string(),
  JWT_REFRESH_SECRET: z.string(),
  RATE_LIMIT_WINDOW_MS: z.string().transform(Number),
  RATE_LIMIT_MAX_REQUESTS: z.string().transform(Number),
  MAX_REQUEST_SIZE: z.string(),
  ENABLE_SECURITY_MIDDLEWARE: z.string().transform((val) => val === 'true'),
  ENABLE_METRICS: z.string().transform((val) => val !== 'false'),
  METRICS_PATH: z.string(),
  LOG_LEVEL: z.string(),
  ENABLE_FILE_LOGGING: z.string().transform((val) => val !== 'false'),
  REDIS_URL: z.string(),
  SCRAPER_API_KEY: z.string(),
  MAIL_PORT: z.string().transform(Number),
  MAIL_SECURE: z.string().transform((val) => val === 'true'),
  MAIL_BOX_CONTACT: z.string().email(),
  MAIL_BOX_BILLING: z.string().email(),
  MAIL_USER: z.string(),
  MAIL_PASS: z.string(),
  MAIL_HOST: z.string()
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
  apiPort: env.API_PORT,
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
  mail: {
    port: env.MAIL_PORT,
    secure: env.MAIL_SECURE,
    user: env.MAIL_USER,
    pass: env.MAIL_PASS,
    host: env.MAIL_HOST,
    boxContact: env.MAIL_BOX_CONTACT,
    boxBilling: env.MAIL_BOX_BILLING,
  }
}

// Environment validation is now handled by Zod schema above
// For production, make sure to set proper values for:
// - DATABASE_URL
// - JWT_ACCESS_SECRET
// - JWT_REFRESH_SECRET
// - SCRAPER_API_KEY

export default config
