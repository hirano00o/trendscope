import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

/**
 * Root layout component for Monthly Swing Trading application
 *
 * @description Main layout wrapper that provides consistent styling and structure
 * across all pages in the monthly swing trading application.
 */

export const metadata: Metadata = {
  title: '月次スイングトレード分析',
  description: '月次スイングトレード戦略に特化した金融分析システム',
  keywords: [
    '月次スイング',
    'スイングトレード',
    '株式分析',
    'トレンド分析',
    '投資',
    '金融',
  ],
  authors: [{ name: '月次スイングトレード分析システム' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'noindex, nofollow', // Development phase - prevent indexing
  openGraph: {
    title: '月次スイングトレード分析',
    description: '月次スイングトレード戦略に特化した金融分析システム',
    type: 'website',
    locale: 'ja_JP',
  },
};

interface RootLayoutProps {
  children: React.ReactNode;
}

/**
 * Root layout component
 *
 * @param children - Child components to render within the layout
 * @returns JSX element containing the root layout structure
 *
 * @example
 * ```tsx
 * // This layout wraps all pages automatically in Next.js App Router
 * export default function Page() {
 *   return <div>Page content</div>
 * }
 * ```
 */
export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ja" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full bg-neutral-50 font-sans antialiased">
        <div className="flex min-h-full flex-col">
          {/* Navigation Header */}
          <header className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-16 items-center justify-between">
                <div className="flex items-center">
                  <h1 className="text-xl font-bold text-neutral-900">
                    月次スイング分析
                  </h1>
                  <span className="ml-2 rounded-full bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700">
                    ベータ版
                  </span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-neutral-600">
                    月次スイングトレード専用分析
                  </span>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 bg-gradient-to-br from-neutral-50 to-neutral-100">
            <Providers>{children}</Providers>
          </main>

          {/* Footer */}
          <footer className="border-t border-neutral-200 bg-white">
            <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
              <div className="text-center text-sm text-neutral-600">
                <p>月次スイングトレード分析システム</p>
                <p className="mt-1">
                  免責事項：これは教育目的のみのためです。投資助言ではありません。
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}