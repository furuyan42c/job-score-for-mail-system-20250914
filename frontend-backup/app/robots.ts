/**
 * Robots.txt Generation
 * Controls search engine crawling behavior
 */

import { MetadataRoute } from 'next';

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://jobmatch.pro';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: [
          '/',
          '/jobs',
          '/jobs/*',
          '/companies',
          '/companies/*',
          '/about',
          '/contact',
          '/privacy',
          '/terms',
        ],
        disallow: [
          '/dashboard',
          '/dashboard/*',
          '/profile',
          '/profile/*',
          '/admin',
          '/admin/*',
          '/api',
          '/api/*',
          '/auth',
          '/auth/*',
          '/_next',
          '/_next/*',
          '/static',
          '/static/*',
          '/*.json',
          '/*?*utm_*',
          '/*?*fbclid*',
          '/*?*gclid*',
        ],
        crawlDelay: 1,
      },
      {
        userAgent: 'Googlebot',
        allow: [
          '/',
          '/jobs',
          '/jobs/*',
          '/companies',
          '/companies/*',
          '/about',
          '/contact',
          '/privacy',
          '/terms',
        ],
        disallow: [
          '/dashboard',
          '/dashboard/*',
          '/profile',
          '/profile/*',
          '/admin',
          '/admin/*',
          '/api',
          '/api/*',
          '/auth',
          '/auth/*',
        ],
        crawlDelay: 0.5,
      },
      {
        userAgent: 'Bingbot',
        allow: [
          '/',
          '/jobs',
          '/jobs/*',
          '/companies',
          '/companies/*',
          '/about',
          '/contact',
          '/privacy',
          '/terms',
        ],
        disallow: [
          '/dashboard',
          '/dashboard/*',
          '/profile',
          '/profile/*',
          '/admin',
          '/admin/*',
          '/api',
          '/api/*',
          '/auth',
          '/auth/*',
        ],
        crawlDelay: 1,
      },
      {
        userAgent: 'facebookexternalhit',
        allow: [
          '/',
          '/jobs/*',
          '/companies/*',
          '/about',
          '/contact',
        ],
        disallow: [
          '/dashboard',
          '/profile',
          '/admin',
          '/api',
          '/auth',
        ],
      },
      {
        userAgent: 'Twitterbot',
        allow: [
          '/',
          '/jobs/*',
          '/companies/*',
          '/about',
          '/contact',
        ],
        disallow: [
          '/dashboard',
          '/profile',
          '/admin',
          '/api',
          '/auth',
        ],
      },
      {
        userAgent: 'LinkedInBot',
        allow: [
          '/',
          '/jobs/*',
          '/companies/*',
          '/about',
          '/contact',
        ],
        disallow: [
          '/dashboard',
          '/profile',
          '/admin',
          '/api',
          '/auth',
        ],
      },
      // Block bad bots
      {
        userAgent: [
          'AhrefsBot',
          'SemrushBot',
          'MJ12bot',
          'DotBot',
          'AspiegelBot',
          'SurveyBot',
          'CCBot',
          'GPTBot',
          'ChatGPT-User',
          'CCBot',
          'anthropic-ai',
          'Claude-Web',
        ],
        disallow: '/',
      },
    ],
    sitemap: [
      `${baseUrl}/sitemap.xml`,
      `${baseUrl}/en/sitemap.xml`,
      `${baseUrl}/ja/sitemap.xml`,
      `${baseUrl}/es/sitemap.xml`,
      `${baseUrl}/fr/sitemap.xml`,
      `${baseUrl}/de/sitemap.xml`,
    ],
    host: baseUrl,
  };
}