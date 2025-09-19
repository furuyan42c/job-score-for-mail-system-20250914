import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test setup...');

  // Launch browser for setup
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Wait for application to be ready
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle', { timeout: 30000 });

    // Verify basic application functionality
    await page.waitForSelector('[data-testid="main-content"]', { timeout: 10000 });

    console.log('✅ Application is ready for testing');

    // Setup test environment state if needed
    // This could include database seeding, auth setup, etc.

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }

  console.log('🎯 E2E test setup completed');
}

export default globalSetup;