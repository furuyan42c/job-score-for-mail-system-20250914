"""
T086: マスタデータ投入スクリプト（SQLite版）
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# データベースパス
DB_PATH = "development.db"
DATA_DIR = Path("../data")

def import_master_data():
    """マスタデータのインポート"""

    print("=" * 60)
    print("マスタデータインポート開始")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefectures (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY,
            prefecture_id INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY (prefecture_id) REFERENCES prefectures(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS occupations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seo_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            search_volume INTEGER,
            difficulty REAL
        )
    """)

    # データ投入
    try:
        # 1. 都道府県データ
        if DATA_DIR.joinpath("prefecture_view.csv").exists():
            df = pd.read_csv(DATA_DIR / "prefecture_view.csv")
            df.to_sql("prefectures", conn, if_exists="replace", index=False)
            print(f"✅ 都道府県: {len(df)}件")

        # 2. 市区町村データ
        if DATA_DIR.joinpath("city_view.csv").exists():
            df = pd.read_csv(DATA_DIR / "city_view.csv")
            # カラム名を調整
            df_cities = pd.DataFrame()
            df_cities['id'] = df['city_cd'] if 'city_cd' in df.columns else df['id']
            df_cities['prefecture_id'] = df['pref_cd'] if 'pref_cd' in df.columns else df['prefecture_id']
            df_cities['name'] = df['name']
            df_cities.to_sql("cities", conn, if_exists="replace", index=False)
            print(f"✅ 市区町村: {len(df_cities)}件")

        # 3. 職種データ
        if DATA_DIR.joinpath("occupation_view.csv").exists():
            df = pd.read_csv(DATA_DIR / "occupation_view.csv")
            df.to_sql("occupations", conn, if_exists="replace", index=False)
            print(f"✅ 職種: {len(df)}件")

        # 4. SEOキーワードデータ（T087）
        if DATA_DIR.joinpath("semrush_kw20250824_sample.csv").exists():
            df = pd.read_csv(DATA_DIR / "semrush_kw20250824_sample.csv")
            # カラム名調整
            df_seo = pd.DataFrame()
            if 'Keyword' in df.columns:
                df_seo['keyword'] = df['Keyword']
            elif 'keyword' in df.columns:
                df_seo['keyword'] = df['keyword']

            if 'Search Volume' in df.columns:
                df_seo['search_volume'] = df['Search Volume']
            elif 'volume' in df.columns:
                df_seo['search_volume'] = df['volume']

            if 'Keyword Difficulty' in df.columns:
                df_seo['difficulty'] = df['Keyword Difficulty']
            elif 'difficulty' in df.columns:
                df_seo['difficulty'] = df['difficulty']

            if not df_seo.empty:
                df_seo.to_sql("seo_keywords", conn, if_exists="replace", index=False)
                print(f"✅ SEOキーワード: {len(df_seo)}件")

        conn.commit()

        # 検証
        print("\n📊 データ検証:")
        for table in ["prefectures", "cities", "occupations", "seo_keywords"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count}件")

    except Exception as e:
        print(f"❌ エラー: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("✅ マスタデータインポート完了")
    print("=" * 60)

    return True

if __name__ == "__main__":
    import_master_data()