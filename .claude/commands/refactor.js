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

function detectRefactoringOpportunities() {
  log('🔍 リファクタリング対象を検出中...', 'info');

  const opportunities = {
    duplicateCode: [],
    longMethods: [],
    complexFiles: [],
    unusedImports: [],
    todoComments: []
  };

  // 重複コード検出 (簡易版)
  const jscpdResult = executeCommand('npx jscpd . --threshold 5 --format json 2>/dev/null || echo "Not available"', '重複コード検出');
  if (jscpdResult.success && jscpdResult.output.includes('{')) {
    try {
      const result = JSON.parse(jscpdResult.output);
      if (result.duplicates) {
        opportunities.duplicateCode = result.duplicates.slice(0, 10);
      }
    } catch (e) {
      // JSON解析エラーは無視
    }
  }

  // 長いメソッド/関数の検出
  const longMethodResult = executeCommand('find . -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | grep -v node_modules | xargs grep -n "function\\|=>" | head -20', '長い関数検出');
  if (longMethodResult.success) {
    opportunities.longMethods = longMethodResult.output.split('\n').filter(line => line.trim());
  }

  // TODO/FIXMEコメント
  const todoResult = executeCommand('find . -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | grep -v node_modules | xargs grep -Hn "TODO\\|FIXME\\|XXX" | head -10', 'TODOコメント検出');
  if (todoResult.success) {
    opportunities.todoComments = todoResult.output.split('\n').filter(line => line.trim());
  }

  return opportunities;
}

function suggestRefactoring(filePath) {
  log(`📝 ${filePath} のリファクタリング提案を生成中...`, 'info');

  if (!fs.existsSync(filePath)) {
    log('ファイルが見つかりません', 'error');
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const suggestions = [];

  // 基本的な分析
  const stats = {
    lines: lines.length,
    functions: (content.match(/function|=>/g) || []).length,
    classes: (content.match(/class /g) || []).length,
    imports: (content.match(/import|require/g) || []).length
  };

  console.log(`\n📊 ファイル統計:`);
  console.log(`  行数: ${stats.lines}`);
  console.log(`  関数数: ${stats.functions}`);
  console.log(`  クラス数: ${stats.classes}`);
  console.log(`  インポート数: ${stats.imports}`);

  // リファクタリング提案
  if (stats.lines > 300) {
    suggestions.push('ファイルが大きすぎます。複数のファイルに分割することを検討してください。');
  }

  if (stats.functions > 10) {
    suggestions.push('関数が多すぎます。関連する関数をクラスやモジュールにまとめることを検討してください。');
  }

  // 長い行の検出
  const longLines = lines.filter((line, index) => {
    return line.length > 120;
  }).length;

  if (longLines > 5) {
    suggestions.push(`${longLines}行が120文字を超えています。行の分割を検討してください。`);
  }

  // ネストの深さチェック
  let maxNesting = 0;
  let currentNesting = 0;

  lines.forEach(line => {
    const openBraces = (line.match(/{/g) || []).length;
    const closeBraces = (line.match(/}/g) || []).length;
    currentNesting += openBraces - closeBraces;
    maxNesting = Math.max(maxNesting, currentNesting);
  });

  if (maxNesting > 4) {
    suggestions.push(`ネストが深すぎます（最大${maxNesting}層）。関数の分割やガード句の使用を検討してください。`);
  }

  if (suggestions.length > 0) {
    console.log('\n💡 リファクタリング提案:');
    suggestions.forEach((suggestion, index) => {
      console.log(`  ${index + 1}. ${suggestion}`);
    });
  } else {
    log('良い状態のコードです！', 'success');
  }
}

function autoRefactor(filePath, options = {}) {
  log(`🔧 ${filePath} の自動リファクタリングを実行中...`, 'info');

  if (!fs.existsSync(filePath)) {
    log('ファイルが見つかりません', 'error');
    return false;
  }

  const backupPath = `${filePath}.backup.${Date.now()}`;
  fs.copyFileSync(filePath, backupPath);
  log(`バックアップを作成: ${backupPath}`, 'info');

  let content = fs.readFileSync(filePath, 'utf8');
  let refactored = false;

  // 基本的な自動修正
  if (options.fixWhitespace) {
    // 末尾の空白削除
    const newContent = content.replace(/[ \t]+$/gm, '');
    if (newContent !== content) {
      content = newContent;
      refactored = true;
      log('末尾の空白を削除', 'success');
    }
  }

  if (options.fixSemicolons && (filePath.endsWith('.js') || filePath.endsWith('.ts'))) {
    // セミコロンの統一（簡易版）
    const newContent = content.replace(/([^;])\n/g, '$1;\n');
    if (newContent !== content) {
      content = newContent;
      refactored = true;
      log('セミコロンを統一', 'success');
    }
  }

  if (options.fixQuotes) {
    // クォートの統一（シングルクォートに）
    const newContent = content.replace(/\"([^\"]*)\"/g, "'$1'");
    if (newContent !== content) {
      content = newContent;
      refactored = true;
      log('クォートをシングルクォートに統一', 'success');
    }
  }

  if (refactored) {
    fs.writeFileSync(filePath, content);
    log('自動リファクタリング完了', 'success');

    // Prettierがあれば実行
    const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
    if (packageJson.devDependencies && packageJson.devDependencies.prettier) {
      executeCommand(`npx prettier --write ${filePath}`, 'Prettier実行');
    }

    return true;
  } else {
    fs.unlinkSync(backupPath);
    log('リファクタリングする箇所が見つかりませんでした', 'info');
    return false;
  }
}

function extractMethod(filePath, startLine, endLine, methodName) {
  log(`🔧 メソッド抽出: ${methodName}`, 'info');

  if (!fs.existsSync(filePath)) {
    log('ファイルが見つかりません', 'error');
    return false;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');

  if (startLine < 1 || endLine > lines.length || startLine > endLine) {
    log('無効な行範囲です', 'error');
    return false;
  }

  const backupPath = `${filePath}.backup.${Date.now()}`;
  fs.copyFileSync(filePath, backupPath);

  // 抽出する行を取得
  const extractedLines = lines.slice(startLine - 1, endLine);
  const extractedCode = extractedLines.join('\n');

  // 新しいメソッドを作成
  const newMethod = `\n  ${methodName}() {\n${extractedCode.replace(/^/gm, '    ')}\n  }\n`;

  // 元のコードを置換
  lines.splice(startLine - 1, endLine - startLine + 1, `    this.${methodName}();`);

  // メソッドを挿入（クラスの最後に）
  let insertIndex = lines.length - 1;
  for (let i = lines.length - 1; i >= 0; i--) {
    if (lines[i].includes('}') && lines[i - 1] && lines[i - 1].trim() !== '') {
      insertIndex = i;
      break;
    }
  }

  lines.splice(insertIndex, 0, newMethod);

  fs.writeFileSync(filePath, lines.join('\n'));
  log(`メソッド「${methodName}」を抽出しました`, 'success');
  log(`バックアップ: ${backupPath}`, 'info');

  return true;
}

function generateRefactoringPlan(directory = '.') {
  log('📋 リファクタリング計画を生成中...', 'info');

  const opportunities = detectRefactoringOpportunities();

  const plan = `# リファクタリング計画

生成日時: ${new Date().toLocaleString('ja-JP')}

## 検出された問題

### 🔄 重複コード
${opportunities.duplicateCode.length > 0 ?
  opportunities.duplicateCode.map(d => `- ${d.firstFile?.name || 'Unknown'}: ${d.lines || 0} 行`).join('\n') :
  '検出されませんでした'}

### 📝 TODO/FIXME コメント
${opportunities.todoComments.length > 0 ?
  opportunities.todoComments.map(c => `- ${c}`).join('\n') :
  '検出されませんでした'}

## リファクタリング計画

### フェーズ1: コード品質向上
- [ ] ESLint/Prettierの設定と実行
- [ ] 未使用インポートの削除
- [ ] TODO/FIXMEコメントの対応

### フェーズ2: 構造の改善
- [ ] 重複コードの統合
- [ ] 長い関数の分割
- [ ] クラスの責任分割

### フェーズ3: パフォーマンス最適化
- [ ] 不要な再レンダリングの防止
- [ ] バンドルサイズの最適化
- [ ] 非同期処理の改善

## 実行コマンド

\`\`\`bash
# 基本的な修正
/refactor --auto --file=src/component.js

# メソッド抽出
/refactor --extract-method --file=src/service.js --start=10 --end=20 --name=processData

# ディレクトリ全体の分析
/refactor --analyze --dir=src/
\`\`\`

---
*Generated by Claude Code /refactor command*
`;

  fs.writeFileSync('.claude/refactoring-plan.md', plan);
  log('📋 リファクタリング計画を .claude/refactoring-plan.md に保存しました', 'success');
}

function main() {
  const args = process.argv.slice(2);

  const options = {
    analyze: args.includes('--analyze'),
    auto: args.includes('--auto'),
    extractMethod: args.includes('--extract-method'),
    file: args.find(arg => arg.startsWith('--file='))?.split('=')[1],
    dir: args.find(arg => arg.startsWith('--dir='))?.split('=')[1] || '.',
    startLine: parseInt(args.find(arg => arg.startsWith('--start='))?.split('=')[1]) || 1,
    endLine: parseInt(args.find(arg => arg.startsWith('--end='))?.split('=')[1]) || 1,
    methodName: args.find(arg => arg.startsWith('--name='))?.split('=')[1] || 'extractedMethod',
    fixWhitespace: args.includes('--fix-whitespace'),
    fixSemicolons: args.includes('--fix-semicolons'),
    fixQuotes: args.includes('--fix-quotes'),
    plan: args.includes('--plan')
  };

  log('🔧 リファクタリングツールを開始します', 'info');

  if (options.plan) {
    generateRefactoringPlan(options.dir);
    return;
  }

  if (options.analyze) {
    if (options.file) {
      suggestRefactoring(options.file);
    } else {
      const opportunities = detectRefactoringOpportunities();
      console.log('\n🔍 検出されたリファクタリング対象:');
      console.log(`重複コード: ${opportunities.duplicateCode.length} 箇所`);
      console.log(`TODOコメント: ${opportunities.todoComments.length} 箇所`);
    }
    return;
  }

  if (options.extractMethod && options.file) {
    extractMethod(options.file, options.startLine, options.endLine, options.methodName);
    return;
  }

  if (options.auto && options.file) {
    autoRefactor(options.file, {
      fixWhitespace: options.fixWhitespace || true,
      fixSemicolons: options.fixSemicolons,
      fixQuotes: options.fixQuotes
    });
    return;
  }

  // デフォルトの動作
  log('使用方法:', 'info');
  console.log('  /refactor --analyze --file=path/to/file.js  # ファイル分析');
  console.log('  /refactor --auto --file=path/to/file.js     # 自動リファクタリング');
  console.log('  /refactor --extract-method --file=path/to/file.js --start=10 --end=20 --name=newMethod');
  console.log('  /refactor --plan                            # リファクタリング計画生成');
}

main();
