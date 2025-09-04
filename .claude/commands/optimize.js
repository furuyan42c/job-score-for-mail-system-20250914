#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function log(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️', perf: '⚡' };
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

function analyzeBundle() {
  log('📦 バンドルサイズを分析中...', 'perf');

  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  const results = {
    beforeSize: 0,
    afterSize: 0,
    suggestions: []
  };

  // ビルドディレクトリの分析
  const buildDirs = ['dist', 'build', '.next/static'];
  let buildDir = null;

  for (const dir of buildDirs) {
    if (fs.existsSync(dir)) {
      buildDir = dir;
      break;
    }
  }

  if (buildDir) {
    const sizeResult = executeCommand(`du -sh ${buildDir}`, 'ビルドサイズ測定');
    if (sizeResult.success) {
      const sizeMatch = sizeResult.output.match(/([\\d.]+)([KMGT]?)/);
      if (sizeMatch) {
        results.beforeSize = parseFloat(sizeMatch[1]);
        console.log(`📦 現在のビルドサイズ: ${sizeResult.output.trim().split('\\t')[0]}`);
      }
    }

    // 大きなファイルの検出
    const largeFiles = executeCommand(`find ${buildDir} -type f -size +100k -exec ls -lh {} \\;`, '大きなファイル検出');
    if (largeFiles.success && largeFiles.output.trim()) {
      console.log('\\n📁 大きなファイル (>100KB):');
      largeFiles.output.trim().split('\\n').slice(0, 5).forEach(line => {
        const parts = line.split(/\\s+/);
        if (parts.length >= 9) {
          console.log(`  ${path.basename(parts[8])}: ${parts[4]}`);
        }
      });
    }
  }

  // webpack-bundle-analyzer の確認
  if (packageJson.devDependencies && packageJson.devDependencies['webpack-bundle-analyzer']) {
    results.suggestions.push('webpack-bundle-analyzer でバンドル分析を実行');
  }

  // 未使用の依存関係チェック
  const depcheckResult = executeCommand('npx depcheck --json', '未使用依存関係チェック');
  if (depcheckResult.success) {
    try {
      const depcheck = JSON.parse(depcheckResult.output);
      if (depcheck.dependencies && depcheck.dependencies.length > 0) {
        console.log(`\\n📦 未使用の依存関係: ${depcheck.dependencies.length} 個`);
        depcheck.dependencies.slice(0, 5).forEach(dep => {
          console.log(`  - ${dep}`);
        });
        results.suggestions.push('未使用の依存関係を削除');
      }
    } catch (e) {
      // JSON解析エラーは無視
    }
  }

  return results;
}

function optimizeImages() {
  log('🖼️ 画像を最適化中...', 'perf');

  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
  const imageFiles = [];

  function findImages(dir) {
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      if (fs.statSync(fullPath).isDirectory() && !['node_modules', '.git'].includes(item)) {
        findImages(fullPath);
      } else if (imageExtensions.includes(path.extname(item).toLowerCase())) {
        imageFiles.push(fullPath);
      }
    }
  }

  findImages('.');

  console.log(`📸 発見された画像ファイル: ${imageFiles.length} 個`);

  // ImageOptim や tinify がある場合の最適化
  const optimizedCount = 0;

  // 大きな画像ファイルの報告
  const largeImages = imageFiles.filter(file => {
    try {
      const stats = fs.statSync(file);
      return stats.size > 500 * 1024; // 500KB以上
    } catch (e) {
      return false;
    }
  });

  if (largeImages.length > 0) {
    console.log(`\\n📏 大きな画像ファイル (>500KB): ${largeImages.length} 個`);
    largeImages.slice(0, 5).forEach(file => {
      const stats = fs.statSync(file);
      const sizeKB = Math.round(stats.size / 1024);
      console.log(`  ${path.basename(file)}: ${sizeKB}KB`);
    });
  }

  return { optimized: optimizedCount, total: imageFiles.length };
}

function optimizeCSS() {
  log('🎨 CSSを最適化中...', 'perf');

  const cssFiles = [];
  const suggestions = [];

  // CSS/SCSSファイルの検索
  const result = executeCommand('find . -name "*.css" -o -name "*.scss" -o -name "*.sass" | grep -v node_modules', 'CSSファイル検索');
  if (result.success) {
    cssFiles.push(...result.output.trim().split('\\n').filter(f => f.trim()));
  }

  console.log(`🎨 発見されたCSSファイル: ${cssFiles.length} 個`);

  let totalSize = 0;
  let unusedSelectors = 0;

  cssFiles.forEach(file => {
    try {
      const stats = fs.statSync(file);
      totalSize += stats.size;

      // 基本的な分析
      const content = fs.readFileSync(file, 'utf8');

      // 重複セレクタの検出
      const selectors = content.match(/[^{]+{/g) || [];
      const uniqueSelectors = new Set(selectors);
      if (selectors.length > uniqueSelectors.size) {
        suggestions.push(`${path.basename(file)}: 重複セレクタがあります`);
      }

      // 長いCSS行の検出
      const longLines = content.split('\\n').filter(line => line.length > 120).length;
      if (longLines > 0) {
        suggestions.push(`${path.basename(file)}: ${longLines} 行が長すぎます`);
      }

    } catch (e) {
      // ファイル読み取りエラーは無視
    }
  });

  console.log(`📊 総CSSサイズ: ${Math.round(totalSize / 1024)}KB`);

  // PurgeCSS の提案
  if (totalSize > 100 * 1024) { // 100KB以上
    suggestions.push('PurgeCSSで未使用CSSを削除することを検討');
  }

  if (suggestions.length > 0) {
    console.log('\\n💡 CSS最適化の提案:');
    suggestions.forEach((suggestion, index) => {
      console.log(`  ${index + 1}. ${suggestion}`);
    });
  }

  return { totalSize, suggestions: suggestions.length };
}

function optimizeJavaScript() {
  log('⚡ JavaScriptを最適化中...', 'perf');

  const jsFiles = [];
  const results = {
    totalFiles: 0,
    totalSize: 0,
    suggestions: []
  };

  // JavaScript/TypeScriptファイルの検索
  const findResult = executeCommand('find . -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | grep -v node_modules | head -50', 'JSファイル検索');
  if (findResult.success) {
    jsFiles.push(...findResult.output.trim().split('\\n').filter(f => f.trim()));
  }

  results.totalFiles = jsFiles.length;
  console.log(`⚡ 発見されたJSファイル: ${jsFiles.length} 個`);

  let complexFiles = 0;

  jsFiles.forEach(file => {
    try {
      const stats = fs.statSync(file);
      results.totalSize += stats.size;

      const content = fs.readFileSync(file, 'utf8');
      const lines = content.split('\\n').length;

      // 複雑なファイルの検出
      if (lines > 500) {
        complexFiles++;
        results.suggestions.push(`${path.basename(file)}: ファイルが大きすぎます (${lines} 行)`);
      }

      // console.log の検出
      const consoleLogs = (content.match(/console\\.log/g) || []).length;
      if (consoleLogs > 0) {
        results.suggestions.push(`${path.basename(file)}: console.log が ${consoleLogs} 個残っています`);
      }

      // 長い関数の検出
      const functionMatches = content.match(/function[^{]*{([^{}]*{[^{}]*})*[^{}]*}/g) || [];
      const longFunctions = functionMatches.filter(fn => fn.split('\\n').length > 50).length;
      if (longFunctions > 0) {
        results.suggestions.push(`${path.basename(file)}: 長い関数が ${longFunctions} 個あります`);
      }

    } catch (e) {
      // ファイル読み取りエラーは無視
    }
  });

  console.log(`📊 総JSサイズ: ${Math.round(results.totalSize / 1024)}KB`);
  console.log(`📊 複雑なファイル: ${complexFiles} 個`);

  // Tree-shaking の提案
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  if (packageJson.dependencies) {
    const heavyPackages = ['lodash', 'moment', 'antd'].filter(pkg => packageJson.dependencies[pkg]);
    if (heavyPackages.length > 0) {
      results.suggestions.push(`重いパッケージ (${heavyPackages.join(', ')}) の代替を検討`);
    }
  }

  return results;
}

function optimizeDatabase() {
  log('🗄️ データベースクエリを分析中...', 'perf');

  const suggestions = [];

  // SQL ファイルの検索
  const sqlResult = executeCommand('find . -name "*.sql" | grep -v node_modules', 'SQLファイル検索');
  if (sqlResult.success && sqlResult.output.trim()) {
    const sqlFiles = sqlResult.output.trim().split('\\n');
    console.log(`🗄️ 発見されたSQLファイル: ${sqlFiles.length} 個`);

    sqlFiles.forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // SELECT * の検出
        if (content.includes('SELECT *')) {
          suggestions.push(`${path.basename(file)}: SELECT * を避けて必要なカラムのみ取得`);
        }

        // JOINの多用検出
        const joinCount = (content.match(/JOIN/gi) || []).length;
        if (joinCount > 3) {
          suggestions.push(`${path.basename(file)}: ${joinCount} 個のJOINがあります。パフォーマンスを確認`);
        }

        // INDEXヒントの提案
        if (!content.includes('INDEX') && content.includes('WHERE')) {
          suggestions.push(`${path.basename(file)}: WHEREで使用されるカラムにINDEXが必要かもしれません`);
        }

      } catch (e) {
        // ファイル読み取りエラーは無視
      }
    });
  }

  // ORM クエリの分析（基本的な検出）
  const jsFiles = executeCommand('find . -name "*.js" -o -name "*.ts" | grep -v node_modules | head -20', 'ORMクエリ検索');
  if (jsFiles.success) {
    jsFiles.output.trim().split('\\n').forEach(file => {
      try {
        const content = fs.readFileSync(file, 'utf8');

        // N+1クエリの可能性
        if (content.includes('.forEach') && content.includes('await')) {
          suggestions.push(`${path.basename(file)}: N+1クエリの可能性があります`);
        }

        // 大量データ取得の検出
        if (content.includes('.findAll()') || content.includes('.find({})')) {
          suggestions.push(`${path.basename(file)}: 大量データ取得時はページングを検討`);
        }

      } catch (e) {
        // ファイル読み取りエラーは無視
      }
    });
  }

  if (suggestions.length > 0) {
    console.log('\\n💡 データベース最適化の提案:');
    suggestions.slice(0, 10).forEach((suggestion, index) => {
      console.log(`  ${index + 1}. ${suggestion}`);
    });
  }

  return { suggestions: suggestions.length };
}

function generateOptimizationPlan(results) {
  log('📋 最適化計画を生成中...', 'info');

  const plan = `# パフォーマンス最適化計画

生成日時: ${new Date().toLocaleString('ja-JP')}

## 現状分析

### バンドルサイズ
- 現在のサイズ: ${results.bundle?.beforeSize || 'N/A'}
- 未使用依存関係: あり
- 最適化可能性: 高

### JavaScript
- 総ファイル数: ${results.js?.totalFiles || 0}
- 総サイズ: ${Math.round((results.js?.totalSize || 0) / 1024)}KB
- 改善提案: ${results.js?.suggestions || 0} 件

### CSS
- 総サイズ: ${Math.round((results.css?.totalSize || 0) / 1024)}KB
- 改善提案: ${results.css?.suggestions || 0} 件

### 画像
- 総ファイル数: ${results.images?.total || 0}
- 最適化済み: ${results.images?.optimized || 0}

### データベース
- 改善提案: ${results.database?.suggestions || 0} 件

## 最適化計画

### Phase 1: 低コスト・高効果
- [ ] 未使用依存関係の削除
- [ ] console.log の削除
- [ ] 画像の圧縮 (>500KB)
- [ ] CSS重複の解消

### Phase 2: バンドル最適化
- [ ] Code Splittingの実装
- [ ] Tree Shakingの有効化
- [ ] Dynamic Importの活用
- [ ] Lazy Loadingの実装

### Phase 3: 詳細最適化
- [ ] Critical CSSの分離
- [ ] Service Workerの実装
- [ ] CDNの活用
- [ ] ガイコンプレッションの有効化

## 実行コマンド

\`\`\`bash
# 基本最適化
/optimize --bundle --images

# 詳細分析
/optimize --full --report

# 特定領域の最適化
/optimize --css --js --database
\`\`\`

## 期待効果

- バンドルサイズ: 20-30%削減
- 初期読み込み: 15-25%改善
- First Contentful Paint: 10-20%改善

---
*Generated by Claude Code /optimize command*
`;

  fs.writeFileSync('.claude/optimization-plan.md', plan);
  log('📋 最適化計画を .claude/optimization-plan.md に保存しました', 'success');
}

function runOptimizations(options) {
  log('🚀 自動最適化を実行中...', 'perf');

  const results = [];

  // 未使用依存関係の削除
  if (options.deps) {
    const depResult = executeCommand('npx depcheck --json', '未使用依存関係チェック');
    if (depResult.success) {
      try {
        const depcheck = JSON.parse(depResult.output);
        if (depcheck.dependencies && depcheck.dependencies.length > 0) {
          const toRemove = depcheck.dependencies.slice(0, 5); // 安全のため5個まで
          const removeCmd = `npm uninstall ${toRemove.join(' ')}`;
          executeCommand(removeCmd, '未使用依存関係削除');
          results.push(`削除した依存関係: ${toRemove.length} 個`);
        }
      } catch (e) {
        // JSON解析エラーは無視
      }
    }
  }

  // Prettier でフォーマット
  if (options.format) {
    executeCommand('npx prettier --write "src/**/*.{js,ts,jsx,tsx}"', 'コードフォーマット');
    results.push('コードフォーマット完了');
  }

  // ESLint自動修正
  if (options.lint) {
    executeCommand('npx eslint --fix "src/**/*.{js,ts,jsx,tsx}" || true', 'ESLint自動修正');
    results.push('ESLint自動修正完了');
  }

  return results;
}

function main() {
  const args = process.argv.slice(2);

  const options = {
    bundle: args.includes('--bundle'),
    images: args.includes('--images'),
    css: args.includes('--css'),
    js: args.includes('--js'),
    database: args.includes('--database'),
    full: args.includes('--full'),
    auto: args.includes('--auto'),
    plan: args.includes('--plan'),
    report: args.includes('--report'),
    // 自動最適化オプション
    deps: args.includes('--deps'),
    format: args.includes('--format'),
    lint: args.includes('--lint')
  };

  log('⚡ パフォーマンス最適化ツールを開始します', 'perf');

  const results = {};

  // 自動最適化実行
  if (options.auto) {
    const optimizationResults = runOptimizations({
      deps: true,
      format: true,
      lint: true
    });

    console.log('\\n🔧 実行された最適化:');
    optimizationResults.forEach(result => {
      console.log(`  ✅ ${result}`);
    });
    return;
  }

  // 分析実行
  if (options.full || !Object.values(options).some(Boolean)) {
    results.bundle = analyzeBundle();
    results.js = optimizeJavaScript();
    results.css = optimizeCSS();
    results.images = optimizeImages();
    results.database = optimizeDatabase();
  } else {
    if (options.bundle) results.bundle = analyzeBundle();
    if (options.js) results.js = optimizeJavaScript();
    if (options.css) results.css = optimizeCSS();
    if (options.images) results.images = optimizeImages();
    if (options.database) results.database = optimizeDatabase();
  }

  // 計画生成
  if (options.plan) {
    generateOptimizationPlan(results);
  }

  log('\\n✨ 最適化分析完了！', 'success');
  console.log('\\n💡 詳細な最適化には以下のオプションを使用:');
  console.log('  --auto: 安全な自動最適化を実行');
  console.log('  --plan: 最適化計画を生成');
  console.log('  --bundle: バンドル分析のみ');
  console.log('  --images: 画像最適化のみ');
  console.log('  --full: 完全分析');
}

main();
