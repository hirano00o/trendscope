/**
 * Runtime configuration API endpoint for dynamic environment settings
 * 
 * @description Provides runtime configuration including API URLs that can
 * be dynamically set via environment variables at container startup.
 * This solves the Next.js build-time static embedding issue for NEXT_PUBLIC_ variables.
 */

import { NextRequest, NextResponse } from 'next/server'

/**
 * Runtime configuration interface
 */
interface RuntimeConfig {
    apiUrl: string
    nodeEnv: string
    version?: string
}

/**
 * GET handler for runtime configuration
 * 
 * @description Returns runtime configuration including the backend API URL
 * that can be set via NEXT_PUBLIC_API_URL or BACKEND_API_URL environment variables.
 * Falls back to localhost:8000 for development.
 * 
 * @returns Runtime configuration object
 * 
 * @example
 * ```typescript
 * const response = await fetch('/api/config')
 * const config = await response.json()
 * console.log(config.apiUrl) // "http://trendscope-backend-service:8000"
 * ```
 */
export async function GET(request: NextRequest): Promise<NextResponse<RuntimeConfig | { error: string }>> {
    try {
        // Try multiple environment variable names for flexibility
        // Prioritize runtime environment variables over build-time variables
        const apiUrl = 
            process.env.BACKEND_API_URL ||
            process.env.API_URL ||
            process.env.NEXT_PUBLIC_API_URL ||
            "http://localhost:8000"

        const config: RuntimeConfig = {
            apiUrl,
            nodeEnv: process.env.NODE_ENV || 'development',
            version: process.env.APP_VERSION || 'unknown'
        }

        console.log('[Config API] Returning runtime configuration:', config)

        return NextResponse.json(config, {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
    } catch (error) {
        console.error('[Config API] Failed to get runtime configuration:', error)
        
        return NextResponse.json(
            { error: 'Failed to retrieve configuration' },
            { status: 500 }
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
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    })
}