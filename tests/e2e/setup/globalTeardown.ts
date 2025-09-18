import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * T068: v0フロントエンドSupabase統合 - Playwright Global Teardown
 * TDD用グローバル後処理（認証なし・シンプルクリーンアップ）
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 T068 Global Teardown: Supabase Integration E2E Tests');

  try {
    // テスト結果のサマリー生成
    console.log('📊 Generating test summary...');
    await generateTestSummary();

    // 一時ファイルクリーンアップ
    console.log('🗂️ Cleaning up temporary files...');
    await cleanupTemporaryFiles();

    console.log('✅ Global teardown completed successfully');

  } catch (error) {
    console.log('⚠️ Teardown completed with warnings');
    // テスト失敗をマスクしないため、エラーを投げない
  }
}


/**
 * Clean up temporary files created during tests
 */
async function cleanupTemporaryFiles(): Promise<void> {

  try {
    const tempDirs = [
      'temp',
      'tmp',
      '.tmp',
      'test-results/downloads'
    ];

    for (const dir of tempDirs) {
      const fullPath = path.resolve(dir);

      if (fs.existsSync(fullPath)) {
        const files = fs.readdirSync(fullPath);

        for (const file of files) {
          const filePath = path.join(fullPath, file);

          if (fs.statSync(filePath).isFile()) {
            fs.unlinkSync(filePath);
          }
        }

        console.log(`🗑️ Cleaned temporary directory: ${dir}`);
      }
    }

    // T068用: Supabaseテスト関連ファイルのクリーンアップ
    console.log('🗑️ Cleaned temporary directories for Supabase tests');

    console.log('✅ Temporary files cleanup completed');

  } catch (error) {
    console.log('⚠️ Could not cleanup temporary files:', error.message);
  }
}

/**
 * Generate a summary of test results
 */
async function generateTestSummary(): Promise<void> {

  try {
    const testResultsDir = 'test-results';
    const summaryFile = path.join(testResultsDir, 'test-summary.json');

    const summary = {
      timestamp: new Date().toISOString(),
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
      },
      testRun: {
        startTime: process.env.TEST_START_TIME || new Date().toISOString(),
        endTime: new Date().toISOString(),
        duration: process.env.TEST_START_TIME
          ? Date.now() - new Date(process.env.TEST_START_TIME).getTime()
          : 'Unknown'
      },
      artifacts: {
        screenshots: 0,
        videos: 0,
        traces: 0,
        downloads: 0
      }
    };

    // Count artifacts
    const artifactDirs = [
      { dir: 'screenshots', key: 'screenshots' },
      { dir: 'videos', key: 'videos' },
      { dir: 'traces', key: 'traces' },
      { dir: 'downloads', key: 'downloads' }
    ];

    for (const { dir, key } of artifactDirs) {
      const dirPath = path.join(testResultsDir, dir);
      if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath);
        summary.artifacts[key] = files.length;
      }
    }

    // Write summary
    fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));

    console.log('📊 Test summary generated:', summary);
    console.log(`📄 Summary saved to: ${summaryFile}`);

  } catch (error) {
    console.log('⚠️ Could not generate test summary:', error.message);
  }
}

/**
 * Clean up old test result artifacts
 */
async function cleanupOldArtifacts(): Promise<void> {

  try {
    const testResultsDir = 'test-results';
    const maxAgeHours = 72; // Keep artifacts for 3 days

    const artifactDirs = ['screenshots', 'videos', 'traces'];

    for (const dir of artifactDirs) {
      const dirPath = path.join(testResultsDir, dir);

      if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath);

        for (const file of files) {
          const filePath = path.join(dirPath, file);
          const stats = fs.statSync(filePath);
          const ageHours = (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60);

          if (ageHours > maxAgeHours) {
            fs.unlinkSync(filePath);
            console.log(`🗑️ Deleted old artifact: ${file}`);
          }
        }
      }
    }

    console.log('✅ Old artifacts cleanup completed');

  } catch (error) {
    console.log('⚠️ Could not cleanup old artifacts:', error.message);
  }
}

// Set test end time for duration calculation
process.env.TEST_END_TIME = new Date().toISOString();

export default globalTeardown;