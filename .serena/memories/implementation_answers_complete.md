# Implementation Answers Completed - 2025-09-16

## Summary
Comprehensive answers provided for all 35+ questions in asks.md, enabling immediate implementation start.

## Key Decisions Made

### Scoring Algorithms
- Basic Score: Weighted average (wage 35%, access 25%, benefits 20%, popularity 20%)
- SEO Score: Partial matching with search volume weighting
- Personalized Score: ALS with 20 factors, 10 iterations

### Email Sections (40 jobs total)
1. TOP5: Personalized recommendations (5 jobs)
2. Regional: Prefecture-level jobs (10 jobs)
3. Nearby: City-level popular jobs (10 jobs)
4. Benefits: Jobs with special perks (10 jobs)
5. New: Recent postings within 3 days (5 jobs)

### User Information Strategy
- NO personal address data collected
- Location inferred from application history only
- Prefecture/city estimation based on past job applications
- Default to Tokyo (13) if no history available

### Data Management
- Soft delete with is_active flag
- History retention for 30 days
- Duplicate handling by compound key
- Checkpoint-based batch processing

### Error Handling
- Checkpoint every 100 users
- 3 retry attempts with 60s delay
- 10% failure threshold for batch stop
- Individual email generation retries

### Performance Optimization
- dtype optimization (int32, float32, category)
- Chunk processing (1000 rows)
- Supabase Edge Functions caching
- Memory limit: 4GB strict

### Testing Strategy
- Faker with realistic patterns
- 100k jobs, 10k users
- Behavior pattern simulation
- Seed=42 for reproducibility

## Implementation Ready
All ambiguities resolved. Tasks can now be executed without blockers.