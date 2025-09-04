#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const SPECS_DIR = 'specs';

function ensureSpecsDirectory() {
  if (!fs.existsSync(SPECS_DIR)) {
    fs.mkdirSync(SPECS_DIR, { recursive: true });
  }
}

function initializeRequirements(featureName) {
  const filePath = path.join(SPECS_DIR, 'requirements.md');
  const content = `# ${featureName} - 要件定義

## 概要
${featureName}の機能について説明

## ユーザーストーリー
- ユーザーとして、〜したい
- なぜなら〜だから

## 機能要件
- [ ] 要件1
- [ ] 要件2
- [ ] 要件3

## 非機能要件
### パフォーマンス
- レスポンス時間: < 200ms

### セキュリティ
- 認証・認可が必要

### 可用性
- 稼働率: 99.9%

## 制約事項
- 制約1
- 制約2

## 受け入れ条件
- [ ] 条件1が満たされる
- [ ] 条件2が満たされる

---
*作成日: ${new Date().toISOString().split('T')[0]}*
`;

  if (fs.existsSync(filePath)) {
    const existingContent = fs.readFileSync(filePath, 'utf8');
    fs.writeFileSync(filePath, existingContent + '\n\n' + content);
    console.log(`✅ ${featureName}の要件を requirements.md に追加しました`);
  } else {
    fs.writeFileSync(filePath, content);
    console.log(`✅ requirements.md を作成し、${featureName}の要件を追加しました`);
  }
}

function initializeDesign(featureName) {
  const filePath = path.join(SPECS_DIR, 'design.md');
  const content = `# ${featureName} - 技術設計

## システム構成
\`\`\`mermaid
graph TD
    A[フロントエンド] --> B[API]
    B --> C[データベース]
\`\`\`

## API設計
### エンドポイント
- \`GET /api/${featureName.toLowerCase()}\` - 一覧取得
- \`POST /api/${featureName.toLowerCase()}\` - 作成
- \`PUT /api/${featureName.toLowerCase()}/:id\` - 更新
- \`DELETE /api/${featureName.toLowerCase()}/:id\` - 削除

### データモデル
\`\`\`typescript
interface ${featureName} {
  id: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
}
\`\`\`

## フロントエンド設計
### コンポーネント構成
- \`${featureName}List\` - 一覧表示
- \`${featureName}Form\` - 作成・編集フォーム
- \`${featureName}Detail\` - 詳細表示

### 状態管理
- React Context / Redux / Zustand

## データベース設計
### テーブル定義
\`\`\`sql
CREATE TABLE ${featureName.toLowerCase()}s (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
\`\`\`

## セキュリティ設計
- 認証: JWT
- 認可: RBAC
- データ検証: Zod/Joi

---
*作成日: ${new Date().toISOString().split('T')[0]}*
`;

  if (fs.existsSync(filePath)) {
    const existingContent = fs.readFileSync(filePath, 'utf8');
    fs.writeFileSync(filePath, existingContent + '\n\n' + content);
    console.log(`✅ ${featureName}の設計を design.md に追加しました`);
  } else {
    fs.writeFileSync(filePath, content);
    console.log(`✅ design.md を作成し、${featureName}の設計を追加しました`);
  }
}

function initializeTasks(featureName) {
  const filePath = path.join(SPECS_DIR, 'tasks.md');
  const content = `# ${featureName} - 実装タスク

## タスク一覧

### バックエンド
- [ ] **データベース**
  - [ ] マイグレーションファイル作成
  - [ ] テーブル作成
  - [ ] インデックス設定

- [ ] **API開発**
  - [ ] モデル定義
  - [ ] バリデーション設定
  - [ ] CRUD操作実装
  - [ ] エラーハンドリング

- [ ] **テスト**
  - [ ] ユニットテスト
  - [ ] 統合テスト
  - [ ] APIテスト

### フロントエンド
- [ ] **コンポーネント開発**
  - [ ] ${featureName}List コンポーネント
  - [ ] ${featureName}Form コンポーネント
  - [ ] ${featureName}Detail コンポーネント

- [ ] **状態管理**
  - [ ] Store設定
  - [ ] Action定義
  - [ ] Reducer実装

- [ ] **UI/UX**
  - [ ] レスポンシブ対応
  - [ ] ローディング状態
  - [ ] エラー表示

### インフラ・デプロイ
- [ ] **環境設定**
  - [ ] 開発環境
  - [ ] ステージング環境
  - [ ] 本番環境

- [ ] **CI/CD**
  - [ ] ビルドパイプライン
  - [ ] テスト自動化
  - [ ] デプロイ自動化

## 進捗管理
- 開始日: ${new Date().toISOString().split('T')[0]}
- 予定終了日:
- 実際終了日:

## 注意事項
- 各タスクは独立してテスト可能にする
- エラーハンドリングを忘れずに実装する
- セキュリティ要件を満たす

---
*作成日: ${new Date().toISOString().split('T')[0]}*
`;

  if (fs.existsSync(filePath)) {
    const existingContent = fs.readFileSync(filePath, 'utf8');
    fs.writeFileSync(filePath, existingContent + '\n\n' + content);
    console.log(`✅ ${featureName}のタスクを tasks.md に追加しました`);
  } else {
    fs.writeFileSync(filePath, content);
    console.log(`✅ tasks.md を作成し、${featureName}のタスクを追加しました`);
  }
}

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('使用方法: /kiro [機能名]');
    console.log('例: /kiro ユーザー管理');
    return;
  }

  const featureName = args.join(' ');

  console.log(`🚀 Kiroスタイル仕様駆動開発を開始します: ${featureName}`);
  console.log('');

  ensureSpecsDirectory();
  initializeRequirements(featureName);
  initializeDesign(featureName);
  initializeTasks(featureName);

  console.log('');
  console.log('📋 次のステップ:');
  console.log('1. specs/requirements.md で要件を詳細化');
  console.log('2. specs/design.md で設計を詳細化');
  console.log('3. specs/tasks.md でタスクを調整');
  console.log('4. 各タスクを順次実装');
}

main();
