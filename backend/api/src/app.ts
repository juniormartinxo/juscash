import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import dotenv from 'dotenv'

// Carregar variáveis de ambiente
dotenv.config()

const app = express()
const PORT = Number(process.env.PORT) || 8000

// Middlewares de segurança
app.use(helmet())
app.use(cors())
app.use(express.json())

// Rota de health check
app.get('/health', (_req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        service: 'JusCash API'
    })
})

// Rota básica
app.get('/', (_req, res) => {
    res.json({
        message: 'JusCash API está rodando!',
        version: '1.0.0'
    })
})

// Iniciar servidor
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Servidor JusCash API rodando na porta ${PORT}`)
    console.log(`📍 Health check: http://localhost:${PORT}/health`)
})

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Recebido SIGTERM, encerrando servidor...')
    process.exit(0)
})

process.on('SIGINT', () => {
    console.log('🛑 Recebido SIGINT, encerrando servidor...')
    process.exit(0)
})
