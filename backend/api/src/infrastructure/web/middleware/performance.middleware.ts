import { Request, Response, NextFunction } from 'express'
import { performance } from 'perf_hooks'

interface PerformanceMetrics {
  responseTime: number
  memoryUsage: NodeJS.MemoryUsage
  cpuUsage: NodeJS.CpuUsage
}

export class PerformanceMiddleware {
  private metrics: PerformanceMetrics[] = [];
  private readonly maxMetrics = 1000;

  middleware = (req: Request, res: Response, next: NextFunction): void => {
    const startTime = performance.now()
    const startCpuUsage = process.cpuUsage()
    const startMemoryUsage = process.memoryUsage()

    // Store metrics on response finish
    res.on('finish', () => {
      const endTime = performance.now()
      const endCpuUsage = process.cpuUsage(startCpuUsage)
      const endMemoryUsage = process.memoryUsage()

      // Calculate metrics
      const responseTime = endTime - startTime
      const memoryDiff = {
        rss: endMemoryUsage.rss - startMemoryUsage.rss,
        heapTotal: endMemoryUsage.heapTotal - startMemoryUsage.heapTotal,
        heapUsed: endMemoryUsage.heapUsed - startMemoryUsage.heapUsed,
        external: endMemoryUsage.external - startMemoryUsage.external,
        arrayBuffers: endMemoryUsage.arrayBuffers - startMemoryUsage.arrayBuffers,
      }

      // Store metrics
      this.storeMetrics({
        responseTime,
        memoryUsage: memoryDiff,
        cpuUsage: endCpuUsage,
      })
    })

    // Add performance headers (will be added by other middleware if needed)
    res.locals.performanceStart = startTime

    next()
  };

  private storeMetrics(metrics: PerformanceMetrics): void {
    this.metrics.push(metrics)

    // Keep only last N metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift()
    }
  }

  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics]
  }

  getAverageResponseTime(): number {
    if (this.metrics.length === 0) return 0

    const total = this.metrics.reduce((sum, metric) => sum + metric.responseTime, 0)
    return total / this.metrics.length
  }

  getSlowRequests(threshold: number = 1000): PerformanceMetrics[] {
    return this.metrics.filter(metric => metric.responseTime > threshold)
  }
}
