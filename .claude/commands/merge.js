#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');

function log(message, type = 'info') {
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };
  console.log(`${icons[type]} ${message}`);
}

function executeCommand(command, description, exitOnError = false) {
  log(`実行中: ${description}`, 'info');
  try {
    const result = execSync(command, { encoding: 'utf8', stdio: 'pipe' });
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

function getCurrentBranch() {
  const result = executeCommand('git branch --show-current', '現在のブランチ取得');
  return result.success ? result.output.trim() : null;
}

function checkWorkingDirectory() {
  const result = executeCommand('git status --porcelain', 'ワーキングディレクトリ確認');
  return result.success && result.output.trim() === '';
}

function fetchLatest() {
  executeCommand('git fetch origin', 'リモートブランチ更新', true);
}

function checkBranchUpToDate(branch, baseBranch = 'main') {
  const result = executeCommand(`git rev-list --count ${branch}..origin/${baseBranch}`, 'ブランチ差分確認');
  if (result.success) {
    const commitsAhead = parseInt(result.output.trim());
    return commitsAhead === 0;
  }
  return false;
}

function runPreMergeChecks() {
  log('🔍 マージ前チェックを実行中...', 'info');

  // テスト実行
  const packageJson = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf8')) : {};
  const scripts = packageJson.scripts || {};

  if (scripts.test) {
    const testResult = executeCommand('npm test', 'テスト実行');
    if (!testResult.success) {
      log('テストが失敗しました。マージを中止します。', 'error');
      return false;
    }
  }

  // Lint実行
  if (scripts.lint) {
    const lintResult = executeCommand('npm run lint', 'Lint実行');
    if (!lintResult.success) {
      log('Lintエラーがあります。修正してから再度実行してください。', 'warning');
    }
  }

  // 型チェック
  if (scripts['type-check'] || fs.existsSync('tsconfig.json')) {
    const typeCommand = scripts['type-check'] ? 'npm run type-check' : 'npx tsc --noEmit';
    const typeResult = executeCommand(typeCommand, '型チェック');
    if (!typeResult.success) {
      log('型チェックエラーがあります。マージを中止します。', 'error');
      return false;
    }
  }

  return true;
}

function checkPRStatus() {
  try {
    const result = executeCommand('gh pr status', 'PR状態確認');
    if (result.success) {
      log('PR状態:', 'info');
      console.log(result.output);

      // CIが通っているかチェック
      const checksResult = executeCommand('gh pr checks', 'CI状態確認');
      if (checksResult.success && !checksResult.output.includes('✓')) {
        log('CIがまだ完了していないか失敗しています。', 'warning');
        return false;
      }
    }
  } catch (error) {
    log('GitHub CLI が利用できません。手動でPR状態を確認してください。', 'warning');
  }
  return true;
}

function createBackupBranch(currentBranch) {
  const backupBranch = `backup-${currentBranch}-${Date.now()}`;
  executeCommand(`git checkout -b ${backupBranch}`, `バックアップブランチ作成: ${backupBranch}`);
  executeCommand(`git checkout ${currentBranch}`, '元のブランチに戻る');
  return backupBranch;
}

function performMerge(targetBranch, baseBranch, options) {
  log(`🔄 ${targetBranch} を ${baseBranch} にマージ中...`, 'info');

  // バックアップ作成
  const backupBranch = options.createBackup ? createBackupBranch(targetBranch) : null;

  // ベースブランチに切り替え
  executeCommand(`git checkout ${baseBranch}`, `${baseBranch} ブランチに切り替え`, true);

  // ベースブランチを最新に更新
  executeCommand(`git pull origin ${baseBranch}`, `${baseBranch} を最新に更新`, true);

  // マージ実行
  const mergeCommand = options.squash ?
    `git merge --squash ${targetBranch}` :
    `git merge --no-ff ${targetBranch}`;

  const mergeResult = executeCommand(mergeCommand, 'マージ実行');

  if (!mergeResult.success) {
    log('マージでコンフリクトが発生しました。', 'error');
    log('コンフリクトを解決してから以下を実行してください:', 'info');
    console.log('  git add .');
    console.log('  git commit');
    console.log('  git push origin ' + baseBranch);
    return false;
  }

  // Squashマージの場合はコミット
  if (options.squash) {
    const commitMessage = options.commitMessage || `feat: merge ${targetBranch} into ${baseBranch}`;
    executeCommand(`git commit -m "${commitMessage}"`, 'Squashマージコミット');
  }

  // プッシュ
  if (options.autoPush) {
    executeCommand(`git push origin ${baseBranch}`, `${baseBranch} をプッシュ`);
  }

  if (backupBranch) {
    log(`バックアップブランチ: ${backupBranch}`, 'info');
  }

  return true;
}

function cleanupBranch(branchName, options) {
  if (options.deleteBranch) {
    executeCommand(`git branch -d ${branchName}`, `ローカルブランチ削除: ${branchName}`);

    if (options.deleteRemote) {
      executeCommand(`git push origin --delete ${branchName}`, `リモートブランチ削除: ${branchName}`);
    }
  }
}

function main() {
  const args = process.argv.slice(2);
  const targetBranch = args[0] || getCurrentBranch();
  const baseBranch = args[1] || 'main';

  const options = {
    skipChecks: args.includes('--skip-checks'),
    squash: args.includes('--squash'),
    autoPush: args.includes('--auto-push'),
    deleteBranch: args.includes('--delete-branch'),
    deleteRemote: args.includes('--delete-remote'),
    createBackup: args.includes('--backup'),
    commitMessage: args.find(arg => arg.startsWith('--message='))?.split('=')[1]
  };

  if (!targetBranch) {
    log('ブランチを取得できませんでした。', 'error');
    process.exit(1);
  }

  log(`🚀 安全なマージプロセスを開始します`, 'info');
  log(`対象ブランチ: ${targetBranch} → ${baseBranch}`, 'info');

  // 1. ワーキングディレクトリの確認
  if (!checkWorkingDirectory()) {
    log('未コミットの変更があります。先にコミットしてください。', 'error');
    process.exit(1);
  }

  // 2. リモート更新
  fetchLatest();

  // 3. ブランチが最新かチェック
  if (!checkBranchUpToDate(targetBranch, baseBranch)) {
    log(`${baseBranch} ブランチが更新されています。リベースを検討してください。`, 'warning');
  }

  // 4. マージ前チェック
  if (!options.skipChecks && !runPreMergeChecks()) {
    log('マージ前チェックが失敗しました。修正してから再実行してください。', 'error');
    process.exit(1);
  }

  // 5. PR状態確認
  if (!checkPRStatus()) {
    log('PRの状態を確認してください。', 'warning');
  }

  // 6. マージ実行
  if (performMerge(targetBranch, baseBranch, options)) {
    log('✨ マージが完了しました！', 'success');

    // 7. ブランチクリーンアップ
    cleanupBranch(targetBranch, options);

    log('🎉 すべてのプロセスが完了しました！', 'success');
  } else {
    log('❌ マージが失敗しました。', 'error');
    process.exit(1);
  }
}

main();
