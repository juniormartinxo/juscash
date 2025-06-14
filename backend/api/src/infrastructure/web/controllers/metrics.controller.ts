import { Request, Response } from 'express'
import { ApiResponseBuilder } from '@/shared/utils/api-response'
import { asyncHandler } from '@/shared/utils/async-handler'
import { MetricsCollector } from '@/infrastructure/monitoring/metrics-collector'

export class MetricsController {
  constructor(private metricsCollector: MetricsCollector) { }

  getMetrics = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const metrics = this.metricsCollector.getMetricsSummary()
    res.json(ApiResponseBuilder.success(metrics))
  });

  getSystemMetrics = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const systemMetrics = this.metricsCollector.getSystemMetrics()
    res.json(ApiResponseBuilder.success({ metrics: systemMetrics }))
  });

  getEndpointMetrics = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const endpointMetrics = this.metricsCollector.getEndpointMetrics()
    res.json(ApiResponseBuilder.success({ endpoints: endpointMetrics }))
  });
}
