/**
 * Root layout component for Trendscope application
 * 
 * @description Provides the main layout structure with global providers,
 * metadata configuration, and consistent styling across all pages.
 * Includes TanStack Query provider for API state management.
 */

import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
    title: {
        default: "Trendscope",
        template: "%s | Trendscope"
    },
    description: "Advanced stock price trend analysis with multi-method probability predictions",
    keywords: [
        "stock analysis",
        "trend analysis", 
        "technical indicators",
        "stock predictions",
        "financial analysis",
        "machine learning"
    ],
    authors: [{ name: "Trendscope Team" }],
    creator: "Trendscope",
    openGraph: {
        type: "website",
        locale: "en_US",
        url: "https://trendscope.app",
        title: "Trendscope - Advanced Stock Trend Analysis",
        description: "Analyze stock price trends with multiple analysis methods and get probability-based predictions",
        siteName: "Trendscope",
    },
    twitter: {
        card: "summary_large_image",
        title: "Trendscope",
        description: "Advanced stock price trend analysis with multi-method probability predictions",
    },
    robots: {
        index: true,
        follow: true,
        googleBot: {
            index: true,
            follow: true,
            "max-video-preview": -1,
            "max-image-preview": "large",
            "max-snippet": -1,
        },
    },
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className} suppressHydrationWarning>
                <Providers>
                    <div className="min-h-screen bg-neutral-50">
                        <main className="relative">
                            {children}
                        </main>
                    </div>
                </Providers>
            </body>
        </html>
    )
}