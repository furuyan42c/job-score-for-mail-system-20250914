/**
 * Sitemap Generation for SEO
 * Automatically generates sitemap.xml for search engines
 */

import { MetadataRoute } from 'next';
import { getJobs } from '@/lib/api/jobs';
import { getCompanies } from '@/lib/api/companies';
import { locales, defaultLocale } from '@/lib/i18n/config';

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://jobmatch.pro';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const sitemapEntries: MetadataRoute.Sitemap = [];

  // Static pages
  const staticPages = [
    '/',
    '/jobs',
    '/companies',
    '/about',
    '/contact',
    '/privacy',
    '/terms',
  ];

  // Add static pages for each locale
  for (const locale of locales) {
    for (const page of staticPages) {
      const url = locale === defaultLocale
        ? `${baseUrl}${page}`
        : `${baseUrl}/${locale}${page}`;

      sitemapEntries.push({
        url,
        lastModified: new Date(),
        changeFrequency: page === '/' ? 'daily' : 'weekly',
        priority: page === '/' ? 1 : 0.8,
        alternates: {
          languages: Object.fromEntries(
            locales.map(l => [
              l,
              l === defaultLocale
                ? `${baseUrl}${page}`
                : `${baseUrl}/${l}${page}`
            ])
          ),
        },
      });
    }
  }

  try {
    // Fetch dynamic content
    const [jobsData, companiesData] = await Promise.all([
      getJobs({ page: 1, pageSize: 1000, status: 'published' }),
      getCompanies({ page: 1, pageSize: 1000, status: 'active' }),
    ]);

    // Add job pages
    for (const job of jobsData.jobs) {
      for (const locale of locales) {
        const url = locale === defaultLocale
          ? `${baseUrl}/jobs/${job.id}`
          : `${baseUrl}/${locale}/jobs/${job.id}`;

        sitemapEntries.push({
          url,
          lastModified: new Date(job.updatedAt || job.createdAt),
          changeFrequency: 'weekly',
          priority: 0.7,
          alternates: {
            languages: Object.fromEntries(
              locales.map(l => [
                l,
                l === defaultLocale
                  ? `${baseUrl}/jobs/${job.id}`
                  : `${baseUrl}/${l}/jobs/${job.id}`
              ])
            ),
          },
        });
      }
    }

    // Add company pages
    for (const company of companiesData.companies) {
      for (const locale of locales) {
        const url = locale === defaultLocale
          ? `${baseUrl}/companies/${company.id}`
          : `${baseUrl}/${locale}/companies/${company.id}`;

        sitemapEntries.push({
          url,
          lastModified: new Date(company.updatedAt || company.createdAt),
          changeFrequency: 'monthly',
          priority: 0.6,
          alternates: {
            languages: Object.fromEntries(
              locales.map(l => [
                l,
                l === defaultLocale
                  ? `${baseUrl}/companies/${company.id}`
                  : `${baseUrl}/${l}/companies/${company.id}`
              ])
            ),
          },
        });
      }
    }

    // Add category pages
    const categories = [
      'technology',
      'marketing',
      'sales',
      'design',
      'finance',
      'operations',
      'customer-service',
      'human-resources',
    ];

    for (const category of categories) {
      for (const locale of locales) {
        const url = locale === defaultLocale
          ? `${baseUrl}/jobs?category=${category}`
          : `${baseUrl}/${locale}/jobs?category=${category}`;

        sitemapEntries.push({
          url,
          lastModified: new Date(),
          changeFrequency: 'daily',
          priority: 0.5,
          alternates: {
            languages: Object.fromEntries(
              locales.map(l => [
                l,
                l === defaultLocale
                  ? `${baseUrl}/jobs?category=${category}`
                  : `${baseUrl}/${l}/jobs?category=${category}`
              ])
            ),
          },
        });
      }
    }

    // Add location pages
    const locations = [
      'new-york',
      'san-francisco',
      'london',
      'tokyo',
      'berlin',
      'paris',
      'remote',
    ];

    for (const location of locations) {
      for (const locale of locales) {
        const url = locale === defaultLocale
          ? `${baseUrl}/jobs?location=${location}`
          : `${baseUrl}/${locale}/jobs?location=${location}`;

        sitemapEntries.push({
          url,
          lastModified: new Date(),
          changeFrequency: 'daily',
          priority: 0.5,
          alternates: {
            languages: Object.fromEntries(
              locales.map(l => [
                l,
                l === defaultLocale
                  ? `${baseUrl}/jobs?location=${location}`
                  : `${baseUrl}/${l}/jobs?location=${location}`
              ])
            ),
          },
        });
      }
    }

  } catch (error) {
    console.error('Error generating sitemap:', error);
    // Continue with static pages only
  }

  return sitemapEntries;
}

// Revalidate sitemap every 24 hours
export const revalidate = 86400;