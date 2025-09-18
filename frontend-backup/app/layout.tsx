/**
 * Root Layout for Job Matching System
 * Next.js 14 App Router with TypeScript
 */

import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import { QueryProvider } from '@/components/providers/query-provider';
import { ToasterProvider } from '@/components/providers/toaster-provider';
import { ThemeProvider } from '@/components/providers/theme-provider';

import { cn } from '@/lib/utils';
import { AuthProvider } from '@/components/providers/auth-provider';
import { Analytics } from '@vercel/analytics/react';

import './globals.css';

// Font configurations
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

// Metadata configuration
export const metadata: Metadata = {
  title: {
    default: 'JobMatch Pro - AI-Powered Job Matching Platform',
    template: '%s | JobMatch Pro',
  },
  description: 'Find your perfect job match with our AI-powered platform. Advanced job scoring, personalized recommendations, and seamless application tracking.',
  keywords: [
    'job matching',
    'career opportunities',
    'AI recruitment',
    'job search',
    'talent acquisition',
    'personalized recommendations',
    'job scoring',
  ],
  authors: [{ name: 'JobMatch Pro Team' }],
  creator: 'JobMatch Pro',
  publisher: 'JobMatch Pro',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://jobmatch.pro',
    siteName: 'JobMatch Pro',
    title: 'JobMatch Pro - AI-Powered Job Matching Platform',
    description: 'Find your perfect job match with our AI-powered platform.',
    images: [
      {
        url: '/images/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'JobMatch Pro - AI-Powered Job Matching Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'JobMatch Pro - AI-Powered Job Matching Platform',
    description: 'Find your perfect job match with our AI-powered platform.',
    creator: '@jobmatchpro',
    images: ['/images/twitter-image.jpg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
    yandex: 'your-yandex-verification-code',
  },
  alternates: {
    canonical: 'https://jobmatch.pro',
    languages: {
      'en-US': 'https://jobmatch.pro/en',
      'ja-JP': 'https://jobmatch.pro/ja',
      'es-ES': 'https://jobmatch.pro/es',
      'fr-FR': 'https://jobmatch.pro/fr',
      'de-DE': 'https://jobmatch.pro/de',
    },
  },
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/icons/icon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/icons/icon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: '/icons/shortcut-icon.png',
  },
};

// Viewport configuration
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
  colorScheme: 'light dark',
};

// React Query configuration moved to QueryProvider

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html
      lang="en"
      className={cn(
        'min-h-screen bg-background font-sans antialiased',
        inter.variable,
        jetbrainsMono.variable
      )}
      suppressHydrationWarning
    >
      <head>
        {/* Preload critical resources */}
        <link
          rel="preload"
          href="/fonts/inter-var.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        {/* DNS prefetch for external domains */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//api.jobmatch.pro" />

        {/* Structured data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebSite',
              name: 'JobMatch Pro',
              url: 'https://jobmatch.pro',
              description: 'AI-Powered Job Matching Platform',
              potentialAction: {
                '@type': 'SearchAction',
                target: 'https://jobmatch.pro/jobs/search?q={search_term_string}',
                'query-input': 'required name=search_term_string',
              },
            }),
          }}
        />
      </head>
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          inter.className
        )}
      >
        {/* Minimal setup to resolve onClick serialization error */}
        <div id="main-content" className="relative flex min-h-screen flex-col">
          {children}
        </div>

        {/* Analytics */}
        {/* <Analytics /> */}

      </body>
    </html>
  );
}