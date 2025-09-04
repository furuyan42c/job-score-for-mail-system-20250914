# ER図ビューアー フロントエンド仕様書

## 1. 概要

### 1.1 目的
ER図（`ER_new_modified.mmd`）の内容をブラウザ上でSQLiteライクなインターフェースで確認できるフロントエンドアプリケーション

### 1.2 主要機能
- テーブル一覧の表示・検索
- テーブル詳細情報の表示（カラム、データ型、制約）
- リレーション（外部キー関係）の視覚化
- SQLiteデータベースブラウザ風のUI/UX

## 2. 技術スタック

### 2.1 推奨構成
- **フレームワーク**: React 18 + TypeScript
- **スタイリング**: Tailwind CSS + shadcn/ui
- **状態管理**: Zustand または Context API
- **ルーティング**: React Router v6
- **ビルドツール**: Vite
- **パーサー**: mermaid.js（ER図パース用）

## 3. 画面構成

### 3.1 メインレイアウト
```
+------------------+------------------------+
|                  |                        |
| サイドパネル      | メインビューエリア      |
| (テーブル一覧)    | (テーブル詳細/関係図)   |
|                  |                        |
+------------------+------------------------+
```

### 3.2 サイドパネル（左側）
#### 機能
- テーブル一覧表示
- リアルタイム検索フィルター
- テーブル数の表示
- カテゴリグループ表示（マスター系、トランザクション系、エンリッチメント系）

#### UI要素
```typescript
interface SidePanelProps {
  tables: Table[];
  selectedTable: string | null;
  onTableSelect: (tableName: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}
```

### 3.3 メインビューエリア（右側）
#### タブ構成
1. **Structure（構造）タブ**
   - カラム一覧
   - データ型
   - NULL許可
   - デフォルト値
   - 制約（PK, FK, UK）
   - コメント/例示値

2. **Relations（リレーション）タブ**
   - 外部キー関係一覧
   - 参照元テーブル
   - 参照先テーブル
   - カーディナリティ表示

3. **DDL タブ**
   - CREATE TABLE文の生成表示
   - コピー機能付き

## 4. データモデル

### 4.1 テーブル定義
```typescript
interface Table {
  name: string;
  columns: Column[];
  relations: Relation[];
  category: 'master' | 'transaction' | 'enrichment';
}

interface Column {
  name: string;
  type: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  isUnique: boolean;
  nullable: boolean;
  defaultValue?: string;
  comment?: string;
  example?: string;
}

interface Relation {
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
  sourceTable: string;
  sourceColumn: string;
  targetTable: string;
  targetColumn: string;
  label?: string;
}
```

## 5. 機能詳細

### 5.1 検索機能
- テーブル名での部分一致検索
- カラム名での検索（オプション）
- 大文字小文字を区別しない
- リアルタイムフィルタリング（デバウンス: 300ms）

### 5.2 テーブル詳細表示
#### カラム情報表示
| カラム名 | データ型 | NULL | デフォルト | キー | コメント |
|---------|---------|------|-----------|------|----------|
| user_id | uuid | NO | - | PK | ユーザーID |
| email | string | NO | - | UK | メールアドレス |

### 5.3 リレーション表示
- 視覚的な矢印表示
- カーディナリティ記号（1:1, 1:N, N:M）
- ホバー時の詳細情報ポップアップ

## 6. UI/UXデザイン

### 6.1 カラーテーマ
```css
/* SQLiteライクなカラーパレット */
--bg-primary: #f5f5f5;
--bg-secondary: #ffffff;
--border: #d1d5db;
--text-primary: #1f2937;
--text-secondary: #6b7280;
--accent: #3b82f6;
--pk-color: #f59e0b;
--fk-color: #10b981;
```

### 6.2 レスポンシブ対応
- モバイル: サイドパネルをドロワーメニュー化
- タブレット: サイドパネル幅を縮小
- デスクトップ: フル機能表示

## 7. パフォーマンス要件

### 7.1 初期ロード
- 3秒以内にインタラクティブ状態
- mmdファイルのパース: 500ms以内

### 7.2 検索レスポンス
- フィルタリング: 50ms以内
- スムーズなスクロール（60fps維持）

## 8. ブラウザ対応

### 8.1 対応ブラウザ
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 9. アクセシビリティ

### 9.1 キーボード操作
- Tab キーでのナビゲーション
- Arrow キーでのテーブル選択
- Ctrl/Cmd + F での検索フォーカス

### 9.2 スクリーンリーダー対応
- ARIA ラベル
- セマンティックHTML
- フォーカス管理

## 10. エラーハンドリング

### 10.1 エラー状態
- mmdファイル読み込みエラー
- パースエラー
- ネットワークエラー（オプション）

### 10.2 エラー表示
```typescript
interface ErrorState {
  type: 'load' | 'parse' | 'network';
  message: string;
  retry?: () => void;
}
```

## 11. 将来的な拡張機能

### 11.1 Phase 2
- ER図のグラフィカル表示（mermaid.js レンダリング）
- SQL実行シミュレーター
- データ辞書のエクスポート（Excel, PDF）

### 11.2 Phase 3
- 複数のER図ファイル対応
- バージョン比較機能
- コメント・アノテーション機能

## 12. ファイル構成

```
src/
├── components/
│   ├── Layout/
│   │   ├── MainLayout.tsx
│   │   ├── SidePanel.tsx
│   │   └── MainView.tsx
│   ├── Table/
│   │   ├── TableList.tsx
│   │   ├── TableDetail.tsx
│   │   ├── ColumnList.tsx
│   │   └── RelationView.tsx
│   └── Common/
│       ├── SearchBar.tsx
│       └── TabPanel.tsx
├── hooks/
│   ├── useERDiagram.ts
│   └── useTableFilter.ts
├── utils/
│   ├── mmdParser.ts
│   └── ddlGenerator.ts
├── types/
│   └── index.ts
└── App.tsx
```

## 13. 開発ガイドライン

### 13.1 コーディング規約
- ESLint + Prettier設定
- TypeScript strict mode
- コンポーネントは関数コンポーネント
- カスタムフックでロジック分離

### 13.2 テスト方針
- Unit Test: Vitest + React Testing Library
- E2E Test: Playwright（オプション）
- カバレッジ目標: 80%以上

## 14. セキュリティ考慮事項

### 14.1 データ処理
- クライアントサイドのみでの処理
- 外部APIコールなし
- ローカルストレージ使用なし（セッションストレージのみ）

### 14.2 入力検証
- 検索クエリのサニタイゼーション
- XSS対策（React標準）