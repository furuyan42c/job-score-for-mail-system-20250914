/**
 * Middleware for Job Matching System
 * Handles authentication, rate limiting, logging, and locale detection
 */

import { NextRequest, NextResponse } from 'next/server';
import { getToken } from 'next-auth/jwt';

// Rate limiting store (in production, use Redis)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

// Protected routes that require authentication
const protectedRoutes = [
  '/dashboard',
  '/profile',
  '/preferences',
  '/recommendations',
  '/applied',
  '/saved',
  '/history',
  '/settings',
];

// Admin routes that require admin role
const adminRoutes = [
  '/admin',
];

// API routes that need rate limiting
const apiRoutes = [
  '/api/jobs',
  '/api/users',
  '/api/scores',
  '/api/actions',
];

// Supported locales
const locales = ['en', 'ja', 'es', 'fr', 'de'];
const defaultLocale = 'en';

/**
 * Rate limiting function
 */
function rateLimit(identifier: string, limit = 100, windowMs = 60000): boolean {
  const now = Date.now();
  const key = `${identifier}:${Math.floor(now / windowMs)}`;

  const current = rateLimitStore.get(key) || { count: 0, resetTime: now + windowMs };

  if (current.count >= limit) {
    return false;
  }

  rateLimitStore.set(key, {
    count: current.count + 1,
    resetTime: current.resetTime,
  });

  // Clean up old entries
  for (const [storeKey, value] of rateLimitStore.entries()) {
    if (value.resetTime < now) {
      rateLimitStore.delete(storeKey);
    }
  }

  return true;
}

/**
 * Locale detection and redirect
 */
function handleLocale(request: NextRequest): NextResponse | null {
  const pathname = request.nextUrl.pathname;

  // Check if pathname already has a locale
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) return null;

  // Get preferred locale from headers
  const acceptLanguage = request.headers.get('accept-language') || '';
  const preferredLocale = acceptLanguage
    .split(',')[0]
    ?.split('-')[0]
    ?.toLowerCase();

  const locale = locales.includes(preferredLocale) ? preferredLocale : defaultLocale;

  // Redirect to locale-prefixed URL
  const url = request.nextUrl.clone();
  url.pathname = `/${locale}${pathname}`;

  return NextResponse.redirect(url);
}

/**
 * Authentication check
 */
async function checkAuth(request: NextRequest): Promise<NextResponse | null> {
  const pathname = request.nextUrl.pathname;

  // Remove locale prefix for route checking
  const pathWithoutLocale = pathname.replace(/^\/[a-z]{2}/, '') || '/';

  // Check if route requires authentication
  const isProtectedRoute = protectedRoutes.some(route =>
    pathWithoutLocale.startsWith(route)
  );

  const isAdminRoute = adminRoutes.some(route =>
    pathWithoutLocale.startsWith(route)
  );

  if (!isProtectedRoute && !isAdminRoute) return null;

  // Get token from request
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  });

  if (!token) {
    // Redirect to login with callback URL
    const url = request.nextUrl.clone();
    url.pathname = '/auth/signin';
    url.searchParams.set('callbackUrl', pathname);

    return NextResponse.redirect(url);
  }

  // Check admin role for admin routes
  if (isAdminRoute && token.role !== 'admin') {
    const url = request.nextUrl.clone();
    url.pathname = '/unauthorized';

    return NextResponse.redirect(url);
  }

  return null;
}

/**
 * Request logging
 */
function logRequest(request: NextRequest): void {
  const { method, url, ip, geo } = request;
  const userAgent = request.headers.get('user-agent') || 'unknown';

  console.log(JSON.stringify({
    timestamp: new Date().toISOString(),
    method,
    url,
    ip,
    userAgent,
    country: geo?.country,
    city: geo?.city,
  }));
}

/**
 * Security headers
 */
function addSecurityHeaders(response: NextResponse): NextResponse {
  // Content Security Policy
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://vercel.live; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';"
  );

  // Other security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin');
  response.headers.set('X-DNS-Prefetch-Control', 'off');
  response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  return response;
}

export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Skip middleware for static files and API routes that don't need it
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/auth') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    return NextResponse.next();
  }

  // Log request
  logRequest(request);

  // Handle locale detection and redirect
  const localeResponse = handleLocale(request);
  if (localeResponse) return localeResponse;

  // Rate limiting for API routes
  if (apiRoutes.some(route => pathname.startsWith(route))) {
    const identifier = request.ip || 'anonymous';

    if (!rateLimit(identifier)) {
      return new NextResponse(
        JSON.stringify({ error: 'Too many requests' }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': '60',
          },
        }
      );
    }
  }

  // Check authentication
  const authResponse = await checkAuth(request);
  if (authResponse) return authResponse;

  // Continue with request and add security headers
  const response = NextResponse.next();
  return addSecurityHeaders(response);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};