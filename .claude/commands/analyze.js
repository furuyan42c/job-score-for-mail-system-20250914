#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function log(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
  console.log(`${icons[type]} ${message}`);
}

function executeCommand(command, description) {
  try {
    const result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
    return { success: true, output: result };
  } catch (error) {
    return { success: false, output: error.stdout + error.stderr };
  }
}

function analyzeProjectStructure() {
  log('📁 プロジェクト構造を分析中...', 'info');

  const structure = {};
  const stats = {
    totalFiles: 0,
    totalLines: 0,
    languages: {},
    directories: 0
  };

  function analyzeDirectory(dir, depth = 0) {
    if (depth > 3) return; // 深すぎる場合は制限

    const items = fs.readdirSync(dir);
    stats.directories++;

    for (const item of items) {
      const fullPath = path.join(dir, item);

      // 除外するディレクトリ/ファイル
      if (['.git', 'node_modules', '.next', 'dist', 'build', '.DS_Store'].includes(item)) {
        continue;
      }

      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        analyzeDirectory(fullPath, depth + 1);
      } else {
        stats.totalFiles++;
        const ext = path.extname(item);
        stats.languages[ext] = (stats.languages[ext] || 0) + 1;

        // ファイル行数カウント
        try {
          const content = fs.readFileSync(fullPath, 'utf8');
          const lines = content.split('\n').length;
          stats.totalLines += lines;
        } catch (e) {
          // バイナリファイルなど読めない場合はスキップ
        }
      }
    }
  }

  analyzeDirectory('.');

  console.log('\n📊 プロジェクト統計:');
  console.log(`  総ファイル数: ${stats.totalFiles}`);
  console.log(`  総行数: ${stats.totalLines.toLocaleString()}`);
  console.log(`  ディレクトリ数: ${stats.directories}`);

  console.log('\n🗂️ ファイル種別:');
  Object.entries(stats.languages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .forEach(([ext, count]) => {
      const percentage = ((count / stats.totalFiles) * 100).toFixed(1);
      console.log(`  ${ext || '(拡張子なし)'}: ${count} (${percentage}%)`);
    });
}

function analyzeDependencies() {
  log('📦 依存関係を分析中...', 'info');

  if (fs.existsSync('package.json')) {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const deps = packageJson.dependencies || {};
    const devDeps = packageJson.devDependencies || {};

    console.log('\n📦 パッケージ依存関係:');
    console.log(`  本番依存: ${Object.keys(deps).length}`);
    console.log(`  開発依存: ${Object.keys(devDeps).length}`);

    // 古いパッケージの検出
    const result = executeCommand('npm outdated --json', '古いパッケージ検出');
    if (result.success && result.output.trim()) {
      try {
        const outdated = JSON.parse(result.output);
        if (Object.keys(outdated).length > 0) {
          console.log('\n⚠️ 更新可能なパッケージ:');
          Object.entries(outdated).slice(0, 5).forEach(([name, info]) => {
            console.log(`  ${name}: ${info.current} → ${info.latest}`);
          });
        }
      } catch (e) {
        // JSON解析エラーは無視
      }
    }

    // 脆弱性チェック
    const auditResult = executeCommand('npm audit --json', '脆弱性チェック');
    if (auditResult.success) {
      try {
        const audit = JSON.parse(auditResult.output);
        if (audit.metadata && audit.metadata.vulnerabilities) {
          const vulns = audit.metadata.vulnerabilities;
          const total = vulns.high + vulns.moderate + vulns.low + vulns.info;
          if (total > 0) {
            console.log('\n🚨 セキュリティ脆弱性:');
            console.log(`  高: ${vulns.high}, 中: ${vulns.moderate}, 低: ${vulns.low}`);
          }
        }
      } catch (e) {
        // JSON解析エラーは無視
      }
    }
  }

  if (fs.existsSync('Cargo.toml')) {
    console.log('\n🦀 Rust プロジェクト検出');
    executeCommand('cargo tree --depth 1', 'Cargo依存関係');
  }

  if (fs.existsSync('go.mod')) {
    console.log('\n🐹 Go プロジェクト検出');
    const result = executeCommand('go list -m all', 'Go依存関係');
    if (result.success) {
      const modules = result.output.split('\n').length - 1;
      console.log(`  モジュール数: ${modules}`);
    }
  }
}

function analyzeGitHistory() {
  log('🔍 Git履歴を分析中...', 'info');

  // コミット数
  const commitResult = executeCommand('git rev-list --count HEAD', 'コミット数取得');
  if (commitResult.success) {
    console.log(`\n📈 Git統計:`);
    console.log(`  総コミット数: ${commitResult.output.trim()}`);
  }

  // 最近のコミット活動
  const recentResult = executeCommand('git log --oneline --since="1 month ago" | wc -l', '最近のコミット数');
  if (recentResult.success) {
    console.log(`  直近1ヶ月のコミット: ${recentResult.output.trim()}`);
  }

  // ブランチ数
  const branchResult = executeCommand('git branch -r | wc -l', 'リモートブランチ数');
  if (branchResult.success) {
    console.log(`  リモートブランチ数: ${branchResult.output.trim()}`);
  }

  // 主要コントリビューター
  const contributorResult = executeCommand('git shortlog -sn --since="6 months ago" | head -5', 'コントリビューター');
  if (contributorResult.success && contributorResult.output.trim()) {
    console.log('\n👥 主要コントリビューター (直近6ヶ月):');
    contributorResult.output.trim().split('\n').forEach(line => {
      console.log(`  ${line}`);
    });
  }
}

function analyzeCodeQuality() {
  log('🔍 コード品質を分析中...', 'info');

  // TypeScript型チェック
  if (fs.existsSync('tsconfig.json')) {
    const tsResult = executeCommand('npx tsc --noEmit --skipLibCheck 2>&1 | wc -l', 'TypeScript型エラー数');
    if (tsResult.success) {
      const errors = parseInt(tsResult.output.trim());
      console.log(`\n📝 TypeScript:`);
      console.log(`  型エラー数: ${errors > 1 ? errors - 1 : 0}`); // wc -lは最後に1行追加するため
    }
  }

  // ESLint
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  if (packageJson.scripts && packageJson.scripts.lint) {
    const lintResult = executeCommand('npm run lint 2>&1 | grep -c "error\\|warning" || echo 0', 'Lint問題数');
    if (lintResult.success) {
      console.log(`  Lint問題数: ${lintResult.output.trim()}`);
    }
  }

  // テストカバレッジ (もしあれば)
  if (packageJson.scripts && packageJson.scripts['test:coverage']) {
    console.log('\n🧪 テスト実行中...');
    executeCommand('npm run test:coverage', 'テストカバレッジ');
  }

  // TODO/FIXME コメント
  const todoResult = executeCommand('find . -type f \\( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \\) -not -path "./node_modules/*" -exec grep -l "TODO\\|FIXME\\|XXX" {} \\; | wc -l', 'TODO/FIXMEコメント');
  if (todoResult.success) {
    console.log(`\n📝 TODO/FIXMEがあるファイル数: ${todoResult.output.trim()}`);
  }
}

function analyzePerformance() {
  log('⚡ パフォーマンス指標を分析中...', 'info');

  if (fs.existsSync('package.json')) {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

    // バンドルサイズ分析
    if (fs.existsSync('dist') || fs.existsSync('build') || fs.existsSync('.next')) {
      const buildDir = fs.existsSync('dist') ? 'dist' :
                      fs.existsSync('build') ? 'build' : '.next';

      const sizeResult = executeCommand(`du -sh ${buildDir}`, 'ビルドサイズ');
      if (sizeResult.success) {
        console.log(`\n📦 ビルドサイズ: ${sizeResult.output.trim().split('\t')[0]}`);
      }
    }

    // 大きなファイルの検出
    const largeFilesResult = executeCommand('find . -type f -not -path "./node_modules/*" -not -path "./.git/*" -size +100k -exec ls -lh {} \\; | head -5', '大きなファイル検出');
    if (largeFilesResult.success && largeFilesResult.output.trim()) {
      console.log('\n📁 大きなファイル (>100KB):');
      largeFilesResult.output.trim().split('\n').forEach(line => {
        const parts = line.split(/\s+/);
        if (parts.length >= 9) {
          console.log(`  ${parts[8]}: ${parts[4]}`);
        }
      });
    }
  }
}

function generateReport() {
  log('📋 分析レポートを生成中...', 'info');

  const report = `# コードベース分析レポート

生成日時: ${new Date().toLocaleString('ja-JP')}

## 概要
このレポートはプロジェクトの現在の状態を分析した結果です。

## 推奨事項
- [ ] 古い依存関係の更新を検討
- [ ] セキュリティ脆弱性の修正
- [ ] テストカバレッジの向上
- [ ] TODO/FIXMEコメントの対応
- [ ] パフォーマンスの最適化

## 次のアクション
1. 脆弱性修正: \`npm audit fix\`
2. 依存関係更新: \`npm update\`
3. テスト実行: \`npm test\`
4. Lint修正: \`npm run lint --fix\`

---
*Generated by Claude Code /analyze command*
`;

  fs.writeFileSync('.claude/analysis-report.md', report);
  log('📋 分析レポートを .claude/analysis-report.md に保存しました', 'success');
}

function main() {
  const args = process.argv.slice(2);
  const options = {
    full: args.includes('--full'),
    performance: args.includes('--performance'),
    security: args.includes('--security'),
    git: args.includes('--git'),
    report: args.includes('--report')
  };

  log('🔍 コードベース分析を開始します', 'info');

  // 基本分析
  analyzeProjectStructure();

  if (options.full || !Object.values(options).some(Boolean)) {
    analyzeDependencies();
    analyzeGitHistory();
    analyzeCodeQuality();
    analyzePerformance();
  } else {
    if (options.security) analyzeDependencies();
    if (options.git) analyzeGitHistory();
    if (options.performance) analyzePerformance();
  }

  if (options.report) {
    generateReport();
  }

  log('\n✨ 分析完了！', 'success');
  console.log('\n💡 詳細な分析には以下のオプションを使用:');
  console.log('  --full: 完全分析');
  console.log('  --security: セキュリティ分析');
  console.log('  --performance: パフォーマンス分析');
  console.log('  --git: Git履歴分析');
  console.log('  --report: レポート生成');
}

main();
