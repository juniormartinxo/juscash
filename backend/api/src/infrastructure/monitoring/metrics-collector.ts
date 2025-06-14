export interface SystemMetrics {
  timestamp: Date
  uptime: number
  memoryUsage: NodeJS.MemoryUsage
  cpuUsage: NodeJS.CpuUsage
  activeConnections: number
  requestCount: number
  errorCount: number
  responseTimeAvg: number
  responseTimeP95: number
  responseTimeP99: number
}

export interface EndpointMetrics {
  path: string
  method: string
  count: number
  errorCount: number
  totalResponseTime: number
  minResponseTime: number
  maxResponseTime: number
  responseTimes: number[]
}

export class MetricsCollector {
  private metrics: SystemMetrics[] = [];
  private endpointMetrics = new Map<string, EndpointMetrics>();
  private readonly maxMetricsHistory = 1440; // 24 hours of minute-by-minute data

  constructor() {
    // Collect system metrics every minute
    setInterval(() => {
      this.collectSystemMetrics()
    }, 60000)
  }

  recordRequest(
    method: string,
    path: string,
    statusCode: number,
    responseTime: number
  ): void {
    const key = `${method}:${path}`
    const endpoint = this.endpointMetrics.get(key) || {
      path,
      method,
      count: 0,
      errorCount: 0,
      totalResponseTime: 0,
      minResponseTime: Infinity,
      maxResponseTime: 0,
      responseTimes: [],
    }

    endpoint.count++
    endpoint.totalResponseTime += responseTime
    endpoint.minResponseTime = Math.min(endpoint.minResponseTime, responseTime)
    endpoint.maxResponseTime = Math.max(endpoint.maxResponseTime, responseTime)
    endpoint.responseTimes.push(responseTime)

    // Keep only last 1000 response times per endpoint
    if (endpoint.responseTimes.length > 1000) {
      endpoint.responseTimes.shift()
    }

    if (statusCode >= 400) {
      endpoint.errorCount++
    }

    this.endpointMetrics.set(key, endpoint)
  }

  private collectSystemMetrics(): void {
    const metric: SystemMetrics = {
      timestamp: new Date(),
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      cpuUsage: process.cpuUsage(),
      activeConnections: this.getActiveConnections(),
      requestCount: this.getTotalRequestCount(),
      errorCount: this.getTotalErrorCount(),
      responseTimeAvg: this.getAverageResponseTime(),
      responseTimeP95: this.getPercentile(95),
      responseTimeP99: this.getPercentile(99),
    }

    this.metrics.push(metric)

    // Keep only recent metrics
    if (this.metrics.length > this.maxMetricsHistory) {
      this.metrics.shift()
    }
  }

  private getActiveConnections(): number {
    // This would be implementation-specific
    // For now, return a placeholder
    return 0
  }

  private getTotalRequestCount(): number {
    return Array.from(this.endpointMetrics.values())
      .reduce((total, endpoint) => total + endpoint.count, 0)
  }

  private getTotalErrorCount(): number {
    return Array.from(this.endpointMetrics.values())
      .reduce((total, endpoint) => total + endpoint.errorCount, 0)
  }

  private getAverageResponseTime(): number {
    const allResponseTimes = Array.from(this.endpointMetrics.values())
      .flatMap(endpoint => endpoint.responseTimes)

    if (allResponseTimes.length === 0) return 0

    return allResponseTimes.reduce((sum, time) => sum + time, 0) / allResponseTimes.length
  }

  private getPercentile(percentile: number): number {
    const allResponseTimes = Array.from(this.endpointMetrics.values())
      .flatMap(endpoint => endpoint.responseTimes)
      .sort((a, b) => a - b)

    if (allResponseTimes.length === 0) return 0

    const index = Math.ceil((percentile / 100) * allResponseTimes.length) - 1
    return allResponseTimes[index] ?? 0
  }

  getSystemMetrics(): SystemMetrics[] {
    return [...this.metrics]
  }

  getEndpointMetrics(): EndpointMetrics[] {
    return Array.from(this.endpointMetrics.values())
  }

  getMetricsSummary(): {
    system: SystemMetrics | null
    endpoints: EndpointMetrics[]
    summary: {
      totalRequests: number
      totalErrors: number
      errorRate: number
      avgResponseTime: number
      p95ResponseTime: number
      uptime: number
    }
  } {
    const latestMetric = this.metrics[this.metrics.length - 1] || null
    const endpoints = this.getEndpointMetrics()

    const totalRequests = this.getTotalRequestCount()
    const totalErrors = this.getTotalErrorCount()

    return {
      system: latestMetric,
      endpoints,
      summary: {
        totalRequests,
        totalErrors,
        errorRate: totalRequests > 0 ? totalErrors / totalRequests : 0,
        avgResponseTime: this.getAverageResponseTime(),
        p95ResponseTime: this.getPercentile(95),
        uptime: process.uptime(),
      },
    }
  }
}