import { PerformanceMiddleware } from '@/infrastructure/web/middleware/performance.middleware'
import { Request, Response, NextFunction } from 'express'

jest.mock('perf_hooks', () => ({
    performance: {
        now: jest.fn(),
    },
}))

describe('PerformanceMiddleware', () => {
    let middleware: PerformanceMiddleware
    let req: Partial<Request>
    let res: Partial<Response>
    let next: NextFunction

    beforeEach(() => {
        middleware = new PerformanceMiddleware()
        req = {}
        res = {
            on: jest.fn(),
            locals: {},
        }
        next = jest.fn()
        jest.clearAllMocks()
    })

    it('should_record_and_store_metrics_on_request_finish', () => {
        const { performance } = require('perf_hooks')
        const startTime = 100
        const endTime = 200
        const startCpu = { user: 10, system: 20 }
        const endCpu = { user: 15, system: 25 }
        const startMem = {
            rss: 1000,
            heapTotal: 2000,
            heapUsed: 1500,
            external: 300,
            arrayBuffers: 100,
        }
        const endMem = {
            rss: 1100,
            heapTotal: 2100,
            heapUsed: 1600,
            external: 350,
            arrayBuffers: 120,
        }

            ; (performance.now as jest.Mock)
                .mockReturnValueOnce(startTime)
                .mockReturnValueOnce(endTime)
        jest.spyOn(process, 'cpuUsage')
            .mockImplementationOnce(() => startCpu as NodeJS.CpuUsage)
            .mockImplementationOnce(() => endCpu as NodeJS.CpuUsage)
        jest.spyOn(process, 'memoryUsage')
            .mockImplementationOnce(() => startMem as NodeJS.MemoryUsage)
            .mockImplementationOnce(() => endMem as NodeJS.MemoryUsage)

        let finishHandler: Function = () => { }
        (res.on as jest.Mock).mockImplementation((event, handler) => {
            if (event === 'finish') finishHandler = handler
        })

        middleware.middleware(req as Request, res as Response, next)

        // Simulate response finish
        finishHandler()

        const metrics = middleware.getMetrics()
        expect(metrics.length).toBe(1)
        expect(metrics[0]?.responseTime).toBe(endTime - startTime)
        expect(metrics[0]?.cpuUsage).toEqual(endCpu)
        expect(metrics[0]?.memoryUsage).toEqual({
            rss: endMem.rss - startMem.rss,
            heapTotal: endMem.heapTotal - startMem.heapTotal,
            heapUsed: endMem.heapUsed - startMem.heapUsed,
            external: endMem.external - startMem.external,
            arrayBuffers: endMem.arrayBuffers - startMem.arrayBuffers,
        })
        expect(res.locals?.performanceStart).toBe(startTime)
        expect(next).toHaveBeenCalled()
    })

    it('should_return_copy_of_metrics_with_getMetrics', () => {
        // Add a metric
        const metric = {
            responseTime: 123,
            memoryUsage: {
                rss: 1, heapTotal: 2, heapUsed: 3, external: 4, arrayBuffers: 5,
            },
            cpuUsage: { user: 10, system: 20 },
        }
        // @ts-ignore
        middleware['metrics'].push(metric)
        const metricsCopy = middleware.getMetrics()
        expect(metricsCopy).toEqual([metric])
        expect(metricsCopy).not.toBe((middleware as any).metrics)
        // Mutate copy, should not affect internal
        if (metricsCopy[0]) {
            metricsCopy[0].responseTime = 999
        }
        expect((middleware as any).metrics[0].responseTime).toBe(123)
    })

    it('should_compute_average_response_time_correctly', () => {
        const mockMemoryUsage: NodeJS.MemoryUsage = {
            rss: 1, heapTotal: 2, heapUsed: 3, external: 4, arrayBuffers: 5
        }
        const mockCpuUsage: NodeJS.CpuUsage = { user: 10, system: 20 }

        // @ts-ignore
        middleware['metrics'] = [
            { responseTime: 100, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 200, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 300, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
        ]
        expect(middleware.getAverageResponseTime()).toBe(200)
    })

    it('should_discard_oldest_metrics_when_limit_exceeded', () => {
        const mockMemoryUsage: NodeJS.MemoryUsage = {
            rss: 1, heapTotal: 2, heapUsed: 3, external: 4, arrayBuffers: 5
        }
        const mockCpuUsage: NodeJS.CpuUsage = { user: 10, system: 20 }

        // @ts-ignore
        middleware['maxMetrics'] = 3
        // @ts-ignore
        middleware['metrics'] = [
            { responseTime: 1, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 2, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 3, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
        ]
        // Add one more metric, should remove the oldest
        // @ts-ignore
        middleware['storeMetrics']({ responseTime: 4, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage })
        expect(middleware.getMetrics().map(m => m.responseTime)).toEqual([2, 3, 4])
    })

    it('should_return_zero_average_when_no_metrics', () => {
        expect(middleware.getAverageResponseTime()).toBe(0)
    })

    it('should_return_empty_array_when_no_slow_requests', () => {
        const mockMemoryUsage: NodeJS.MemoryUsage = {
            rss: 1, heapTotal: 2, heapUsed: 3, external: 4, arrayBuffers: 5
        }
        const mockCpuUsage: NodeJS.CpuUsage = { user: 10, system: 20 }

        // @ts-ignore
        middleware['metrics'] = [
            { responseTime: 100, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 200, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
            { responseTime: 300, memoryUsage: mockMemoryUsage, cpuUsage: mockCpuUsage },
        ]
        expect(middleware.getSlowRequests(500)).toEqual([])
    })
})