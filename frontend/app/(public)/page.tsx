/**
 * Landing Page for Job Matching System
 * Public page with SEO optimization and performance features
 */

import { Metadata } from 'next';
import { Suspense } from 'react';
import dynamic from 'next/dynamic';

import { HeroSection } from '@/components/sections/hero-section';
import { FeaturesSection } from '@/components/sections/features-section';
import { StatsSection } from '@/components/sections/stats-section';
import { HowItWorksSection } from '@/components/sections/how-it-works-section';
import { TestimonialsSection } from '@/components/sections/testimonials-section';
import { CTASection } from '@/components/sections/cta-section';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

// Dynamic imports for non-critical sections
const CompaniesSection = dynamic(
  () => import('@/components/sections/companies-section').then(mod => ({ default: mod.CompaniesSection })),
  {
    loading: () => <LoadingSkeleton className="h-32" />,
    ssr: false,
  }
);

const BlogPreviewSection = dynamic(
  () => import('@/components/sections/blog-preview-section').then(mod => ({ default: mod.BlogPreviewSection })),
  {
    loading: () => <LoadingSkeleton className="h-64" />,
    ssr: false,
  }
);

// Page metadata
export const metadata: Metadata = {
  title: 'AI-Powered Job Matching Platform | JobMatch Pro',
  description: 'Discover your perfect career opportunity with JobMatch Pro. Our AI-powered platform matches you with jobs based on your skills, experience, and preferences. Start your journey today.',
  keywords: [
    'job matching',
    'AI recruitment',
    'career opportunities',
    'job search platform',
    'personalized job recommendations',
    'talent matching',
    'career development',
  ],
  openGraph: {
    title: 'AI-Powered Job Matching Platform | JobMatch Pro',
    description: 'Discover your perfect career opportunity with JobMatch Pro. Our AI-powered platform matches you with jobs based on your skills, experience, and preferences.',
    url: 'https://jobmatch.pro',
    siteName: 'JobMatch Pro',
    images: [
      {
        url: '/images/landing/og-hero.jpg',
        width: 1200,
        height: 630,
        alt: 'JobMatch Pro - Find Your Perfect Job Match',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AI-Powered Job Matching Platform | JobMatch Pro',
    description: 'Discover your perfect career opportunity with JobMatch Pro.',
    creator: '@jobmatchpro',
    images: ['/images/landing/twitter-hero.jpg'],
  },
  alternates: {
    canonical: 'https://jobmatch.pro',
  },
};

// JSON-LD structured data
const structuredData = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'JobMatch Pro',
  url: 'https://jobmatch.pro',
  logo: 'https://jobmatch.pro/images/logo.png',
  description: 'AI-powered job matching platform connecting talent with opportunities',
  foundingDate: '2024',
  contactPoint: {
    '@type': 'ContactPoint',
    telephone: '+1-555-0123',
    contactType: 'customer service',
    email: 'support@jobmatch.pro',
  },
  sameAs: [
    'https://twitter.com/jobmatchpro',
    'https://linkedin.com/company/jobmatchpro',
    'https://facebook.com/jobmatchpro',
  ],
  service: {
    '@type': 'Service',
    name: 'AI Job Matching',
    description: 'Advanced AI algorithms match candidates with perfect job opportunities',
    provider: {
      '@type': 'Organization',
      name: 'JobMatch Pro',
    },
  },
};

export default function LandingPage() {
  return (
    <>
      {/* Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(structuredData),
        }}
      />

      {/* Page Content */}
      <div className="flex flex-col">
        {/* Hero Section - Above the fold */}
        <section className="relative">
          <HeroSection />
        </section>

        {/* Stats Section - Critical for trust */}
        <section className="py-12 bg-muted/50">
          <Suspense fallback={<LoadingSkeleton className="h-32" />}>
            <StatsSection />
          </Suspense>
        </section>

        {/* Features Section - Core value proposition */}
        <section className="py-16">
          <Suspense fallback={<LoadingSkeleton className="h-96" />}>
            <FeaturesSection />
          </Suspense>
        </section>

        {/* How It Works Section */}
        <section className="py-16 bg-muted/30">
          <Suspense fallback={<LoadingSkeleton className="h-64" />}>
            <HowItWorksSection />
          </Suspense>
        </section>

        {/* Companies Section - Social proof */}
        <section className="py-12">
          <CompaniesSection />
        </section>

        {/* Testimonials Section - Social proof */}
        <section className="py-16 bg-muted/50">
          <Suspense fallback={<LoadingSkeleton className="h-64" />}>
            <TestimonialsSection />
          </Suspense>
        </section>

        {/* Blog Preview Section - Content marketing */}
        <section className="py-16">
          <BlogPreviewSection />
        </section>

        {/* CTA Section - Conversion */}
        <section className="py-16 bg-primary text-primary-foreground">
          <Suspense fallback={<LoadingSkeleton className="h-32" />}>
            <CTASection />
          </Suspense>
        </section>
      </div>
    </>
  );
}

// Enable static generation with ISR
export const revalidate = 3600; // Revalidate every hour