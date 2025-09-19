# E2E Tests for Mail Score Backend Dashboard

This directory contains comprehensive end-to-end tests for the Mail Score backend dashboard application using Playwright.

## Test Coverage

### T050: SQL Execution E2E Test (`sql-execution.spec.ts`)
Tests the complete SQL query workflow:
- ✅ Table selection from sidebar (19 tables)
- ✅ SQL query input and execution
- ✅ Result display and error handling
- ✅ Tab switching between SQL Query, Data Browser, Table Structure
- ✅ Performance and responsiveness testing

### T051: Dashboard E2E Test (`dashboard.spec.ts`)
Tests dashboard functionality:
- ✅ Table structure tab with detailed column information
- ✅ Data browsing tab with mock data display
- ✅ Search functionality (table name and description filtering)
- ✅ Statistics display and monitoring
- ✅ Real-time status indicators

### T052: UI Responsive E2E Test (`responsive.spec.ts`)
Tests responsive design across viewports:
- ✅ Desktop (1920x1080) layout
- ✅ Tablet (768x1024) layout
- ✅ Mobile (375x667) layout
- ✅ Cross-viewport functionality
- ✅ Touch target optimization
- ✅ Visual consistency

## Project Structure

```
tests/e2e/
├── fixtures/
│   └── test-data.ts          # Test data constants and fixtures
├── helpers/
│   ├── database-helpers.ts   # Database interaction utilities
│   └── responsive-helpers.ts # Responsive testing utilities
├── setup/
│   ├── global-setup.ts       # Test environment setup
│   └── global-teardown.ts    # Test environment cleanup
├── dashboard.spec.ts         # T051: Dashboard functionality tests
├── responsive.spec.ts        # T052: Responsive design tests
├── sql-execution.spec.ts     # T050: SQL execution tests
├── supabase-integration.spec.ts # Existing Supabase integration tests
└── README.md                 # This file
```

## Running Tests

### Prerequisites
1. Ensure the frontend development server is running:
   ```bash
   npm run dev
   ```

2. Install Playwright browsers (if not already installed):
   ```bash
   npx playwright install
   ```

### Test Commands

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with UI mode for debugging
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Debug tests step by step
npm run test:e2e:debug

# Run specific test suites
npm run test:e2e:sql         # T050: SQL Execution tests
npm run test:e2e:dashboard   # T051: Dashboard tests
npm run test:e2e:responsive  # T052: Responsive tests

# View test results
npm run test:e2e:report
```

### Advanced Playwright Commands

```bash
# Run tests on specific browsers
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run tests on mobile browsers
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"

# Run tests in parallel
npx playwright test --workers=4

# Generate test report
npx playwright show-report
```

## Test Configuration

The tests are configured in `playwright.config.ts` with:
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Retries**: 2 retries on CI, 0 locally
- **Timeouts**: 60s test timeout, 10s expect timeout
- **Screenshots**: On failure only
- **Videos**: Retained on failure
- **Traces**: On first retry

## Test Data and Fixtures

### Database Tables (19 total)
- `users`, `jobs`, `jobs_match_raw`, `jobs_contents_raw`
- `user_actions`, `daily_email_queue`, `job_enrichment`
- `user_job_mapping`, `daily_job_picks`, `user_profiles`
- `keyword_scoring`, `semrush_keywords`
- `occupation_master`, `prefecture_master`, `city_master`
- `employment_type_master`, `salary_type_master`
- `feature_master`, `needs_category_master`

### Test Queries
- **Valid queries**: Basic SELECT statements, JOINs, aggregates
- **Invalid queries**: Syntax errors, missing tables, typos
- **Performance queries**: Large result sets, complex operations

### Responsive Viewports
- **Desktop**: 1920x1080, 1366x768, 2560x1440
- **Tablet**: 768x1024, 1024x768 (landscape)
- **Mobile**: 375x667, 320x568 (iPhone SE)

## Helper Classes

### DatabaseHelpers
Provides utilities for:
- Navigation and table selection
- SQL query execution
- Tab switching
- Error handling
- Statistics retrieval

### ResponsiveHelpers
Provides utilities for:
- Viewport management
- Layout verification
- Touch target validation
- Screenshot capture
- Cross-breakpoint testing

## Performance Thresholds

- **Page Load**: < 5 seconds
- **Query Execution**: < 10 seconds
- **Tab Switch**: < 1 second
- **Search**: < 2 seconds
- **Table Load**: < 3 seconds

## Expected Behavior

### Current Implementation (v0 Mock)
The tests are designed to work with the current v0 frontend implementation, which includes:
- Mock data for all 19 database tables
- Simulated SQL query execution
- Responsive UI components
- Real-time status indicators (mock)

### Error Handling
Tests verify appropriate error handling for:
- Invalid SQL queries
- Network failures
- Missing data
- UI interaction errors

### Accessibility
Tests include checks for:
- ARIA labels and roles
- Keyboard navigation
- Touch target sizes
- Screen reader compatibility

## Debugging Tests

### Common Issues
1. **Test timeouts**: Increase timeout values in configuration
2. **Element not found**: Check data-testid attributes in components
3. **Viewport issues**: Verify responsive design implementation
4. **Flaky tests**: Add wait conditions and retry logic

### Debug Tools
- Use `--debug` flag to step through tests
- Use `--ui` flag for interactive debugging
- Check browser developer tools during headed runs
- Review screenshots and videos in `test-results/`

### Troubleshooting

```bash
# Clear test cache
rm -rf test-results/

# Update Playwright
npm install @playwright/test@latest

# Reinstall browsers
npx playwright install --force
```

## Contributing

When adding new tests:
1. Follow the existing file naming convention
2. Use appropriate helper classes
3. Add test data to fixtures
4. Include performance expectations
5. Test across all viewports
6. Document new functionality

### Test Structure
```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup code
  });

  test('should do something specific', async ({ page }) => {
    // Test implementation
  });
});
```

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines with:
- Headless execution
- Retry logic for flaky tests
- Artifact generation (screenshots, videos, reports)
- JUnit XML output for integration

## Future Enhancements

- Visual regression testing with screenshot comparison
- Performance monitoring and metrics collection
- Database state validation
- API integration testing
- Cross-browser compatibility matrix
- Accessibility audit automation