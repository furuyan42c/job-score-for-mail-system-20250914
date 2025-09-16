# GPT-5 nano Integration Added - 2025-09-16

## Update Summary
Added GPT-5 nano AI email subject generation specifications to both asks.md and answers.md

## Key Specifications Added

### GPT-5 nano Configuration
- Model: gpt-5-nano (OpenAI)
- Purpose: Generate personalized email subjects
- Max tokens: 60
- Temperature: 0.7 (balanced creativity)
- Timeout: 5 seconds
- Fallback: Template-based subjects

### Implementation Strategy
1. **Individual Generation**: Each user gets personalized subject
2. **Caching**: Similar users share subjects (cache key based on area + categories)
3. **Batch Processing**: 100 users at a time, 10 parallel requests
4. **Rate Limiting**: 100 requests/minute
5. **Error Handling**: Fallback to templates on API failure

### Subject Generation Context
- User area (inferred from application history)
- Frequent job categories (top 3)
- Recent applications (5 most recent)
- TOP5 job titles
- Featured job
- New job count

### Fallback Templates
- 【バイト速報】{area}のおすすめ求人{count}件
- 【{area}】今週の注目バイト{count}件をお届け
- 【新着あり】{area}エリアの人気求人{count}件

### A/B Testing Support
- Initially disabled
- Can generate variations with different temperatures
- Tracks open_rate and click_rate metrics

## Files Updated
- specs/001-job-matching-system/asks.md: Added section 7.0 with GPT-5 nano questions
- specs/001-job-matching-system/answers.md: Added complete implementation guide for GPT-5 nano