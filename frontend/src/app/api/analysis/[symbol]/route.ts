/**
 * Analysis API proxy route for bridging browser requests to backend service
 * 
 * @description Serves as a server-side proxy between browser clients and 
 * the Kubernetes backend service. This resolves DNS name resolution issues
 * where browsers cannot directly access cluster-internal service names.
 */

import { NextRequest, NextResponse } from 'next/server'
import { AnalysisResponse } from '@/types/analysis'

/**
 * GET handler for comprehensive stock analysis
 * 
 * @description Proxies browser requests to the backend comprehensive analysis endpoint.
 * The backend service is accessed using cluster-internal DNS names that only work
 * within the Kubernetes cluster.
 * 
 * @param request - Incoming request from browser
 * @param params - URL parameters containing the stock symbol
 * @returns Proxied response from backend service
 * 
 * @example
 * ```typescript
 * // Browser makes request to:
 * // GET /api/analysis/AAPL
 * 
 * // This route proxies to:
 * // GET http://trendscope-backend-service:8000/api/v1/comprehensive/AAPL
 * ```
 */
export async function GET(
    request: NextRequest,
    { params }: { params: { symbol: string } }
): Promise<NextResponse<AnalysisResponse | { error: string }>> {
    try {
        const { symbol } = params

        if (!symbol || symbol.trim().length === 0) {
            console.error('[Analysis Proxy] Missing or invalid symbol')
            return NextResponse.json(
                { error: 'Stock symbol is required' },
                { status: 400 }
            )
        }

        // Get backend URL from environment variable
        const backendUrl = process.env.BACKEND_API_URL || 'http://trendscope-backend-service:8000'

        const targetUrl = `${backendUrl}/api/v1/comprehensive/${symbol.toUpperCase()}`
        
        console.log(`[Analysis Proxy] Proxying request from browser to: ${targetUrl}`)
        console.log(`[Analysis Proxy] Symbol: ${symbol}`)

        // Create AbortController for timeout handling
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 seconds

        let backendResponse: Response
        try {
            // Make request to backend service using cluster-internal DNS
            // Note: Using fetch with Node.js DNS resolution fix (NODE_OPTIONS=--dns-result-order=ipv4first)
            backendResponse = await fetch(targetUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    // Forward relevant headers from original request
                    'User-Agent': request.headers.get('user-agent') || 'Trendscope-Frontend-Proxy',
                },
                signal: controller.signal,
            })
        } finally {
            clearTimeout(timeoutId)
        }

        console.log(`[Analysis Proxy] Backend response status: ${backendResponse.status}`)

        if (!backendResponse.ok) {
            const errorText = await backendResponse.text()
            console.error(`[Analysis Proxy] Backend error: ${backendResponse.status} - ${errorText}`)
            
            return NextResponse.json(
                { 
                    error: `Backend analysis failed: ${backendResponse.status}`,
                    details: errorText
                },
                { status: backendResponse.status }
            )
        }

        // Parse and forward the response
        const analysisData = await backendResponse.json() as AnalysisResponse
        
        console.log(`[Analysis Proxy] Successfully proxied analysis for ${symbol}`)
        console.log(`[Analysis Proxy] Response success: ${analysisData.success}`)

        // Return response with appropriate headers
        return NextResponse.json(analysisData, {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                // Add CORS headers if needed for development
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                // Cache policy
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            }
        })

    } catch (error) {
        console.error('[Analysis Proxy] Request failed:', error)

        // Handle different types of errors
        let errorMessage = 'Analysis request failed'
        let statusCode = 500

        if (error instanceof Error) {
            errorMessage = error.message
            
            // Handle specific error types
            if (error.name === 'AbortError') {
                errorMessage = 'Backend request timeout'
                statusCode = 504
            } else if (error.message.includes('fetch')) {
                errorMessage = 'Unable to connect to backend service'
                statusCode = 502
            }
        }

        return NextResponse.json(
            { 
                error: errorMessage,
                timestamp: new Date().toISOString(),
                symbol: params.symbol
            },
            { status: statusCode }
        )
    }
}

/**
 * OPTIONS handler for CORS preflight
 */
export async function OPTIONS(): Promise<NextResponse> {
    return new NextResponse(null, {
        status: 200,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    })
}
