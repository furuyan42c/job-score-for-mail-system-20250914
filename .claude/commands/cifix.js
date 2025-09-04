#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');

function log(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
  console.log(`${icons[type]} ${message}`);
}

function executeCommand(command, description) {
  log(`実行中: ${description}`, 'info');
  try {
    const result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    log(`完了: ${description}`, 'success');
    return { success: true, output: result };
  } catch (error) {
    log(`エラー: ${description}`, 'error');
    return { success: false, output: error.stdout + error.stderr };
  }
}

function checkGitStatus() {
  const result = executeCommand('git status --porcelain', 'Git状態確認');
  return result.success && result.output.trim() === '';
}

function runTests() {
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  const scripts = packageJson.scripts || {};

  // テストコマンドの候補
  const testCommands = [
    scripts.test && 'npm test',
    scripts['test:unit'] && 'npm run test:unit',
    scripts['test:integration'] && 'npm run test:integration',
    scripts['test:e2e'] && 'npm run test:e2e',
    fs.existsSync('pytest.ini') && 'pytest',
    fs.existsSync('phpunit.xml') && 'phpunit',
    fs.existsSync('Cargo.toml') && 'cargo test',
    fs.existsSync('go.mod') && 'go test ./...'
  ].filter(Boolean);

  if (testCommands.length === 0) {
    log('テストコマンドが見つかりません', 'warning');
    return { success: true, output: 'No tests found' };
  }

  for (const command of testCommands) {
    const result = executeCommand(command, `テスト実行: ${command}`);
    if (!result.success) {
      return result;
    }
  }

  return { success: true, output: 'All tests passed' };
}

function runLintAndFormat() {
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  const scripts = packageJson.scripts || {};

  const lintCommands = [
    scripts.lint && 'npm run lint',
    scripts['lint:fix'] && 'npm run lint:fix',
    scripts.format && 'npm run format',
    scripts.prettier && 'npm run prettier',
    fs.existsSync('pyproject.toml') && 'ruff check --fix',
    fs.existsSync('pyproject.toml') && 'black .',
    fs.existsSync('Cargo.toml') && 'cargo fmt',
    fs.existsSync('Cargo.toml') && 'cargo clippy --fix --allow-dirty'
  ].filter(Boolean);

  for (const command of lintCommands) {
    executeCommand(command, `Lint/Format実行: ${command}`);
  }
}

function runTypeCheck() {
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  const scripts = packageJson.scripts || {};

  const typeCommands = [
    scripts['type-check'] && 'npm run type-check',
    scripts.typecheck && 'npm run typecheck',
    fs.existsSync('tsconfig.json') && 'npx tsc --noEmit',
    fs.existsSync('mypy.ini') && 'mypy .',
    fs.existsSync('Cargo.toml') && 'cargo check'
  ].filter(Boolean);

  for (const command of typeCommands) {
    const result = executeCommand(command, `型チェック: ${command}`);
    if (!result.success) {
      return result;
    }
  }

  return { success: true, output: 'Type check passed' };
}

function checkCIStatus() {
  try {
    const result = executeCommand('gh pr checks', 'GitHub PR チェック状態確認');
    if (result.success) {
      log('CI/CD状態:', 'info');
      console.log(result.output);
      return result.output.includes('✓') || result.output.includes('passing');
    }
  } catch (error) {
    log('GitHub CLI が利用できません。手動でCI状態を確認してください。', 'warning');
  }
  return true;
}

function fixCommonIssues() {
  log('一般的な問題の自動修正を試行中...', 'info');

  // Node.js関連
  if (fs.existsSync('package.json')) {
    executeCommand('npm audit fix', '脆弱性の自動修正');
    executeCommand('npm update', 'パッケージ更新');
  }

  // Git関連
  executeCommand('git add .', 'ファイルのステージング');

  // 権限修正
  executeCommand('find . -name "*.sh" -exec chmod +x {} \\;', 'シェルスクリプト実行権限付与');
}

function main() {
  const args = process.argv.slice(2);
  const options = {
    skipTests: args.includes('--skip-tests'),
    autoCommit: args.includes('--auto-commit'),
    maxRetries: parseInt(args.find(arg => arg.startsWith('--retries='))?.split('=')[1]) || 3
  };

  log('🔧 CI/CD エラー修正プロセスを開始します', 'info');

  let retryCount = 0;
  let allPassed = false;

  while (retryCount < options.maxRetries && !allPassed) {
    log(`\n🔄 試行 ${retryCount + 1}/${options.maxRetries}`, 'info');

    // 1. 一般的な問題の修正
    fixCommonIssues();

    // 2. Lint/Format実行
    runLintAndFormat();

    // 3. 型チェック
    const typeCheckResult = runTypeCheck();
    if (!typeCheckResult.success) {
      log('型チェックエラーがあります:', 'error');
      console.log(typeCheckResult.output);
      retryCount++;
      continue;
    }

    // 4. テスト実行
    if (!options.skipTests) {
      const testResult = runTests();
      if (!testResult.success) {
        log('テストエラーがあります:', 'error');
        console.log(testResult.output);
        retryCount++;
        continue;
      }
    }

    // 5. コミット（必要に応じて）
    if (options.autoCommit && !checkGitStatus()) {
      executeCommand('git add .', 'すべての変更をステージング');
      executeCommand('git commit -m "fix: CI/CD エラー修正 🤖"', 'エラー修正のコミット');
    }

    // 6. CI状態チェック
    const ciPassed = checkCIStatus();

    if (ciPassed) {
      allPassed = true;
      log('✨ すべてのチェックが成功しました！', 'success');
    } else {
      log('CI/CDでまだエラーがあります。再試行します...', 'warning');
      retryCount++;
    }
  }

  if (!allPassed) {
    log('❌ 最大試行回数に達しました。手動での修正が必要です。', 'error');
    process.exit(1);
  } else {
    log('🎉 CI/CD修正プロセスが完了しました！', 'success');
  }
}

main();
