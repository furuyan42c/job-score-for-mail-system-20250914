#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function log(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️', deploy: '🚀' };
  console.log(`${icons[type]} ${message}`);
}

function executeCommand(command, description, exitOnError = false) {
  log(`実行中: ${description}`, 'info');
  try {
    const result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    log(`完了: ${description}`, 'success');
    return { success: true, output: result };
  } catch (error) {
    log(`エラー: ${description}`, 'error');
    if (exitOnError) {
      console.log(error.stdout + error.stderr);
      process.exit(1);
    }
    return { success: false, output: error.stdout + error.stderr };
  }
}

function checkPreDeployRequirements() {
  log('📋 デプロイ前チェックを実行中...', 'info');

  const requirements = [];

  // Git状態確認
  const gitStatus = executeCommand('git status --porcelain', 'Git状態確認');
  if (gitStatus.success && gitStatus.output.trim() !== '') {
    requirements.push('未コミットの変更があります');
  }

  // ブランチ確認
  const branch = executeCommand('git branch --show-current', '現在のブランチ確認');
  if (branch.success && branch.output.trim() !== 'main' && branch.output.trim() !== 'master') {
    requirements.push(`現在のブランチ: ${branch.output.trim()}`);
  }

  // 設定ファイル確認
  const requiredFiles = ['.env.production', 'package.json'];
  requiredFiles.forEach(file => {
    if (!fs.existsSync(file)) {
      requirements.push(`必要なファイルが見つかりません: ${file}`);
    }
  });

  // テスト実行
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  if (packageJson.scripts && packageJson.scripts.test) {
    const testResult = executeCommand('npm test', 'テスト実行');
    if (!testResult.success) {
      requirements.push('テストが失敗しています');
    }
  }

  // ビルド確認
  if (packageJson.scripts && packageJson.scripts.build) {
    const buildResult = executeCommand('npm run build', 'ビルド実行');
    if (!buildResult.success) {
      requirements.push('ビルドが失敗しています');
    }
  }

  return requirements;
}

function detectDeploymentPlatform() {
  log('🔍 デプロイプラットフォームを検出中...', 'info');

  const platforms = [];

  // Vercel
  if (fs.existsSync('vercel.json') || fs.existsSync('.vercel')) {
    platforms.push('vercel');
  }

  // Netlify
  if (fs.existsSync('netlify.toml') || fs.existsSync('_redirects')) {
    platforms.push('netlify');
  }

  // Heroku
  if (fs.existsSync('Procfile') || fs.existsSync('app.json')) {
    platforms.push('heroku');
  }

  // Docker
  if (fs.existsSync('Dockerfile') || fs.existsSync('docker-compose.yml')) {
    platforms.push('docker');
  }

  // AWS
  if (fs.existsSync('.aws') || fs.existsSync('aws.yml') || fs.existsSync('serverless.yml')) {
    platforms.push('aws');
  }

  // Firebase
  if (fs.existsSync('firebase.json') || fs.existsSync('.firebaserc')) {
    platforms.push('firebase');
  }

  // GitHub Actions
  if (fs.existsSync('.github/workflows')) {
    platforms.push('github-actions');
  }

  return platforms;
}

function deployToVercel(environment = 'production') {
  log(`🚀 Vercelにデプロイ中 (${environment})...`, 'deploy');

  const command = environment === 'production' ? 'npx vercel --prod' : 'npx vercel';
  const result = executeCommand(command, `Vercel ${environment} デプロイ`);

  if (result.success) {
    const url = result.output.match(/https:\/\/[^\s]+/);
    if (url) {
      log(`デプロイ完了: ${url[0]}`, 'success');
    }
  }

  return result.success;
}

function deployToNetlify(environment = 'production') {
  log(`🚀 Netlifyにデプロイ中 (${environment})...`, 'deploy');

  // ビルド
  executeCommand('npm run build', 'Netlify用ビルド', true);

  const command = environment === 'production' ?
    'npx netlify deploy --prod --dir=dist' :
    'npx netlify deploy --dir=dist';

  const result = executeCommand(command, `Netlify ${environment} デプロイ`);
  return result.success;
}

function deployToHeroku(app = null) {
  log(`🚀 Herokuにデプロイ中...`, 'deploy');

  const appFlag = app ? ` --app ${app}` : '';

  // Herokuにプッシュ
  const result = executeCommand(`git push heroku main${appFlag}`, 'Herokuデプロイ');

  if (result.success) {
    executeCommand(`heroku open${appFlag}`, 'アプリを開く');
  }

  return result.success;
}

function deployWithDocker(tag = 'latest') {
  log(`🐳 Dockerデプロイ中...`, 'deploy');

  // Dockerイメージビルド
  const buildResult = executeCommand(`docker build -t app:${tag} .`, 'Dockerイメージビルド');
  if (!buildResult.success) {
    return false;
  }

  // コンテナ実行 (開発用)
  executeCommand('docker run -d -p 3000:3000 app:latest', 'Dockerコンテナ実行');

  log('Docker デプロイ完了: http://localhost:3000', 'success');
  return true;
}

function deployToAWS(service = 'ec2') {
  log(`☁️ AWSにデプロイ中 (${service})...`, 'deploy');

  switch (service) {
    case 'lambda':
      if (fs.existsSync('serverless.yml')) {
        return executeCommand('npx serverless deploy', 'AWS Lambda デプロイ').success;
      }
      break;

    case 's3':
      executeCommand('npm run build', 'S3用ビルド', true);
      return executeCommand('aws s3 sync dist/ s3://your-bucket-name --delete', 'S3デプロイ').success;

    default:
      log('AWS EC2へのデプロイは手動設定が必要です', 'info');
      return false;
  }
}

function deployToFirebase() {
  log(`🔥 Firebaseにデプロイ中...`, 'deploy');

  // ビルド
  executeCommand('npm run build', 'Firebase用ビルド', true);

  // デプロイ
  const result = executeCommand('npx firebase deploy', 'Firebaseデプロイ');
  return result.success;
}

function createDeploymentScript(platforms) {
  log('📝 デプロイスクリプトを作成中...', 'info');

  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};

  if (!packageJson.scripts) {
    packageJson.scripts = {};
  }

  platforms.forEach(platform => {
    switch (platform) {
      case 'vercel':
        packageJson.scripts['deploy:vercel:dev'] = 'vercel';
        packageJson.scripts['deploy:vercel:prod'] = 'vercel --prod';
        break;

      case 'netlify':
        packageJson.scripts['deploy:netlify:dev'] = 'netlify deploy --dir=dist';
        packageJson.scripts['deploy:netlify:prod'] = 'netlify deploy --prod --dir=dist';
        break;

      case 'heroku':
        packageJson.scripts['deploy:heroku'] = 'git push heroku main';
        break;

      case 'firebase':
        packageJson.scripts['deploy:firebase'] = 'npm run build && firebase deploy';
        break;
    }
  });

  fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2));
  log('package.json にデプロイスクリプトを追加しました', 'success');
}

function rollbackDeployment(platform) {
  log(`⏪ ${platform} からロールバック中...`, 'warning');

  switch (platform) {
    case 'vercel':
      executeCommand('npx vercel rollback', 'Vercel ロールバック');
      break;

    case 'heroku':
      executeCommand('heroku rollback', 'Heroku ロールバック');
      break;

    default:
      log(`${platform} のロールバックは手動で実行してください`, 'warning');
  }
}

function generateDeploymentReport(platforms, results) {
  const report = `# デプロイメントレポート

実行日時: ${new Date().toLocaleString('ja-JP')}

## デプロイ結果

${platforms.map((platform, index) =>
  `### ${platform.toUpperCase()}
  - ステータス: ${results[index] ? '✅ 成功' : '❌ 失敗'}
  - デプロイ時刻: ${new Date().toLocaleString('ja-JP')}`
).join('\n\n')}

## 次のアクション

- [ ] 本番環境での動作確認
- [ ] パフォーマンス監視
- [ ] エラーログの確認

---
*Generated by Claude Code /deploy command*
`;

  fs.writeFileSync('.claude/deployment-report.md', report);
  log('デプロイレポートを .claude/deployment-report.md に保存しました', 'success');
}

function main() {
  const args = process.argv.slice(2);

  const options = {
    platform: args.find(arg => arg.startsWith('--platform='))?.split('=')[1],
    environment: args.find(arg => arg.startsWith('--env='))?.split('=')[1] || 'production',
    skipChecks: args.includes('--skip-checks'),
    rollback: args.includes('--rollback'),
    createScript: args.includes('--create-script'),
    app: args.find(arg => arg.startsWith('--app='))?.split('=')[1]
  };

  log('🚀 デプロイメント管理ツールを開始します', 'deploy');

  // ロールバック
  if (options.rollback && options.platform) {
    rollbackDeployment(options.platform);
    return;
  }

  // プラットフォーム検出
  const detectedPlatforms = detectDeploymentPlatform();
  const targetPlatforms = options.platform ? [options.platform] : detectedPlatforms;

  if (targetPlatforms.length === 0) {
    log('デプロイプラットフォームが検出されませんでした', 'warning');
    log('以下のコマンドでセットアップを検討してください:', 'info');
    console.log('  --platform=vercel   # Vercel設定');
    console.log('  --platform=netlify  # Netlify設定');
    console.log('  --platform=heroku   # Heroku設定');
    return;
  }

  log(`検出されたプラットフォーム: ${targetPlatforms.join(', ')}`, 'info');

  // デプロイスクリプト作成
  if (options.createScript) {
    createDeploymentScript(targetPlatforms);
    return;
  }

  // デプロイ前チェック
  if (!options.skipChecks) {
    const requirements = checkPreDeployRequirements();
    if (requirements.length > 0) {
      log('デプロイ前の問題:', 'warning');
      requirements.forEach(req => console.log(`  - ${req}`));
      console.log('\n問題を修正するか --skip-checks を使用してください');
      return;
    }
  }

  // デプロイ実行
  const results = [];

  for (const platform of targetPlatforms) {
    let success = false;

    switch (platform) {
      case 'vercel':
        success = deployToVercel(options.environment);
        break;

      case 'netlify':
        success = deployToNetlify(options.environment);
        break;

      case 'heroku':
        success = deployToHeroku(options.app);
        break;

      case 'docker':
        success = deployWithDocker();
        break;

      case 'firebase':
        success = deployToFirebase();
        break;

      case 'aws':
        success = deployToAWS('lambda');
        break;

      default:
        log(`${platform} のデプロイは未対応です`, 'warning');
        success = false;
    }

    results.push(success);
  }

  // レポート生成
  generateDeploymentReport(targetPlatforms, results);

  const successCount = results.filter(r => r).length;
  if (successCount === targetPlatforms.length) {
    log('🎉 全てのデプロイが完了しました！', 'success');
  } else {
    log(`❌ ${targetPlatforms.length - successCount} 個のデプロイが失敗しました`, 'error');
  }
}

main();
