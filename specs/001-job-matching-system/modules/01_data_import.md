# モジュール1: データインポート機能

## 概要
毎日10万件のバイト求人データをCSVからSupabaseにインポートする機能。

## 機能要件
- CSVファイル（100カラム以上）の読み込み
- データクレンジング（不正データのスキップ）
- Supabaseへのバッチ挿入（1000件単位）
- 重複チェック（job_id + endcl_cd）

## 技術要件
- Python 3.11+ with pandas
- Supabase Python Client
- メモリ使用量: 2GB以内
- 処理時間: 5分以内

## 入力
- /data/sample_job_data.csv

## 出力
- jobsテーブルへの10万件挿入
- インポートログ（成功/失敗件数）