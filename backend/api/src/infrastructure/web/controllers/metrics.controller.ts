import { Request, Response } from 'express'
import { ApiResponseBuilder } from '../../../shared/utils/ApiResponse.js'
import { asyncHandler } from '../../../shared/utils/AsyncHandler.js'
import { MetricsCollector } from '../../monitoring/metrics-collector.js'

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
