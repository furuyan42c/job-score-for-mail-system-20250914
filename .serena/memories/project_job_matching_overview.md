# Job Matching System Project Overview
**Project**: Job Score for Mail System
**Repository**: /Users/naoki/000_PROJECT/job-score-for-mail-system-20250914
**Status**: Specification and Planning Complete, Ready for Implementation

## System Purpose
Match 100,000 jobs to 10,000 users daily (40 jobs per user) and generate personalized email content. System focuses on content generation, NOT email delivery.

## Key Specifications

### Scale Requirements
- 100,000 jobs × 10,000 users = 400,000 matches daily
- Processing time: < 30 minutes
- Memory usage: < 4GB
- Batch processing at 3 AM daily

### Core Technologies
- **Backend**: Python 3.11, Supabase (PostgreSQL), pandas, scikit-learn, APScheduler
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS (monitoring UI only)
- **ML**: Implicit library for collaborative filtering (ALS algorithm)
- **Testing**: pytest, Jest, Playwright for E2E

### Database Schema (20+ tables)
- Master tables: prefectures, cities, job categories, etc.
- Core tables: jobs (100+ fields), users, user_actions, user_profiles
- Processing tables: job_enrichment, user_job_mapping, daily_job_picks
- Queue tables: daily_email_queue, job_processing_history

### Email Structure (40 jobs per user)
1. **TOP5**: 5 personalized recommendations
2. **Regional (都道府県)**: 10 prefecture-level jobs
3. **Nearby (市区町村)**: 10 city-level jobs
4. **Benefits (お得)**: 10 jobs with special benefits
5. **New (新着)**: 5 recent job postings

### Scoring Algorithms
1. **Basic Score**: Job quality metrics
2. **SEO Score**: Search optimization potential
3. **Personalized Score**: User-specific preferences

### Category System
- 14 needs-based categories (高収入, 未経験OK, etc.)
- 12 occupation categories (飲食, 販売, IT, etc.)

## Current Implementation Status

### Completed Documents
- ✅ for-specify-prompt.md: System requirements
- ✅ spec.md: Detailed functional requirements (FR-001 to FR-010)
- ✅ plan.md: Implementation strategy with parallel execution
- ✅ research.md: Technology decisions and rationale
- ✅ data-model.md: Complete database schema
- ✅ api-contracts.yaml: OpenAPI specifications
- ✅ tasks.md: 74 detailed implementation tasks
- ✅ asks.md: 35+ clarification questions

### Frontend Status
- Existing Next.js app at /front (60% complete)
- Has SQL query interface, table browser, mock data
- Needs Supabase connection (T010-A task)
- Can be used for verification immediately after setup

### Key Implementation Notes
1. **Test Data**: Use /data/sample_job_data.csv (per FR-002 modification)
2. **TDD Approach**: Write tests first (RED), then implement (GREEN)
3. **Parallel Execution**: Can reduce 54 hours to 28.5 hours (47% savings)
4. **Continuous Verification**: Check points after each major implementation
5. **MCP Strategy**: Use Serena for code, Sequential for analysis, Magic for UI

## Critical Success Factors
1. Early Frontend setup for continuous verification
2. Proper database indexing for performance
3. Efficient batch processing with chunking
4. Memory management in pandas operations
5. Parallel processing for user matching

## Known Constraints
- No email delivery implementation (content only)
- Local development only (no deployment)
- SELECT-only SQL access from monitoring UI
- 30-minute processing window is hard limit
- Must handle 10k users without memory overflow

## Risk Areas
1. Memory usage during 10k user processing
2. 30-minute time constraint for full pipeline
3. Collaborative filtering scalability
4. Database connection pool management
5. Frontend performance with large result sets

## Quick Command Reference
```bash
# Start development
cd /Users/naoki/000_PROJECT/job-score-for-mail-system-20250914
git checkout feature/specification-20250915

# Run verification
/verify-and-pr 001-job-matching-system --comprehensive

# Check implementation
cd front && npm run dev
# Navigate to http://localhost:3000/monitoring
```