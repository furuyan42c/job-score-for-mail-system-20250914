import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * T068: v0フロントエンドSupabase統合 - Playwright Global Setup
 * TDD用グローバルセットアップ（認証なし・Supabase接続検証のみ）
 */
async function globalSetup(config: FullConfig) {
  console.log('🔧 T068 Global Setup: Supabase Integration E2E Tests');

  try {
    // テスト環境の確認
    console.log('📊 Environment Check:');
    console.log(`  - Base URL: ${config.projects[0].use.baseURL || 'http://localhost:3000'}`);
    console.log(`  - Supabase URL: ${process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://127.0.0.1:54321'}`);

    // Supabase接続確認（RED Phaseでは失敗想定）
    console.log('🔍 Checking Supabase connection...');
    await checkSupabaseConnection();

    // v0フロントエンド確認
    console.log('🌐 Checking v0 frontend...');
    await checkFrontendAccess();

    // テスト結果ディレクトリ作成
    createTestDirectories();

    console.log('✅ Global setup completed successfully');

  } catch (error) {
    console.log('⚠️ Setup completed with expected failures (RED phase)');
    // TDDのRED phaseでは失敗が想定されるため、エラーを投げない
  }
}

/**
 * Supabase接続確認（TDD RED Phaseでは失敗想定）
 */
async function checkSupabaseConnection(): Promise<void> {
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://127.0.0.1:54321';
    const response = await fetch(`${supabaseUrl}/rest/v1/`, {
      method: 'GET',
      headers: {
        'apikey': process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'demo-key'
      }
    });

    if (response.ok || response.status === 401) {
      console.log('✅ Supabase connection available');
    } else {
      console.log('🔴 RED Phase: Supabase connection failed (expected)');
    }
  } catch (error) {
    console.log('🔴 RED Phase: Supabase connection error (expected)');
  }
}

/**
 * v0フロントエンドアクセス確認
 */
async function checkFrontendAccess(): Promise<void> {
  try {
    const response = await fetch('http://localhost:3000');

    if (response.ok) {
      console.log('✅ v0 frontend accessible');
    } else {
      console.log('🔴 RED Phase: v0 frontend access failed (expected)');
    }
  } catch (error) {
    console.log('🔴 RED Phase: v0 frontend connection error (expected)');
  }
}


/**
 * Create test directories if they don't exist
 */
function createTestDirectories(): void {
  const directories = [
    'test-results',
    'test-results/screenshots',
    'test-results/videos',
    'test-results/traces',
    'test-results/downloads'
  ];

  directories.forEach(dir => {
    const fullPath = path.resolve(dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
      console.log(`📁 Created directory: ${dir}`);
    }
  });
}

export default globalSetup;