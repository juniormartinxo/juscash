#!/bin/bash

# Monitor script for production
echo "🔍 Monitoring DJE API System..."

API_URL="${API_URL:-http://localhost:3001}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
LOG_FILE="/var/log/dje-monitor.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_message() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    local severity="$2"

    log_message "${RED}ALERT[$severity]: $message${NC}"

    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"🚨 DJE API Alert [$severity]: $message\"}" \
            --silent
    fi
}

check_api_health() {
    local response
    local status_code

    response=$(curl -s -w "%{http_code}" "$API_URL/health" -o /tmp/health_response.json)
    status_code="${response: -3}"

    if [ "$status_code" != "200" ]; then
        send_alert "API health check failed - Status: $status_code" "HIGH"
        return 1
    fi

    # Check database connection
    local db_status
    db_status=$(jq -r '.data.database' /tmp/health_response.json 2>/dev/null)

    if [ "$db_status" != "connected" ]; then
        send_alert "Database connection failed - Status: $db_status" "CRITICAL"
        return 1
    fi

    log_message "${GREEN}✅ API health check passed${NC}"
    return 0
}

check_response_time() {
    local response_time
    response_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_URL/health")

    # Convert to milliseconds
    response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)

    if [ "$response_time_ms" -gt 2000 ]; then
        send_alert "High response time: ${response_time_ms}ms" "MEDIUM"
    elif [ "$response_time_ms" -gt 5000 ]; then
        send_alert "Critical response time: ${response_time_ms}ms" "HIGH"
    fi

    log_message "⏱️  Response time: ${response_time_ms}ms"
}

check_disk_space() {
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$disk_usage" -gt 85 ]; then
        send_alert "High disk usage: ${disk_usage}%" "MEDIUM"
    elif [ "$disk_usage" -gt 95 ]; then
        send_alert "Critical disk usage: ${disk_usage}%" "HIGH"
    fi

    log_message "💾 Disk usage: ${disk_usage}%"
}

check_memory_usage() {
    local memory_usage
    memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')

    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        send_alert "High memory usage: ${memory_usage}%" "MEDIUM"
    elif (( $(echo "$memory_usage > 95" | bc -l) )); then
        send_alert "Critical memory usage: ${memory_usage}%" "HIGH"
    fi

    log_message "🧠 Memory usage: ${memory_usage}%"
}

check_docker_containers() {
    if command -v docker &> /dev/null; then
        local unhealthy_containers
        unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "table {{.Names}}" | tail -n +2)

        if [ -n "$unhealthy_containers" ]; then
            send_alert "Unhealthy containers: $unhealthy_containers" "HIGH"
        fi

        # Check if containers are running
        local expected_containers=("dje-api" "dje-postgres" "dje-redis")
        for container in "${expected_containers[@]}"; do
            if ! docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
                send_alert "Container $container is not running" "CRITICAL"
            fi
        done
    fi
}

check_log_errors() {
    local error_count
    local log_file="/app/logs/error.log"

    if [ -f "$log_file" ]; then
        # Count errors in the last 5 minutes
        error_count=$(find "$log_file" -newermt "5 minutes ago" -exec grep -c "ERROR\|CRITICAL" {} \; 2>/dev/null | awk '{s+=$1} END {print s+0}')

        if [ "$error_count" -gt 10 ]; then
            send_alert "High error rate: $error_count errors in last 5 minutes" "MEDIUM"
        elif [ "$error_count" -gt 50 ]; then
            send_alert "Critical error rate: $error_count errors in last 5 minutes" "HIGH"
        fi

        log_message "📝 Error count (5min): $error_count"
    fi
}

main() {
    log_message "🔍 Starting system monitoring check..."

    local checks_passed=0
    local total_checks=6

    check_api_health && ((checks_passed++))
    check_response_time
    check_disk_space
    check_memory_usage
    check_docker_containers
    check_log_errors

    if [ "$checks_passed" -eq "$total_checks" ]; then
        log_message "${GREEN}✅ All critical checks passed${NC}"
    else
        log_message "${YELLOW}⚠️  Some checks failed ($checks_passed/$total_checks passed)${NC}"
    fi

    log_message "🔍 Monitoring check completed\n"
}

# Run monitoring check
main

# If running in daemon mode, repeat every 5 minutes
if [ "$1" = "--daemon" ]; then
    log_message "🔄 Running in daemon mode (checking every 5 minutes)..."
    while true; do
        sleep 300  # 5 minutes
        main
    done
fi