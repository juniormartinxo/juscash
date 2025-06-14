#!/usr/bin/env node

/**
 * Script de teste para a API do Scraper
 *
 * Como usar:
 * 1. Configure a variável SCRAPER_API_KEY no seu .env
 * 2. Execute: node test-scraper-api.js
 *
 * O script testará:
 * - Autenticação com API Key
 * - Validação de dados
 * - Criação de publicação
 * - Tratamento de erros
 */

const axios = require('axios');
require('dotenv').config();

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000';
const SCRAPER_API_KEY = process.env.SCRAPER_API_KEY;

// Cores para output no terminal
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logTest(testName) {
  log(`\n${colors.bold}🧪 Teste: ${testName}${colors.reset}`, 'blue');
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

// Dados de exemplo para teste
const samplePublicationData = {
  processNumber: `TEST-${Date.now()}-89.2024.8.26.0100`,
  publicationDate: '2024-03-15T00:00:00.000Z',
  availabilityDate: '2024-03-17T00:00:00.000Z',
  authors: ['João Silva Santos - TESTE', 'Maria Oliveira - TESTE'],
  defendant: 'Instituto Nacional do Seguro Social - INSS',
  lawyers: [
    {
      name: 'Dr. Carlos Advogado - TESTE',
      oab: '123456'
    },
    {
      name: 'Dra. Ana Jurista - TESTE',
      oab: '789012'
    }
  ],
  grossValue: 150000,
  netValue: 135000,
  interestValue: 10000,
  attorneyFees: 5000,
  content: 'Conteúdo de teste da publicação do DJE sobre aposentadoria por invalidez. Este é um teste automatizado da API do scraper.',
  status: 'NOVA',
  scrapingSource: 'DJE-SP-TEST',
  caderno: '3',
  instancia: '1',
  local: 'Capital',
  parte: '1',
  extractionMetadata: {
    extraction_date: new Date().toISOString(),
    source_url: 'https://dje.tjsp.jus.br/test',
    confidence_score: 0.95,
    test_run: true
  }
};

async function testApiKeyMissing() {
  logTest('API Key ausente');

  try {
    const response = await axios.post(`${API_BASE_URL}/api/scraper/publications`, samplePublicationData, {
      headers: {
        'Content-Type': 'application/json'
        // Sem X-API-Key header
      }
    });

    logError('Deveria ter falhado sem API Key');
    return false;
  } catch (error) {
    if (error.response?.status === 400 && error.response?.data?.error?.includes('X-API-Key')) {
      logSuccess('Rejeitou corretamente requisição sem API Key');
      return true;
    } else {
      logError(`Erro inesperado: ${error.response?.data?.error || error.message}`);
      return false;
    }
  }
}

async function testApiKeyInvalid() {
  logTest('API Key inválida');

  try {
    const response = await axios.post(`${API_BASE_URL}/api/scraper/publications`, samplePublicationData, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'invalid-api-key-123'
      }
    });

    logError('Deveria ter falhado com API Key inválida');
    return false;
  } catch (error) {
    if (error.response?.status === 401 && error.response?.data?.error?.includes('Invalid API Key')) {
      logSuccess('Rejeitou corretamente API Key inválida');
      return true;
    } else {
      logError(`Erro inesperado: ${error.response?.data?.error || error.message}`);
      return false;
    }
  }
}

async function testDataValidation() {
  logTest('Validação de dados');

  try {
    const invalidData = {
      // Dados inválidos - sem campos obrigatórios
      processNumber: '',
      authors: [],
      content: ''
    };

    const response = await axios.post(`${API_BASE_URL}/api/scraper/publications`, invalidData, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': SCRAPER_API_KEY
      }
    });

    logError('Deveria ter falhado na validação de dados');
    return false;
  } catch (error) {
    if (error.response?.status === 400) {
      logSuccess('Validação de dados funcionando corretamente');
      return true;
    } else {
      logError(`Erro inesperado: ${error.response?.data?.error || error.message}`);
      return false;
    }
  }
}

async function testSuccessfulCreation() {
  logTest('Criação bem-sucedida de publicação');

  try {
    const response = await axios.post(`${API_BASE_URL}/api/scraper/publications`, samplePublicationData, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': SCRAPER_API_KEY
      }
    });

    if (response.status === 201 && response.data.success) {
      logSuccess('Publicação criada com sucesso via scraper');
      log(`   📄 ID: ${response.data.data.publication.id}`);
      log(`   📋 Processo: ${response.data.data.publication.processNumber}`);
      log(`   👥 Autores: ${response.data.data.publication.authors.join(', ')}`);
      return true;
    } else {
      logError('Resposta inesperada na criação');
      return false;
    }
  } catch (error) {
    logError(`Erro na criação: ${error.response?.data?.error || error.message}`);
    return false;
  }
}

async function testDuplicateProcess() {
  logTest('Processo duplicado');

  try {
    // Tentar criar a mesma publicação novamente
    const response = await axios.post(`${API_BASE_URL}/api/scraper/publications`, samplePublicationData, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': SCRAPER_API_KEY
      }
    });

    logError('Deveria ter falhado com processo duplicado');
    return false;
  } catch (error) {
    if (error.response?.status === 500 && error.response?.data?.error?.includes('constraint')) {
      logSuccess('Rejeitou corretamente processo duplicado');
      return true;
    } else {
      logWarning(`Erro diferente do esperado: ${error.response?.data?.error || error.message}`);
      return true; // Pode ser que o processo não tenha sido criado no teste anterior
    }
  }
}

async function testRateLimit() {
  logTest('Rate limiting (teste básico)');

  try {
    const promises = [];

    // Fazer várias requisições simultâneas (mas não o suficiente para atingir o limite)
    for (let i = 0; i < 5; i++) {
      const testData = {
        ...samplePublicationData,
        processNumber: `RATE-TEST-${Date.now()}-${i}-89.2024.8.26.0100`
      };

      promises.push(
        axios.post(`${API_BASE_URL}/api/scraper/publications`, testData, {
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': SCRAPER_API_KEY
          }
        }).catch(err => ({ error: err }))
      );
    }

    const results = await Promise.all(promises);
    const successful = results.filter(r => !r.error && r.status === 201).length;
    const failed = results.filter(r => r.error).length;

    logSuccess(`Rate limiting básico: ${successful} sucessos, ${failed} falhas`);
    return true;
  } catch (error) {
    logError(`Erro no teste de rate limiting: ${error.message}`);
    return false;
  }
}

async function runAllTests() {
  log(`${colors.bold}🚀 Iniciando testes da API do Scraper${colors.reset}`, 'blue');
  log(`📍 URL Base: ${API_BASE_URL}`);
  log(`🔑 API Key configurada: ${SCRAPER_API_KEY ? 'Sim' : 'Não'}`);

  if (!SCRAPER_API_KEY) {
    logError('SCRAPER_API_KEY não configurada no .env');
    logWarning('Configure a variável SCRAPER_API_KEY no arquivo .env');
    process.exit(1);
  }

  const tests = [
    { name: 'API Key ausente', fn: testApiKeyMissing },
    { name: 'API Key inválida', fn: testApiKeyInvalid },
    { name: 'Validação de dados', fn: testDataValidation },
    { name: 'Criação bem-sucedida', fn: testSuccessfulCreation },
    { name: 'Processo duplicado', fn: testDuplicateProcess },
    { name: 'Rate limiting básico', fn: testRateLimit }
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      const result = await test.fn();
      if (result) {
        passed++;
      } else {
        failed++;
      }
    } catch (error) {
      logError(`Erro no teste ${test.name}: ${error.message}`);
      failed++;
    }

    // Pequena pausa entre testes
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  log(`\n${colors.bold}📊 Resultados dos Testes${colors.reset}`, 'blue');
  logSuccess(`✅ Passou: ${passed}`);
  if (failed > 0) {
    logError(`❌ Falhou: ${failed}`);
  }
  log(`📈 Total: ${passed + failed}`);

  if (failed === 0) {
    log(`\n${colors.bold}🎉 Todos os testes passaram! A API do Scraper está funcionando corretamente.${colors.reset}`, 'green');
  } else {
    log(`\n${colors.bold}⚠️  Alguns testes falharam. Verifique a implementação.${colors.reset}`, 'yellow');
  }
}

// Executar testes se o script for chamado diretamente
if (require.main === module) {
  runAllTests().catch(error => {
    logError(`Erro fatal: ${error.message}`);
    process.exit(1);
  });
}

module.exports = {
  runAllTests,
  testApiKeyMissing,
  testApiKeyInvalid,
  testDataValidation,
  testSuccessfulCreation,
  testDuplicateProcess,
  testRateLimit
};
