# E2E Testing Guide for Job Matching System

This guide explains how to set up and run the comprehensive End-to-End (E2E) tests for the job matching system using Playwright.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Installation & Setup](#installation--setup)
- [Running Tests](#running-tests)
- [Test Scenarios](#test-scenarios)
- [Page Object Model](#page-object-model)
- [Test Data & Fixtures](#test-data--fixtures)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The E2E test suite covers three main areas of the job matching system:

1. **User Flow Tests** (`user-flow.spec.ts`) - Complete user journeys from registration to job application
2. **SQL Execution Tests** (`sql-execution.spec.ts`) - SQL query interface, execution, and data export
3. **Dashboard Tests** (`dashboard.spec.ts`) - Batch monitoring, error logs, and performance metrics

## Test Structure

```
tests/e2e/
├── page-objects/           # Page Object Model classes
│   ├── BasePage.ts        # Base class with common functionality
│   ├── HomePage.ts        # Homepage interactions
│   ├── AuthPage.ts        # Login/Registration functionality
│   ├── JobsPage.ts        # Job search and application
│   ├── SqlExecutionPage.ts # SQL interface interactions
│   └── DashboardPage.ts   # Dashboard monitoring features
├── fixtures/              # Test data and fixtures
│   └── testData.ts        # User data, SQL queries, mock data
├── utils/                 # Test utilities and helpers
│   └── testUtils.ts       # Common testing functions
├── setup/                 # Global setup and teardown
│   ├── globalSetup.ts     # Pre-test setup
│   └── globalTeardown.ts  # Post-test cleanup
├── user-flow.spec.ts      # User journey tests
├── sql-execution.spec.ts  # SQL execution tests
└── dashboard.spec.ts      # Dashboard monitoring tests
```

## Installation & Setup

### 1. Install Dependencies

```bash
# Install Playwright and related dependencies
npm install

# Install Playwright browsers
npm run test:e2e:install
```

### 2. Environment Setup

Ensure your application is running locally:

```bash
# Start the frontend development server
npm run dev

# Start the backend server (if separate)
# npm run backend:dev
```

### 3. Database Setup

The tests expect certain test data to be available. You can set this up by:

1. Creating test user accounts
2. Seeding test jobs data
3. Setting up sample SQL data for query tests

## Running Tests

### Basic Commands

```bash
# Run all E2E tests
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in debug mode
npm run test:e2e:debug

# Run tests in headed mode (see browser)
npm run test:e2e:headed
```

### Browser-Specific Tests

```bash
# Run tests in Chrome only
npm run test:e2e:chrome

# Run tests in Firefox only
npm run test:e2e:firefox

# Run tests in Safari only
npm run test:e2e:safari

# Run mobile tests
npm run test:e2e:mobile
```

### Specific Test Files

```bash
# Run only user flow tests
npx playwright test user-flow

# Run only SQL execution tests
npx playwright test sql-execution

# Run only dashboard tests
npx playwright test dashboard

# Run specific test by name
npx playwright test --grep "should complete full user registration"
```

### View Test Reports

```bash
# Open HTML test report
npm run test:e2e:report

# View test results in terminal
npx playwright test --reporter=line
```

## Test Scenarios

### User Flow Tests

**New User Journey:**
- Homepage navigation and verification
- User registration with validation
- Profile setup completion
- Job search and filtering
- Job application submission
- Application status tracking

**Returning User Flow:**
- Login with existing credentials
- Personalized dashboard access
- Saved searches management
- Application history review
- Preference updates

**Email Integration:**
- Email link job viewing
- Notification settings management
- Application confirmations

### SQL Execution Tests

**Query Operations:**
- Simple SELECT queries
- Complex JOIN operations
- Query formatting and validation
- Keyboard shortcuts (Ctrl+Enter)

**Results Management:**
- Pagination handling
- CSV/JSON export functionality
- Large dataset handling
- Empty result sets

**Query History:**
- Query saving and loading
- History persistence
- Sample query usage

**Error Handling:**
- SQL syntax errors
- Connection failures
- Permission errors
- Query timeouts

### Dashboard Tests

**Batch Monitoring:**
- Real-time status updates
- Progress tracking
- Phase transitions
- Batch control operations (pause/stop/restart)

**Error Log Management:**
- Log filtering by severity
- Search functionality
- Log export capabilities
- Real-time log updates

**Performance Metrics:**
- CPU usage monitoring
- Memory usage tracking
- Database connection metrics
- System health indicators
- Auto-refresh functionality

## Page Object Model

The tests use the Page Object Model (POM) pattern for maintainability:

### BasePage

Base class providing common functionality:
- Element location helpers
- Wait utilities
- Screenshot capabilities
- Error monitoring
- Accessibility checks

### Specific Page Objects

Each page object extends BasePage and provides:
- Page-specific locators
- Action methods (click, fill, etc.)
- Verification methods
- Navigation helpers

Example usage:

```typescript
import { HomePage } from './page-objects/HomePage';

test('homepage test', async ({ page }) => {
  const homePage = new HomePage(page);
  await homePage.goto();
  await homePage.verifyHomePageLoaded();
  await homePage.clickSignUp();
});
```

## Test Data & Fixtures

### TestDataHelper

Utility class for generating test data:

```typescript
import { TestDataHelper } from './fixtures/testData';

// Generate unique test user
const user = TestDataHelper.generateTestUser({
  firstName: 'Custom',
  lastName: 'User'
});

// Get random SQL query
const query = TestDataHelper.getRandomQuery('complex');

// Generate date range for reports
const dateRange = TestDataHelper.generateDateRange(30);
```

### Available Test Data

- **TEST_USERS**: Various user types (new, existing, admin)
- **SAMPLE_JOBS**: Job listings for testing
- **SQL_QUERIES**: Valid and invalid queries for testing
- **DASHBOARD_DATA**: Mock dashboard data
- **ERROR_MESSAGES**: Expected error message patterns

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm ci

    - name: Install Playwright Browsers
      run: npx playwright install --with-deps

    - name: Start application
      run: |
        npm run dev &
        sleep 10

    - name: Run E2E tests
      run: npm run test:e2e

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: playwright-report
        path: playwright-report/
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
                sh 'npx playwright install --with-deps'
            }
        }

        stage('Start App') {
            steps {
                sh 'npm run dev &'
                sh 'sleep 30' // Wait for app to start
            }
        }

        stage('E2E Tests') {
            steps {
                sh 'npm run test:e2e'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: 'playwright-report',
                        reportFiles: 'index.html',
                        reportName: 'Playwright Test Report'
                    ])
                }
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

**1. Application Not Ready**
```bash
# Check if application is running
curl http://localhost:3000

# Wait longer for app startup
export PLAYWRIGHT_TIMEOUT=60000
```

**2. Browser Installation Issues**
```bash
# Reinstall browsers
npx playwright install --force

# Check browser dependencies
npx playwright install-deps
```

**3. Test Data Issues**
```bash
# Reset test database
npm run test:db:reset

# Create test users manually
npm run test:create-users
```

**4. Flaky Tests**
- Increase timeouts in playwright.config.ts
- Add explicit waits for dynamic content
- Use retry mechanisms for unstable operations

### Debug Mode

Run tests in debug mode to step through execution:

```bash
# Debug specific test
npx playwright test --debug user-flow.spec.ts

# Debug with browser console
npx playwright test --headed --debug
```

### Screenshots and Videos

Failed tests automatically capture:
- Screenshots (test-results/screenshots/)
- Videos (test-results/videos/)
- Traces (test-results/traces/)

View traces:
```bash
npx playwright show-trace test-results/traces/trace.zip
```

### Performance Monitoring

Tests include performance thresholds:
- Page load: < 3 seconds
- API responses: < 2 seconds
- Search operations: < 3 seconds

Monitor performance in test reports and adjust thresholds as needed.

## Best Practices

1. **Use Page Objects**: Keep tests maintainable with the POM pattern
2. **Explicit Waits**: Use explicit waits instead of arbitrary timeouts
3. **Test Isolation**: Each test should be independent
4. **Error Monitoring**: Monitor console errors and network failures
5. **Mobile Testing**: Include responsive design tests
6. **Accessibility**: Test keyboard navigation and ARIA attributes
7. **Performance**: Monitor and assert performance metrics
8. **Data Cleanup**: Clean up test data after test runs

## Contributing

When adding new tests:

1. Follow the existing Page Object Model structure
2. Add appropriate test data fixtures
3. Include error scenarios and edge cases
4. Test responsive design
5. Update this documentation

For questions or issues, please refer to the project's main documentation or create an issue in the repository.