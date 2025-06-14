#!/bin/bash

# Script de otimização de performance para DJE Scraper

set -e

echo "⚡ Otimização de Performance - DJE Scraper"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar se é root para algumas otimizações
if [[ $EUID -eq 0 ]]; then
    IS_ROOT=true
    log_info "Executando como root - todas as otimizações serão aplicadas"
else
    IS_ROOT=false
    log_warning "Não é root - algumas otimizações serão puladas"
fi

# Otimizações de sistema (requer root)
if [ "$IS_ROOT" = true ]; then
    log_info "Aplicando otimizações de sistema..."
    
    # Otimizações de TCP
    cat >> /etc/sysctl.conf << EOF

# DJE Scraper TCP optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 10
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_congestion_control = bbr

# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF
    
    sysctl -p
    log_success "Otimizações de TCP aplicadas"
    
    # Otimizações de limites de arquivo
    cat >> /etc/security/limits.conf << EOF

# DJE Scraper file limits
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
EOF
    
    log_success "Limites de arquivo otimizados"
    
else
    log_warning "Otimizações de sistema puladas (requer root)"
fi

# Otimizações específicas do Python
log_info "Configurando otimizações Python..."

# Criar script de otimização Python
cat > optimize_python.py << 'EOF'
import sys
import os

# Configurações de otimização
optimizations = {
    'PYTHONOPTIMIZE': '2',  # Otimizações máximas
    'PYTHONDONTWRITEBYTECODE': '1',  # Não gerar .pyc
    'PYTHONHASHSEED': '0',  # Hash seed determinístico
    'PYTHONIOENCODING': 'utf-8',  # Encoding padrão
    'PYTHONUTF8': '1',  # UTF-8 mode
}

print("🐍 Configurações Python recomendadas:")
for key, value in optimizations.items():
    print(f"export {key}={value}")

# Verificar se playwright está otimizado
try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright disponível")
except ImportError:
    print("❌ Playwright não instalado")

# Verificar se httpx está com HTTP/2
try:
    import httpx
    print("✅ HTTPX disponível")
except ImportError:
    print("❌ HTTPX não instalado")
EOF

python3 optimize_python.py > python_env.sh
chmod +x python_env.sh

log_success "Configurações Python criadas em python_env.sh"

# Otimizações específicas do Playwright
log_info "Configurando otimizações Playwright..."

# Configurações de browser
cat > browser_optimization.py << 'EOF'
# Configurações otimizadas para Playwright em produção

OPTIMIZED_LAUNCH_OPTIONS = {
    'headless': True,
    'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-breakpad',
        '--disable-client-side-phishing-detection',
        '--disable-component-extensions-with-background-pages',
        '--disable-default-apps',
        '--disable-extensions',
        '--disable-features=TranslateUI',
        '--disable-hang-monitor',
        '--disable-ipc-flooding-protection',
        '--disable-popup-blocking',
        '--disable-prompt-on-repost',
        '--disable-renderer-backgrounding',
        '--disable-sync',
        '--force-color-profile=srgb',
        '--metrics-recording-only',
        '--no-default-browser-check',
        '--no-first-run',
        '--password-store=basic',
        '--use-mock-keychain',
        '--memory-pressure-off',
        '--max_old_space_size=4096',
    ]
}

OPTIMIZED_PAGE_OPTIONS = {
    'viewport': {'width': 1280, 'height': 720},
    'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'java_script_enabled': True,
    'bypass_csp': True,
}

print("🌐 Configurações de browser otimizadas criadas")
EOF

python3 browser_optimization.py
log_success "Configurações de browser otimizadas"

# Otimizações de configuração do scraper
log_info "Ajustando configuração do scraper..."

if [ -f ".env" ]; then
    # Backup da configuração atual
    cp .env .env.backup
    
    # Aplicar otimizações
    cat >> .env << EOF

# Performance optimizations
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY=5
SCRAPER_DELAY_BETWEEN_PAGES=2
SCRAPER_DELAY_BETWEEN_REQUESTS=1
SCRAPER_MAX_CONCURRENT_PAGES=1
API_TIMEOUT=30

# Memory optimizations
LOG_LEVEL=INFO
LOG_MAX_SIZE_MB=20
BACKUP_COMPRESS=true

# Cache optimizations
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
EOF
    
    log_success "Configurações de performance aplicadas ao .env"
else
    log_warning "Arquivo .env não encontrado - otimizações puladas"
fi

# Script de monitoramento de performance
log_info "Criando script de monitoramento..."

cat > monitor_performance.py << 'EOF'
#!/usr/bin/env python3
"""
Monitor de performance em tempo real para DJE Scraper
"""

import psutil
import time
import sys
from datetime import datetime

def monitor_resources():
    """Monitora recursos do sistema"""
    try:
        while True:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('.')
            
            # Rede
            net = psutil.net_io_counters()
            
            # Processos Python
            python_procs = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']) 
                           if 'python' in p.info['name'].lower()]
            
            # Output
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\r[{timestamp}] CPU: {cpu_percent:5.1f}% | "
                  f"MEM: {memory.percent:5.1f}% | "
                  f"DISK: {(disk.used/disk.total)*100:5.1f}% | "
                  f"PY_PROCS: {len(python_procs)}", end='', flush=True)
            
            # Alertas
            if cpu_percent > 80:
                print(f"\n⚠️  Alto uso de CPU: {cpu_percent:.1f}%")
            if memory.percent > 85:
                print(f"\n⚠️  Alto uso de memória: {memory.percent:.1f}%")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n📊 Monitoramento finalizado")
        
        # Resumo final
        print(f"CPU final: {psutil.cpu_percent():.1f}%")
        print(f"Memória final: {psutil.virtual_memory().percent:.1f}%")
        print(f"Processos Python ativos: {len(python_procs)}")

if __name__ == '__main__':
    print("📊 Monitor de Performance - DJE Scraper")
    print("Pressione Ctrl+C para parar")
    print("-" * 50)
    monitor_resources()
EOF

chmod +x monitor_performance.py
log_success "Monitor de performance criado"

# Script de limpeza de cache
log_info "Criando script de limpeza..."

cat > cleanup_cache.sh << 'EOF'
#!/bin/bash
# Script de limpeza para liberar recursos

echo "🧹 Limpando cache e arquivos temporários..."

# Limpar cache Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Limpar logs antigos
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Limpar cache do Playwright
python3 -c "
import os
import shutil
playwright_cache = os.path.expanduser('~/.cache/ms-playwright')
if os.path.exists(playwright_cache):
    size_before = sum(os.path.getsize(os.path.join(dirpath, filename))
                     for dirpath, dirnames, filenames in os.walk(playwright_cache)
                     for filename in filenames) / (1024*1024)
    print(f'Cache Playwright: {size_before:.1f}MB')
" 2>/dev/null || true

# Limpar arquivos temporários
rm -rf /tmp/dje-scraper-* 2>/dev/null || true

# Liberar memória
sync
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

echo "✅ Limpeza concluída"
EOF

chmod +x cleanup_cache.sh
log_success "Script de limpeza criado"

# Benchmark simples
log_info "Criando benchmark..."

cat > benchmark.py << 'EOF'
#!/usr/bin/env python3
"""
Benchmark simples para DJE Scraper
"""

import time
import asyncio
import sys
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

async def benchmark_basic():
    """Benchmark básico do sistema"""
    results = []
    
    print("🏃 Executando benchmark...")
    
    for i in range(5):
        start_time = time.time()
        
        # Simular carga básica
        try:
            from infrastructure.web.content_parser import DJEContentParser
            parser = DJEContentParser()
            
            # Teste de parsing
            test_content = """
            PROCESSO: 1234567-89.2024.8.26.0100
            Autor: João Silva Santos
            Réu: Instituto Nacional do Seguro Social - INSS
            Valor Principal: R$ 1.500,00
            """
            
            result = parser.parse_publication(test_content)
            
        except Exception as e:
            print(f"❌ Erro no benchmark: {e}")
            continue
        
        end_time = time.time()
        duration = end_time - start_time
        results.append(duration)
        
        print(f"   Execução {i+1}: {duration:.3f}s")
    
    if results:
        avg_time = statistics.mean(results)
        min_time = min(results)
        max_time = max(results)
        
        print(f"\n📊 Resultados do Benchmark:")
        print(f"   Tempo médio: {avg_time:.3f}s")
        print(f"   Tempo mínimo: {min_time:.3f}s")
        print(f"   Tempo máximo: {max_time:.3f}s")
        
        if avg_time < 0.1:
            print("✅ Performance excelente")
        elif avg_time < 0.5:
            print("✅ Performance boa")
        else:
            print("⚠️  Performance pode ser melhorada")
    else:
        print("❌ Nenhum resultado válido")

if __name__ == '__main__':
    asyncio.run(benchmark_basic())
EOF

chmod +x benchmark.py
log_success "Benchmark criado"

echo ""
echo "⚡ Otimização de Performance Concluída!"
echo "======================================"
echo ""
echo "📋 Arquivos criados:"
echo "   python_env.sh      - Variáveis de ambiente Python"
echo "   monitor_performance.py - Monitor em tempo real"
echo "   cleanup_cache.sh   - Script de limpeza"
echo "   benchmark.py       - Teste de performance"
echo ""
echo "🚀 Para aplicar otimizações:"
echo "   source python_env.sh"
echo "   ./cleanup_cache.sh"
echo ""
echo "📊 Para monitorar:"
echo "   ./monitor_performance.py"
echo "   ./benchmark.py"
echo ""

if [ "$IS_ROOT" = true ]; then
    echo "⚠️  Reinicie o sistema para aplicar todas as otimizações"
fi
