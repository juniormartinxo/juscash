#!/bin/bash

# Script para configurar monitoramento avançado (opcional)
# Instala Prometheus, Grafana e alerting

set -e

echo "📊 Configurando Monitoramento Avançado - DJE Scraper"
echo "===================================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar se Docker está rodando
if ! docker info >/dev/null 2>&1; then
    log_error "Docker não está rodando"
    exit 1
fi

# Criar diretório de monitoramento
mkdir -p monitoring/{prometheus,grafana,alertmanager}
cd monitoring

# Configurar Prometheus
log_info "Configurando Prometheus..."
cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'dje-scraper-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/admin/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Regras de alerta
cat > prometheus/alert_rules.yml << 'EOF'
groups:
  - name: dje_scraper_alerts
    rules:
      - alert: ScraperDown
        expr: up{job="dje-scraper-api"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "DJE Scraper API está down"
          description: "A API do DJE Scraper não está respondendo há {{ $value }} minutos."

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto uso de CPU"
          description: "CPU usage está em {{ $value }}% na instância {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto uso de memória"
          description: "Uso de memória está em {{ $value }}% na instância {{ $labels.instance }}"

      - alert: LowDiskSpace
        expr: (1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pouco espaço em disco"
          description: "Espaço em disco está em {{ $value }}% na instância {{ $labels.instance }}"
EOF

# Configurar Grafana
log_info "Configurando Grafana..."
mkdir -p grafana/provisioning/{dashboards,datasources}

cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

cat > grafana/provisioning/dashboards/dashboard.yml << 'EOF'
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Dashboard básico para DJE Scraper
cat > grafana/provisioning/dashboards/dje-scraper.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "DJE Scraper Monitoring",
    "tags": ["dje", "scraper"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"dje-scraper-api\"}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

# Configurar Alertmanager
log_info "Configurando Alertmanager..."
cat > alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@exemplo.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    email_configs:
      - to: 'admin@exemplo.com'
        subject: '[ALERTA] DJE Scraper - {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alerta: {{ .Annotations.summary }}
          Descrição: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

# Docker Compose para monitoramento
log_info "Criando Docker Compose para monitoramento..."
cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: dje-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: dje-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: dje-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: dje-node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

# Iniciar monitoramento
log_info "Iniciando serviços de monitoramento..."
docker-compose -f docker-compose.monitoring.yml up -d

# Aguardar serviços ficarem prontos
log_info "Aguardando serviços ficarem prontos..."
sleep 30

# Verificar se serviços estão rodando
if curl -s http://localhost:9090/-/healthy >/dev/null; then
    log_success "Prometheus rodando em http://localhost:9090"
else
    log_error "Prometheus não está respondendo"
fi

if curl -s http://localhost:3000/api/health >/dev/null; then
    log_success "Grafana rodando em http://localhost:3000 (admin/admin123)"
else
    log_error "Grafana não está respondendo"
fi

# Script para parar monitoramento
cat > stop-monitoring.sh << 'EOF'
#!/bin/bash
echo "🛑 Parando serviços de monitoramento..."
docker-compose -f docker-compose.monitoring.yml down
echo "✅ Serviços parados"
EOF

chmod +x stop-monitoring.sh

cd ..

log_success "Monitoramento configurado!"
echo ""
echo "📊 Serviços disponíveis:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3000 (admin/admin123)"
echo "   Alertas:    http://localhost:9093"
echo ""
echo "🔧 Comandos:"
echo "   Parar: cd monitoring && ./stop-monitoring.sh"
echo "   Logs:  cd monitoring && docker-compose -f docker-compose.monitoring.yml logs -f"
