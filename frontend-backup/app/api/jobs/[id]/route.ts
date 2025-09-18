/**
 * Individual Job API Route Handler
 * Handles operations for specific job posts
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
const updateJobSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().min(50).optional(),
  summary: z.string().max(500).optional(),
  location: z.string().min(1).optional(),
  category: z.string().min(1).optional(),
  employmentType: z.enum(['full-time', 'part-time', 'contract', 'internship']).optional(),
  experienceLevel: z.enum(['entry', 'mid', 'senior', 'lead', 'executive']).optional(),
  skills: z.array(z.string()).min(1).optional(),
  requirements: z.array(z.string()).optional(),
  benefits: z.array(z.string()).optional(),
  salary: z.object({
    min: z.number().min(0),
    max: z.number().min(0),
    currency: z.string().default('USD'),
    period: z.enum(['hour', 'day', 'month', 'year']).default('year'),
  }).optional(),
  remote: z.boolean().optional(),
  urgent: z.boolean().optional(),
  workHours: z.string().optional(),
  expiresAt: z.string().datetime().optional(),
  status: z.enum(['draft', 'published', 'archived', 'closed']).optional(),
});

interface RouteParams {
  params: {
    id: string;
  };
}

/**
 * GET /api/jobs/[id]
 * Fetch a specific job by ID
 */
export async function GET(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    // Rate limiting
    const rateLimitResult = await rateLimit(request, {
      maxRequests: 200,
      windowMs: 60 * 1000, // 1 minute
    });

    if (!rateLimitResult.success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        { status: 429 }
      );
    }

    // Validate job ID
    if (!params.id || typeof params.id !== 'string') {
      throw new ApiError(400, 'Invalid job ID');
    }

    // Get session for potential user-specific data
    const session = await getServerSession(authOptions);

    // Fetch job with user context
    const job = await jobsService.getJobById(params.id, {
      userId: session?.user?.id,
      includeApplicationStatus: !!session,
      includeSaveStatus: !!session,
    });

    if (!job) {
      throw new ApiError(404, 'Job not found');
    }

    // Check if job is published or user has permission to view
    if (job.status !== 'published') {
      if (!session || !['admin', 'company'].includes(session.user.role)) {
        throw new ApiError(404, 'Job not found');
      }

      // Company users can only view their own jobs
      if (session.user.role === 'company' && job.companyId !== session.user.companyId) {
        throw new ApiError(404, 'Job not found');
      }
    }

    return NextResponse.json(job, {
      headers: {
        'Cache-Control': 'public, s-maxage=1800, stale-while-revalidate=3600',
        'X-RateLimit-Limit': '200',
        'X-RateLimit-Remaining': rateLimitResult.remaining.toString(),
      },
    });
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * PUT /api/jobs/[id]
 * Update a specific job (admin/company owner only)
 */
export async function PUT(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    // Rate limiting
    const rateLimitResult = await rateLimit(request, {
      maxRequests: 20,
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

    // Validate job ID
    if (!params.id || typeof params.id !== 'string') {
      throw new ApiError(400, 'Invalid job ID');
    }

    // Get existing job to check permissions
    const existingJob = await jobsService.getJobById(params.id);
    if (!existingJob) {
      throw new ApiError(404, 'Job not found');
    }

    // Check authorization
    if (session.user.role === 'admin') {
      // Admin can update any job
    } else if (session.user.role === 'company') {
      // Company users can only update their own jobs
      if (existingJob.companyId !== session.user.companyId) {
        throw new ApiError(403, 'Insufficient permissions');
      }
    } else {
      throw new ApiError(403, 'Insufficient permissions');
    }

    // Parse and validate request body
    const body = await request.json();
    const validatedData = await validateRequest(updateJobSchema, body);

    // Update job
    const updatedJob = await jobsService.updateJob(params.id, {
      ...validatedData,
      updatedBy: session.user.id,
      updatedAt: new Date().toISOString(),
    });

    return NextResponse.json(updatedJob);
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * DELETE /api/jobs/[id]
 * Delete a specific job (admin/company owner only)
 */
export async function DELETE(
  request: NextRequest,
  { params }: RouteParams
) {
  try {
    // Rate limiting
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

    // Validate job ID
    if (!params.id || typeof params.id !== 'string') {
      throw new ApiError(400, 'Invalid job ID');
    }

    // Get existing job to check permissions
    const existingJob = await jobsService.getJobById(params.id);
    if (!existingJob) {
      throw new ApiError(404, 'Job not found');
    }

    // Check authorization
    if (session.user.role === 'admin') {
      // Admin can delete any job
    } else if (session.user.role === 'company') {
      // Company users can only delete their own jobs
      if (existingJob.companyId !== session.user.companyId) {
        throw new ApiError(403, 'Insufficient permissions');
      }
    } else {
      throw new ApiError(403, 'Insufficient permissions');
    }

    // Delete job (soft delete - archive instead)
    await jobsService.updateJob(params.id, {
      status: 'archived',
      archivedBy: session.user.id,
      archivedAt: new Date().toISOString(),
    });

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    return handleApiError(error);
  }
}

/**
 * OPTIONS /api/jobs/[id]
 * Handle CORS preflight requests
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Allow': 'GET, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Origin': process.env.ALLOWED_ORIGINS || '*',
      'Access-Control-Allow-Methods': 'GET, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}