# Frontend Dockerfile for Next.js mail scoring application
# Multi-stage build for optimization and security

# Dependencies stage
FROM node:18-alpine as deps

# Set build arguments
ARG BUILD_DATE
ARG VERSION=latest
ARG VCS_REF

# Labels for container metadata
LABEL maintainer="mail-score-team" \
      description="Next.js frontend for mail scoring system" \
      version="${VERSION}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install system dependencies
RUN apk add --no-cache \
    libc6-compat \
    curl \
    ca-certificates

WORKDIR /app

# Copy package files for better caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Builder stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Install all dependencies for building
RUN npm ci

# Set build environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine as production

# Install system dependencies and dumb-init for signal handling
RUN apk add --no-cache \
    dumb-init \
    curl \
    ca-certificates

WORKDIR /app

# Create non-root user with explicit IDs for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Set production environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Enhanced health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=5 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "server.js"]

# Development stage
FROM node:18-alpine as development

# Install system dependencies
RUN apk add --no-cache \
    libc6-compat \
    curl \
    git \
    ca-certificates

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev)
RUN npm ci

# Copy source code
COPY . .

# Set development environment
ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Create nextjs user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app

USER nextjs

# Expose port
EXPOSE 3000

# Start development server with hot reload
CMD ["npm", "run", "dev"]