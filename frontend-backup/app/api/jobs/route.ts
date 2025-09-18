/**
 * Jobs API Route Handler
 * Handles CRUD operations for jobs
 */

import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { z } from 'zod';

import { authOptions } from '@/lib/auth';
import { jobsService } from '@/lib/services/jobs-service';
import { ApiError, handleApiError } from '@/lib/utils/api-error';
import { validateRequest } from '@/lib/utils/validation';
import { rateLimit } from '@/lib/utils/rate-limit';

// Validation schemas
const getJobsSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  query: z.string().optional(),
  location: z.string().optional(),
  category: z.string().optional(),
  experience: z.string().optional(),
  salary: z.string().optional(),
  jobType: z.string().optional(),
  remote: z.coerce.boolean().optional(),
  sort: z.enum(['relevance', 'date', 'salary', 'title']).default('relevance'),
});

const createJobSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().min(50),
  summary: z.string().max(500).optional(),
  companyId: z.string().uuid(),
  location: z.string().min(1),
  category: z.string().min(1),
  employmentType: z.enum(['full-time', 'part-time', 'contract', 'internship']),
  experienceLevel: z.enum(['entry', 'mid', 'senior', 'lead', 'executive']),
  skills: z.array(z.string()).min(1),
  requirements: z.array(z.string()).optional(),
  benefits: z.array(z.string()).optional(),
  salary: z.object({
    min: z.number().min(0),
    max: z.number().min(0),
    currency: z.string().default('USD'),
    period: z.enum(['hour', 'day', 'month', 'year']).default('year'),
  }).optional(),
  remote: z.boolean().default(false),
  urgent: z.boolean().default(false),
  workHours: z.string().optional(),
  expiresAt: z.string().datetime().optional(),
});

/**
 * GET /api/jobs
 * Fetch jobs with filtering, sorting, and pagination
 */
export async function GET(request: NextRequest) {
  try {
    // Rate limiting
    const rateLimitResult = await rateLimit(request, {
      maxRequests: 100,
      windowMs: 60 * 1000, // 1 minute
    });

    if (!rateLimitResult.success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        {
          status: 429,
          headers: {
            'Retry-After': '60',
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': rateLimitResult.resetTime?.toString() || '',
          },
        }
      );
    }

    // Extract and validate query parameters
    const url = new URL(request.url);
    const searchParams = Object.fromEntries(url.searchParams.entries());

    const validatedParams = await validateRequest(getJobsSchema, searchParams);

    // Fetch jobs
    const result = await jobsService.getJobs(validatedParams);

    return NextResponse.json(result, {
      headers: {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': rateLimitResult.remaining.toString(),
        'X-RateLimit-Reset': rateLimitResult.resetTime?.toString() || '',
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
      },
    });
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * POST /api/jobs
 * Create a new job posting (admin/company only)
 */
export async function POST(request: NextRequest) {
  try {
    // Rate limiting for POST requests (stricter)
    const rateLimitResult = await rateLimit(request, {
      maxRequests: 10,
      windowMs: 60 * 1000, // 1 minute
    });

    if (!rateLimitResult.success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        { status: 429 }
      );
    }

    // Check authentication
    const session = await getServerSession(authOptions);
    if (!session) {
      throw new ApiError(401, 'Authentication required');
    }

    // Check authorization (admin or company user)
    if (!['admin', 'company'].includes(session.user.role)) {
      throw new ApiError(403, 'Insufficient permissions');
    }

    // Parse and validate request body
    const body = await request.json();
    const validatedData = await validateRequest(createJobSchema, body);

    // Verify company ownership for non-admin users
    if (session.user.role === 'company' && validatedData.companyId !== session.user.companyId) {
      throw new ApiError(403, 'Cannot create jobs for other companies');
    }

    // Create job
    const job = await jobsService.createJob({
      ...validatedData,
      createdBy: session.user.id,
    });

    return NextResponse.json(job, {
      status: 201,
      headers: {
        'Location': `/api/jobs/${job.id}`,
      },
    });
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * OPTIONS /api/jobs
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Allow': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Origin': process.env.ALLOWED_ORIGINS || '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}