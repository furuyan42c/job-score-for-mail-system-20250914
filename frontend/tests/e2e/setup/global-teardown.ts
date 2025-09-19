import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test teardown...');

  try {
    // Cleanup test data, close connections, etc.
    // This could include database cleanup, file cleanup, etc.

    console.log('✅ Test environment cleaned up');
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  }

  console.log('🏁 E2E test teardown completed');
}

export default globalTeardown;