# バイト求人マッチングシステム 総合仕様書 v2.0
## LLM実装用詳細仕様

## 1. システム概要

### 1.1 目的
本システムは、1万人のユーザーに対して、毎日パーソナライズされたバイト求人情報をメール配信するシステムです。10万件の求人データから、各ユーザーに最適な40件を自動選定し、高いコンバージョン率を実現します。

### 1.2 主要機能
1. **求人データ収集・管理**: 外部API/CSVから求人データを日次インポート
2. **スコアリング処理**: SEMRushキーワードとLLMを活用した求人評価
3. **パーソナライゼーション**: ユーザーの応募履歴に基づく最適化
4. **メール自動生成・配信**: LLMによるキャッチーな文面生成と大量配信
5. **効果測定・分析**: 開封率、クリック率、応募率の追跡

### 1.3 技術スタック
- **開発環境**: Claude Code / Cursor（AI支援開発）
- **データベース**: Supabase (PostgreSQL 15+)
- **バックエンド**: Python 3.11+
- **非同期処理**: Celery + Redis
- **メール配信**: SendGrid / Amazon SES
- **LLM API**: OpenAI GPT-4 / Claude API
- **モニタリング**: Grafana + Prometheus
- **ログ管理**: Elasticsearch + Kibana

### 1.4 システム構成図
```
[外部求人API] → [データ収集バッチ] → [PostgreSQL]
                                         ↓
[SEMRush API] → [スコアリングバッチ] → [job_enrichment]
                                         ↓
                   [マッチングバッチ] → [user_job_mapping]
                                         ↓
                    [メール生成バッチ] → [daily_email_queue]
                                         ↓
                      [SendGrid/SES] → [ユーザー]
```

## 2. データベース設計

### 2.1 ER図
データベース設計は `/specs/ER/ER_new_modified.mmd` を参照してください。

### 2.2 主要テーブル概要

#### 2.2.1 マスターデータ
- **occupation_master**: 職種分類マスター（大中小分類）
- **prefecture_master**: 都道府県マスター
- **city_master**: 市区町村マスター（緯度経度含む）
- **employment_type_master**: 雇用形態マスター
- **salary_type_master**: 給与タイプマスター
- **feature_master**: 求人特徴マスター（マッチキーワード付き）
- **needs_category_master**: ニーズカテゴリーマスター

#### 2.2.2 求人データ
- **jobs**: 求人詳細データ（全385カラム）
- **jobs_match_raw**: マッチング用軽量データ
- **jobs_contents_raw**: 表示用コンテンツデータ
- **job_enrichment**: スコアリング結果

#### 2.2.3 キーワード・スコアリング
- **semrush_keywords**: SEMRushから取得したキーワードデータ
- **keyword_scoring**: キーワードとスコアリングルール

#### 2.2.4 ユーザー関連
- **users**: ユーザー基本情報
- **user_profiles**: ユーザープロファイル（応募傾向の集計）
- **user_actions**: ユーザー行動履歴（開封・クリック・応募）
- **user_job_mapping**: ユーザー×求人のマッピングとスコア

#### 2.2.5 配信関連
- **daily_job_picks**: 日次選定求人（LLM生成文面付き）
- **daily_email_queue**: メール配信キュー

## 3. カテゴリー分類システム詳細

### 3.1 カテゴリー分類の概要
カテゴリー分類は、10万件の求人を効率的に分類し、ユーザーのニーズに合わせて検索・マッチングを行うための重要な仕組みです。2つの軸（ニーズベース・職種ベース）で分類し、複合的な条件でユーザーに最適な求人を提供します。

### 3.2 ニーズベースカテゴリー（14種類）詳細

#### 3.2.1 カテゴリー定義と実装詳細

```python
# needs_category_masterテーブル構造
{
    "category_id": 1,
    "category_name": "日払い・週払い",
    "matching_type": "keyword",  # keyword/feature_code/salary_compare/complex
    "matching_value": "日払い,週払い,即日払い,当日払い",
    "priority": 1
}
```

##### 1. 日払い・週払い
```sql
-- 実装SQL
SELECT * FROM jobs WHERE 
  application_name ~* '(日払|週払|即日払|当日払|デイリー)' OR
  salary ~* '(日払|週払|即日払|当日払)' OR
  welfare ~* '(日払|週払|即日払|当日払)';

-- スコアブースト: 1.3倍
```

##### 2. 短期・単発OK
```sql
-- 実装SQL
SELECT * FROM jobs WHERE 
  application_name ~* '(短期|単発|1日のみ|１日のみ|スポット)' OR
  hours ~* '(短期|単発|1日のみ|１日のみ)' OR
  employment_term_cd IN (1, 2);  -- 1:単発, 2:短期

-- スコアブースト: 1.2倍
```

##### 3. 高時給（動的計算）
```python
def is_high_salary(job, area_stats):
    """地域平均より20%以上高い求人を判定"""
    area_avg = area_stats[job.pref_cd]['avg_salary']
    threshold = area_avg * 1.2
    return job.min_salary >= threshold

# 都道府県別平均時給（例）
area_salary_stats = {
    13: {"avg": 1150, "median": 1100},  # 東京都
    14: {"avg": 1050, "median": 1000},  # 神奈川県
    27: {"avg": 980, "median": 950},    # 大阪府
}

-- スコアブースト: 1.5倍
```

##### 4. シフト自由
```sql
-- 実装SQL
SELECT * FROM jobs WHERE 
  application_name ~* '(シフト自由|自由シフト|週1|週１)' OR
  hours ~* '(シフト自由|相談|週1日|週１日|自己申告)' OR
  requirement ~* '(シフト自由|週1|週１)';

-- スコアブースト: 1.2倍
```

##### 5. 未経験歓迎
```sql
-- 実装SQL
SELECT * FROM jobs WHERE 
  feature_codes ~ '\y103\y' OR  -- feature_masterの未経験歓迎コード
  inexperience_flg = true OR
  requirement ~* '(未経験|初心者|経験不問|経験なし)';

-- スコアブースト: 1.1倍
```

##### 6. 在宅・リモート
```sql
-- 実装SQL
SELECT * FROM jobs WHERE 
  application_name ~* '(在宅|リモート|テレワーク|完全在宅)' OR
  area ~* '(在宅|リモート|テレワーク|全国)' OR
  traffic = '通勤不要';

-- スコアブースト: 1.4倍
```

##### 7-14. その他カテゴリー
```python
# カテゴリー別の複合条件定義
category_conditions = {
    "学生歓迎": {
        "feature_codes": [104],
        "keywords": ["学生歓迎", "大学生", "専門学生"],
        "boost": 1.1
    },
    "高校生歓迎": {
        "age_field": "高校生OK",
        "keywords": ["高校生歓迎", "高校生可", "16歳以上"],
        "boost": 1.1
    },
    "主婦歓迎": {
        "keywords": ["主婦歓迎", "主婦活躍", "扶養内"],
        "hours_pattern": "(9:00|10:00).*(14:00|15:00)",  # 昼間時間帯
        "boost": 1.1
    },
    "シニア歓迎": {
        "keywords": ["シニア歓迎", "60歳以上", "定年後"],
        "max_age_condition": "max_age >= 60 OR max_age IS NULL",
        "boost": 1.1
    }
}
```

### 3.3 職種カテゴリー詳細

#### 3.3.1 職種階層構造
```
大分類(occupation_cd1) → 中分類(occupation_cd2) → 小分類(occupation_cd3) → 詳細(jobtype_detail)
   100                     110                      111                      5
```

#### 3.3.2 職種別スコアリング係数
```python
occupation_score_factors = {
    100: {"base": 1.2, "name": "飲食・フード系"},      # 高需要
    200: {"base": 1.1, "name": "販売・サービス"},       # 中高需要
    300: {"base": 1.3, "name": "配送・ドライバー"},     # 高需要
    400: {"base": 1.0, "name": "オフィスワーク"},       # 標準
    500: {"base": 1.4, "name": "医療・介護・保育"},     # 超高需要
    600: {"base": 1.1, "name": "軽作業・工場"},         # 中高需要
    700: {"base": 0.9, "name": "美容・理容"},           # やや低需要
    800: {"base": 1.2, "name": "教育"},                 # 高需要
    900: {"base": 1.0, "name": "エンタメ"},             # 標準
    1000: {"base": 1.1, "name": "イベント"},            # 中高需要
    1100: {"base": 1.3, "name": "IT・クリエイティブ"}, # 高需要
    1200: {"base": 0.8, "name": "その他"}               # 低需要
}
```

### 3.4 カテゴリー分類処理フロー

```python
def categorize_job(job):
    """求人のカテゴリー分類処理"""
    categories = {
        'needs': [],
        'occupation': None
    }
    
    # 1. ニーズカテゴリー判定
    for category in needs_categories:
        if check_needs_match(job, category):
            categories['needs'].append(category.name)
    
    # 2. 職種カテゴリー判定
    categories['occupation'] = get_occupation_category(job.occupation_cd1)
    
    # 3. job_enrichmentテーブルに保存
    save_enrichment(job.id, categories)
    
    return categories
```

### 3.5 カテゴリー分類の改善実装（ER図変更なし）

#### 3.5.1 拡張検索対象カラム
```python
# 検索対象カラムを拡張（既存テーブル構造のまま）
SEARCH_COLUMNS = [
    'application_name',  # 求人タイトル
    'company_name',      # 企業名
    'salary',           # 給与
    'hours',            # 勤務時間
    'welfare',          # 福利厚生（追加）
    'requirement',      # 応募条件（追加）
    'job_contents',     # 仕事内容（追加）
    'free1_contents',   # 自由項目1（追加）
    'free2_contents'    # 自由項目2（追加）
]
```

#### 3.5.2 否定パターン除外機能
```python
def check_needs_match_enhanced(job, category):
    """改善版ニーズマッチング（否定パターン考慮）"""
    
    # 否定パターン定義
    NEGATIVE_PATTERNS = [
        '不可', 'なし', 'ありません', '対応していません',
        '除く', '以外', 'NG', '×', '✕'
    ]
    
    # 検索テキスト結合
    search_text = ' '.join([
        getattr(job, col, '') for col in SEARCH_COLUMNS
    ])
    
    if category.matching_type == 'keyword':
        keywords = category.matching_value.split(',')
        
        for keyword in keywords:
            if keyword in search_text:
                # キーワード周辺の否定チェック（前後20文字）
                position = search_text.find(keyword)
                context = search_text[max(0, position-20):position+len(keyword)+20]
                
                # 否定パターンがないことを確認
                if not any(neg in context for neg in NEGATIVE_PATTERNS):
                    return True
    
    elif category.matching_type == 'feature_code':
        feature_codes = job.feature_codes.split(',') if job.feature_codes else []
        return category.matching_value in feature_codes
    
    elif category.matching_type == 'salary_compare':
        # 地域平均との比較
        return check_salary_condition(job, category.matching_value)
    
    elif category.matching_type == 'complex':
        # 複合条件（JSON形式で条件を定義）
        return check_complex_condition(job, json.loads(category.matching_value))
    
    return False
```

#### 3.5.3 複合条件判定の実装
```python
def check_complex_condition(job, conditions):
    """複合条件のチェック"""
    
    # 主婦歓迎の例
    if conditions.get('category') == '主婦歓迎':
        # キーワードチェック
        keyword_match = any(
            kw in job.application_name or kw in job.requirement 
            for kw in conditions['keywords']
        )
        
        # 勤務時間チェック（9-15時の間）
        time_match = False
        if job.hours:
            import re
            time_pattern = r'(\d{1,2}):?\d{0,2}'
            times = re.findall(time_pattern, job.hours)
            if times:
                start_hour = int(times[0])
                if 9 <= start_hour <= 10 and '15:00' in job.hours:
                    time_match = True
        
        return keyword_match and time_match
    
    # シニア歓迎の例
    elif conditions.get('category') == 'シニア歓迎':
        keyword_match = any(
            kw in job.requirement for kw in conditions['keywords']
        )
        age_match = job.max_age is None or job.max_age >= 60
        
        return keyword_match or age_match
    
    return False
```

#### 3.5.4 信頼度スコアの計算
```python
def calculate_category_confidence(job, category, match_details):
    """カテゴリーマッチの信頼度計算（0-100）"""
    
    confidence = 50  # 基本スコア
    
    # キーワードの出現回数
    if match_details.get('keyword_count'):
        confidence += min(match_details['keyword_count'] * 10, 30)
    
    # 出現位置（タイトルに含まれる場合は高スコア）
    if match_details.get('in_title'):
        confidence += 20
    
    # feature_codeでの裏付け
    if match_details.get('feature_code_match'):
        confidence = max(confidence, 90)
    
    return min(confidence, 100)
```

#### 3.5.5 優先順位を活用した主要カテゴリー選定
```python
def enhanced_categorize_job(job):
    """改善版カテゴリー分類処理"""
    
    matched_needs = []
    
    # 全カテゴリーチェック
    for category in needs_categories:
        if check_needs_match_enhanced(job, category):
            match_details = get_match_details(job, category)
            confidence = calculate_category_confidence(job, category, match_details)
            
            matched_needs.append({
                'category_name': category.category_name,
                'priority': category.priority,
                'confidence': confidence,
                'match_details': match_details
            })
    
    # 優先順位と信頼度でソート
    matched_needs.sort(key=lambda x: (-x['priority'], -x['confidence']))
    
    # job_enrichmentに保存
    enrichment_data = {
        'job_id': job.job_id,
        'needs_categories': [m['category_name'] for m in matched_needs],
        'occupation_category': str(job.occupation_cd1),
        'jobtype_detail': job.jobtype_detail,
        'score_details': json.dumps({
            'category_matches': matched_needs,
            'primary_category': matched_needs[0] if matched_needs else None
        })
    }
    
    save_to_job_enrichment(enrichment_data)
    
    return {
        'needs': matched_needs,
        'primary_need': matched_needs[0] if matched_needs else None,
        'occupation': get_occupation_category(job.occupation_cd1)
    }
```

#### 3.5.6 地域別給与統計の動的計算
```python
# 地域別給与統計を定期更新（バッチ処理）
def update_area_salary_stats():
    """地域別給与統計の更新（日次バッチ）"""
    
    query = """
    SELECT 
        pref_cd,
        salary_type_cd,
        occupation_cd1,
        AVG(min_salary) as avg_salary,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY min_salary) as median_salary,
        PERCENTILE_CONT(0.2) WITHIN GROUP (ORDER BY min_salary) as p20_salary,
        PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY min_salary) as p80_salary,
        COUNT(*) as job_count
    FROM jobs_match_raw
    WHERE 
        is_delivery = true 
        AND end_at > NOW()
        AND min_salary > 0
    GROUP BY pref_cd, salary_type_cd, occupation_cd1
    """
    
    stats = execute_query(query)
    
    # メモリキャッシュまたはRedisに保存
    cache_salary_stats(stats)
    
    return stats

def check_high_salary_category(job):
    """高時給カテゴリーの判定（動的統計使用）"""
    
    stats = get_cached_salary_stats(
        job.pref_cd, 
        job.salary_type_cd,
        job.occupation_cd1
    )
    
    if not stats:
        # 統計がない場合は都道府県全体の平均を使用
        stats = get_pref_average_stats(job.pref_cd)
    
    # 地域平均の1.2倍以上を高時給とする
    threshold = stats['avg_salary'] * 1.2
    
    return job.min_salary >= threshold
```

#### 3.5.7 バッチ処理での一括カテゴリー分類
```python
def batch_categorize_jobs():
    """全求人のカテゴリー分類バッチ処理"""
    
    # 1. 統計情報の更新
    update_area_salary_stats()
    
    # 2. カテゴリーマスター読み込み（キャッシュ）
    needs_categories = load_needs_categories()
    
    # 3. チャンク単位で処理（メモリ効率化）
    CHUNK_SIZE = 1000
    offset = 0
    
    while True:
        jobs = fetch_jobs_chunk(offset, CHUNK_SIZE)
        if not jobs:
            break
        
        # 並列処理
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(enhanced_categorize_job, jobs)
        
        # 結果を一括保存
        bulk_save_enrichments(results)
        
        offset += CHUNK_SIZE
        
    log.info(f"Categorized {offset} jobs")
```

#### 3.5.8 カテゴリーマッチングのSQL最適化
```sql
-- カテゴリー検索用の生成カラム（PostgreSQL）を活用
-- ※テーブル構造は変更せず、インデックスのみ追加

-- 全文検索用インデックス
CREATE INDEX idx_jobs_fulltext ON jobs 
USING gin(to_tsvector('japanese', 
    coalesce(application_name, '') || ' ' || 
    coalesce(job_contents, '') || ' ' ||
    coalesce(requirement, '') || ' ' ||
    coalesce(welfare, '')
));

-- カテゴリー検索クエリの例
WITH category_keywords AS (
    SELECT 
        category_id,
        category_name,
        unnest(string_to_array(matching_value, ',')) as keyword
    FROM needs_category_master
    WHERE matching_type = 'keyword'
)
SELECT 
    j.job_id,
    array_agg(DISTINCT ck.category_name) as matched_categories
FROM jobs j
JOIN category_keywords ck ON 
    to_tsvector('japanese', j.application_name || ' ' || j.job_contents) 
    @@ plainto_tsquery('japanese', ck.keyword)
GROUP BY j.job_id;
```

## 4. スコアリングシステム詳細

### 4.1 スコアリングの全体設計

#### 4.1.1 スコアリングの目的
- **求人の魅力度を定量化**: 0-999,999の範囲で数値化
- **ユーザーマッチング最適化**: パーソナライズの基礎データ
- **配信優先順位決定**: 限られた配信枠（40件）の最適配分

#### 4.1.2 スコア構成要素
```python
# スコア計算の主要コンポーネント
SCORE_COMPONENTS = {
    "keyword_match": 0.35,    # SEMRushキーワードマッチ
    "feature_score": 0.25,    # 特徴・条件スコア
    "salary_score": 0.20,     # 給与競争力スコア
    "freshness": 0.10,        # 掲載新鮮度スコア
    "location": 0.05,         # 立地利便性スコア
    "company": 0.05           # 企業評価スコア
}
```

### 4.2 キーワードマッチスコア（35%）

#### 4.2.1 SEMRushキーワード処理
```python
def process_semrush_keywords():
    """SEMRushキーワードの処理"""
    
    # 1. キーワード取得
    keywords = fetch_from_semrush_api()
    
    # 2. スコアリングルール定義
    scoring_rules = {
        "exact_match": 100,      # 完全一致
        "partial_match": 50,     # 部分一致
        "category_match": 30     # カテゴリー一致
    }
    
    return keywords, scoring_rules
```

#### 4.2.2 キーワードスコア計算
```python
def calculate_keyword_score(job, keywords_data):
    """求人のキーワードスコア計算"""
    score = 0
    matched_keywords = []
    
    # 検索対象フィールド
    search_fields = [
        job.application_name,
        job.company_name,
        job.job_contents,
        job.requirement,
        job.welfare
    ]
    
    for keyword_data in keywords_data:
        for field in search_fields:
            match_type = check_match_type(field, keyword_data)
            
            if match_type:
                # 検索ボリュームによる重み付け
                volume_weight = math.log10(keyword_data.volume + 1) / 5
                
                # 競合度による調整
                difficulty_adjust = (100 - keyword_data.keyword_difficulty) / 100
                
                # スコア計算
                keyword_score = (
                    scoring_rules[match_type] * 
                    volume_weight * 
                    difficulty_adjust
                )
                
                score += keyword_score
                matched_keywords.append({
                    "keyword": keyword_data.keyword,
                    "match_type": match_type,
                    "score": keyword_score
                })
    
    return score, matched_keywords
```

### 4.3 特徴スコア（25%）

#### 4.3.1 特徴マスターによる評価
```python
def calculate_feature_score(job):
    """求人の特徴スコア計算"""
    feature_scores = {
        100: 30,  # 学歴不問
        103: 50,  # 未経験歓迎
        104: 40,  # 学生歓迎
        201: 45,  # 交通費支給
        206: 35,  # 社員登用あり
        # ... 他の特徴コード
    }
    
    total_score = 0
    job_features = job.feature_codes.split(',')
    
    for feature_cd in job_features:
        if int(feature_cd) in feature_scores:
            total_score += feature_scores[int(feature_cd)]
    
    # 特徴数によるボーナス
    feature_count_bonus = min(len(job_features) * 5, 50)
    
    return total_score + feature_count_bonus
```

### 4.4 給与スコア（20%）

#### 4.4.1 給与競争力評価
```python
def calculate_salary_score(job, area_stats):
    """給与スコア計算"""
    
    # 1. 地域別基準値取得
    area_avg = area_stats[job.pref_cd]['avg']
    area_median = area_stats[job.pref_cd]['median']
    
    # 2. 相対給与レベル計算
    salary_ratio = job.min_salary / area_avg
    
    # 3. スコア変換（S字カーブ）
    if salary_ratio < 0.8:
        score = 20 * salary_ratio / 0.8
    elif salary_ratio < 1.2:
        score = 20 + 60 * (salary_ratio - 0.8) / 0.4
    else:
        score = 80 + 20 * min((salary_ratio - 1.2) / 0.3, 1)
    
    # 4. 給与タイプによる調整
    type_adjustments = {
        1: 1.0,   # 時給
        2: 0.9,   # 日給
        3: 0.8,   # 月給
        4: 1.1    # 歩合
    }
    
    score *= type_adjustments.get(job.salary_type_cd, 1.0)
    
    return min(score, 100)
```

### 4.5 鮮度スコア（10%）

#### 4.5.1 掲載期間による評価
```python
def calculate_freshness_score(job):
    """鮮度スコア計算"""
    
    days_since_start = (datetime.now() - job.start_at).days
    days_until_end = (job.end_at - datetime.now()).days
    
    # 新着ボーナス
    if days_since_start <= 3:
        new_bonus = 50
    elif days_since_start <= 7:
        new_bonus = 30
    elif days_since_start <= 14:
        new_bonus = 10
    else:
        new_bonus = 0
    
    # 締切間近ペナルティ
    if days_until_end <= 3:
        deadline_penalty = -30
    elif days_until_end <= 7:
        deadline_penalty = -10
    else:
        deadline_penalty = 0
    
    # 基本スコア（掲載期間による減衰）
    base_score = max(50 - days_since_start, 0)
    
    return max(base_score + new_bonus + deadline_penalty, 0)
```

### 4.6 立地スコア（5%）

#### 4.6.1 アクセス利便性評価
```python
def calculate_location_score(job):
    """立地スコア計算"""
    score = 50  # 基本スコア
    
    # 駅近ボーナス
    if job.station_cd:
        # 駅からの距離（推定）
        if "1分" in job.traffic or "駅直結" in job.traffic:
            score += 50
        elif "5分" in job.traffic:
            score += 30
        elif "10分" in job.traffic:
            score += 10
    
    # 主要駅ボーナス
    major_stations = [1130207, 1130208, 1130209]  # 新宿、渋谷、池袋
    if job.station_cd in major_stations:
        score += 20
    
    return min(score, 100)
```

### 4.7 企業スコア（5%）

#### 4.7.1 企業評価
```python
def calculate_company_score(job):
    """企業スコア計算"""
    
    # 企業実績による評価
    company_stats = get_company_stats(job.endcl_cd)
    
    score = 50  # 基本スコア
    
    # 過去の応募率
    if company_stats['application_rate'] > 0.1:
        score += 20
    
    # 手数料（信頼性指標）
    if job.fee == 0:
        score += 10
    
    # 掲載頻度（安定性）
    if company_stats['posting_frequency'] > 10:
        score += 20
    
    return min(score, 100)
```

### 4.8 最終スコア計算とブースト

#### 4.8.1 統合スコア計算
```python
def calculate_total_score(job):
    """最終スコア計算"""
    
    # 各コンポーネントスコア取得
    components = {
        'keyword': calculate_keyword_score(job),
        'feature': calculate_feature_score(job),
        'salary': calculate_salary_score(job),
        'freshness': calculate_freshness_score(job),
        'location': calculate_location_score(job),
        'company': calculate_company_score(job)
    }
    
    # 重み付け合計
    weighted_score = sum(
        components[key] * SCORE_COMPONENTS[key] 
        for key in components
    )
    
    # カテゴリーブースト適用
    category_boost = get_category_boost(job)
    
    # 最終スコア（0-999,999の範囲に正規化）
    final_score = int(weighted_score * category_boost * 1000)
    
    # スコア詳細の保存
    save_score_details(job.id, components, final_score)
    
    return final_score
```

#### 4.8.2 動的ブースト調整
```python
def apply_dynamic_boost(job, user_context=None):
    """コンテキストに応じた動的ブースト"""
    
    boost = 1.0
    
    # 時間帯ブースト（配信時間に応じて）
    current_hour = datetime.now().hour
    if 6 <= current_hour <= 9:  # 朝の通勤時間
        if "即日" in job.application_name:
            boost *= 1.3
    elif 12 <= current_hour <= 13:  # 昼休み
        if "短期" in job.application_name:
            boost *= 1.2
    elif 18 <= current_hour <= 21:  # 帰宅時間
        if "夜勤" in job.hours:
            boost *= 1.2
    
    # 曜日ブースト
    weekday = datetime.now().weekday()
    if weekday >= 5:  # 週末
        if "土日" in job.hours:
            boost *= 1.4
    
    # 季節ブースト
    month = datetime.now().month
    if month in [7, 8]:  # 夏季
        if "短期" in job.application_name or "夏" in job.application_name:
            boost *= 1.3
    elif month == 12:  # 年末
        if "年末" in job.application_name:
            boost *= 1.4
    
    return boost
```

### 4.9 スコアリング結果の保存と活用

#### 4.9.1 job_enrichmentテーブルへの保存
```python
def save_enrichment_data(job_id, score_data):
    """スコアリング結果の保存"""
    
    enrichment = {
        'job_id': job_id,
        'score': score_data['final_score'],
        'keyword_matches': json.dumps(score_data['keyword_matches']),
        'needs_categories': score_data['categories']['needs'],
        'occupation_category': score_data['categories']['occupation'],
        'jobtype_detail': score_data['jobtype_detail'],
        'score_details': json.dumps({
            'keyword_score': score_data['components']['keyword'],
            'feature_score': score_data['components']['feature'],
            'salary_score': score_data['components']['salary'],
            'freshness_score': score_data['components']['freshness'],
            'location_score': score_data['components']['location'],
            'company_score': score_data['components']['company'],
            'boost_factor': score_data['boost'],
            'calculation_time': score_data['calc_time']
        }),
        'updated_at': datetime.now()
    }
    
    # Upsert処理
    db.execute("""
        INSERT INTO job_enrichment 
        VALUES (%(job_id)s, %(score)s, ...) 
        ON CONFLICT (job_id) 
        DO UPDATE SET score = EXCLUDED.score, ...
    """, enrichment)
```

### 4.10 ユーザー行動履歴に基づくパーソナライズドマッチング

#### 4.10.1 ユーザープロファイル分析（応募データベース）
```python
def analyze_user_profile(user_id):
    """ユーザーの応募履歴から傾向を分析（応募データから開始）"""
    
    # user_profilesから応募履歴データ取得
    profile = get_user_profile(user_id)
    
    # 初回ユーザー（応募履歴1件のみ）の場合の処理
    if profile.total_applications == 1:
        return create_initial_preferences(user_id)
    
    # 文字列形式のデータをパース
    preferences = {
        'pref_weights': {},      # 都道府県の重み（応募データから推定）
        'city_weights': {},      # 市区町村の重み（応募データから推定）
        'occupation_weights': {}, # 職種の重み
        'salary_range': {},      # 給与レンジ
        'feature_weights': {},   # 特徴の重み
        'company_weights': {},   # 企業の重み
        'estimated_location': {} # 推定居住地
    }
    
    # 応募回数から重みを計算
    # 例: "13:5,14:3,11:1" → {13: 0.55, 14: 0.33, 11: 0.11}
    if profile.applied_pref_cds:
        total_apps = 0
        for item in profile.applied_pref_cds.split(','):
            pref_cd, count = item.split(':')
            count = int(count)
            preferences['pref_weights'][int(pref_cd)] = count
            total_apps += count
        
        # 正規化（合計1.0になるように）
        for pref_cd in preferences['pref_weights']:
            preferences['pref_weights'][pref_cd] /= total_apps
    
    # 最も応募が多い地域を推定居住地とする
    if preferences['pref_weights']:
        estimated_pref = max(preferences['pref_weights'], key=preferences['pref_weights'].get)
        preferences['estimated_location']['pref_cd'] = estimated_pref
    
    # 市区町村レベルの推定
    preferences['city_weights'] = parse_weighted_string(profile.applied_city_cds)
    if preferences['city_weights']:
        estimated_city = max(preferences['city_weights'], key=preferences['city_weights'].get)
        preferences['estimated_location']['city_cd'] = estimated_city
    
    # 同様に他の項目も処理
    preferences['occupation_weights'] = parse_weighted_string(profile.applied_occupation_cd1s)
    preferences['feature_weights'] = parse_weighted_string(profile.applied_feature_codes)
    
    # 給与統計から好みの範囲を推定
    if profile.applied_salary_stats:
        stats = json.loads(profile.applied_salary_stats)
        preferences['salary_range'] = {
            'min_preferred': stats.get('median', 1000) * 0.9,
            'max_preferred': stats.get('median', 1000) * 1.3,
            'avg_applied': stats.get('avg', 1200)
        }
    
    return preferences

def create_initial_preferences(user_id):
    """初回応募ユーザーの初期設定（1件の応募データから推定）"""
    
    # 最初の応募データを取得
    first_application = get_first_application(user_id)
    if not first_application:
        return get_default_preferences()
    
    preferences = {
        'pref_weights': {first_application.pref_cd: 1.0},
        'city_weights': {first_application.city_cd: 1.0},
        'occupation_weights': {first_application.occupation_cd1: 1.0},
        'salary_range': {
            'min_preferred': first_application.min_salary * 0.8,
            'max_preferred': first_application.max_salary * 1.2,
            'avg_applied': first_application.min_salary
        },
        'feature_weights': {},
        'company_weights': {},
        'estimated_location': {
            'pref_cd': first_application.pref_cd,
            'city_cd': first_application.city_cd
        },
        'is_initial': True  # 初期ユーザーフラグ
    }
    
    # 特徴コードがあれば初期重みを設定
    if first_application.feature_codes:
        for feature in first_application.feature_codes.split(','):
            preferences['feature_weights'][feature] = 1.0
    
    return preferences
```

#### 4.10.2 パーソナライズドスコア計算
```python
def calculate_personalized_score(job, user_preferences, base_score):
    """ユーザーの好みに基づくスコア調整"""
    
    # 各要素のマッチ度を計算
    scores = {
        'location': 0.0,
        'occupation': 0.0,
        'salary': 0.0,
        'features': 0.0,
        'category': 0.0
    }
    
    # 1. 地域マッチ度（最大40%の影響）
    if job.pref_cd in user_preferences['pref_weights']:
        scores['location'] += user_preferences['pref_weights'][job.pref_cd] * 0.7
    if job.city_cd in user_preferences['city_weights']:
        scores['location'] += user_preferences['city_weights'][job.city_cd] * 0.3
    
    # 2. 職種マッチ度（最大30%の影響）
    if job.occupation_cd1 in user_preferences['occupation_weights']:
        scores['occupation'] = user_preferences['occupation_weights'][job.occupation_cd1]
    
    # 3. 給与マッチ度（最大15%の影響）
    if user_preferences['salary_range']:
        salary_range = user_preferences['salary_range']
        if salary_range['min_preferred'] <= job.min_salary <= salary_range['max_preferred']:
            scores['salary'] = 1.0
        else:
            # 範囲外の場合は距離に応じて減衰
            if job.min_salary < salary_range['min_preferred']:
                ratio = job.min_salary / salary_range['min_preferred']
            else:
                ratio = salary_range['max_preferred'] / job.min_salary
            scores['salary'] = max(0, ratio)
    
    # 4. 特徴マッチ度（最大10%の影響）
    if job.feature_codes and user_preferences['feature_weights']:
        job_features = set(job.feature_codes.split(','))
        matched_weight = sum(
            user_preferences['feature_weights'].get(f, 0) 
            for f in job_features
        )
        scores['features'] = min(matched_weight, 1.0)
    
    # 5. カテゴリーマッチ度（最大5%の影響）
    # ユーザーが過去に応募した求人のカテゴリー傾向
    user_category_preference = analyze_category_preference(user_preferences)
    if job.needs_categories:
        job_categories = job.needs_categories if isinstance(job.needs_categories, list) else [job.needs_categories]
        scores['category'] = calculate_category_match(job_categories, user_category_preference)
    
    # 重み付け合計（1.0〜2.0の範囲）
    weight_factors = {
        'location': 0.4,
        'occupation': 0.3,
        'salary': 0.15,
        'features': 0.1,
        'category': 0.05
    }
    
    total_weight = 1.0 + sum(
        scores[key] * weight_factors[key] 
        for key in scores
    )
    
    # 最終スコア計算
    personalized_score = int(base_score * total_weight)
    
    # マッチ詳細を保存
    match_details = {
        'base_score': base_score,
        'location_match': scores['location'],
        'occupation_match': scores['occupation'],
        'salary_match': scores['salary'],
        'feature_match': scores['features'],
        'category_match': scores['category'],
        'total_weight': total_weight,
        'final_score': personalized_score
    }
    
    return personalized_score, match_details
```

#### 4.10.3 カテゴリーベースのフィルタリング
```python
def filter_jobs_by_user_preference(jobs, user_id):
    """ユーザーの好みに基づく求人フィルタリング"""
    
    # ユーザーの応募履歴から除外条件を生成
    exclusion_rules = generate_exclusion_rules(user_id)
    
    filtered_jobs = []
    for job in jobs:
        # 1. ハードフィルター（絶対に除外）
        if should_exclude(job, exclusion_rules):
            continue
        
        # 2. カテゴリーフィルター
        if not matches_user_categories(job, user_id):
            continue
        
        # 3. 距離フィルター（遠すぎる求人を除外）
        if not within_acceptable_distance(job, user_id):
            continue
        
        filtered_jobs.append(job)
    
    return filtered_jobs

def generate_exclusion_rules(user_id):
    """除外ルールの生成"""
    
    # user_actionsから応募したが採用されなかった求人の特徴を分析
    rejected_patterns = analyze_rejected_applications(user_id)
    
    rules = {
        'excluded_companies': [],  # 過去に不採用だった企業
        'excluded_features': [],   # マッチしない特徴
        'min_salary': None,        # 最低給与ライン
        'max_distance': None,      # 最大通勤距離
        'excluded_categories': []  # 興味のないカテゴリー
    }
    
    # 3回以上応募して全て不採用の企業は除外
    rules['excluded_companies'] = get_repeatedly_rejected_companies(user_id, threshold=3)
    
    # 一度も応募していないカテゴリーで、配信回数が多いものは除外
    rules['excluded_categories'] = get_ignored_categories(user_id)
    
    return rules
```

#### 4.10.4 求人選定アルゴリズム
```python
def select_jobs_for_user(user_id, date):
    """ユーザー向けの求人40件を選定"""
    
    # 1. ユーザープロファイル取得
    user_preferences = analyze_user_profile(user_id)
    
    # 2. スコアリング済み求人を取得（基本スコア上位1000件）
    candidate_jobs = get_high_scored_jobs(limit=1000)
    
    # 3. ユーザーの好みでフィルタリング
    filtered_jobs = filter_jobs_by_user_preference(candidate_jobs, user_id)
    
    # 4. パーソナライズドスコア計算
    personalized_jobs = []
    for job in filtered_jobs:
        p_score, match_details = calculate_personalized_score(
            job, 
            user_preferences, 
            job.score
        )
        personalized_jobs.append({
            'job': job,
            'personalized_score': p_score,
            'match_details': match_details
        })
    
    # 5. スコア順にソート
    personalized_jobs.sort(key=lambda x: -x['personalized_score'])
    
    # 6. 多様性を確保しながら40件選定
    selected_jobs = ensure_diversity(personalized_jobs[:100], limit=40)
    
    # 7. user_job_mappingに保存
    save_user_job_mappings(user_id, selected_jobs, date)
    
    return selected_jobs
```

#### 4.10.5 多様性の確保
```python
def ensure_diversity(jobs, limit=40):
    """求人の多様性を確保"""
    
    selected = []
    category_counts = {}
    occupation_counts = {}
    location_counts = {}
    
    # 制約条件
    MAX_PER_CATEGORY = 10      # 同一カテゴリーは最大10件
    MAX_PER_OCCUPATION = 15    # 同一職種は最大15件
    MAX_PER_LOCATION = 20      # 同一地域は最大20件
    
    # 上位10件は無条件で選定（高スコア保証）
    for job_data in jobs[:10]:
        selected.append(job_data)
        update_counts(job_data, category_counts, occupation_counts, location_counts)
    
    # 残り30件は多様性を考慮
    for job_data in jobs[10:]:
        if len(selected) >= limit:
            break
        
        job = job_data['job']
        
        # カテゴリー制約チェック
        categories = job.needs_categories or []
        if any(category_counts.get(cat, 0) >= MAX_PER_CATEGORY for cat in categories):
            continue
        
        # 職種制約チェック
        if occupation_counts.get(job.occupation_cd1, 0) >= MAX_PER_OCCUPATION:
            continue
        
        # 地域制約チェック
        if location_counts.get(job.pref_cd, 0) >= MAX_PER_LOCATION:
            continue
        
        selected.append(job_data)
        update_counts(job_data, category_counts, occupation_counts, location_counts)
    
    # 40件に満たない場合は制約を緩めて追加
    if len(selected) < limit:
        remaining = [j for j in jobs if j not in selected]
        selected.extend(remaining[:limit - len(selected)])
    
    return selected[:limit]
```

#### 4.10.6 配信セクション別の振り分け
```python
def assign_to_email_sections(selected_jobs, user_id):
    """選定した40件を配信セクションに振り分け"""
    
    # ユーザーの推定居住地を応募履歴から取得
    user_preferences = analyze_user_profile(user_id)
    estimated_location = user_preferences.get('estimated_location', {})
    
    sections = {
        'top5': [],           # おすすめTOP5（詳細表示）
        'area_top10': [],     # 地域別TOP10
        'local_top10': [],    # 市区町村別TOP10  
        'special_top10': [],  # お得バイトTOP10
        'remaining': []       # その他
    }
    
    # TOP5: 最高スコアの5件
    sections['top5'] = selected_jobs[:5]
    
    remaining = selected_jobs[5:]
    
    # 地域別TOP10: 最も応募が多い都道府県の求人
    if estimated_location.get('pref_cd'):
        user_pref = estimated_location['pref_cd']
        sections['area_top10'] = [
            j for j in remaining 
            if j['job'].pref_cd == user_pref
        ][:10]
    else:
        # 推定できない場合は、選定された求人の最頻出都道府県を使用
        sections['area_top10'] = get_most_common_pref_jobs(remaining)[:10]
    
    # 市区町村別TOP10: 最も応募が多い市区町村の求人
    if estimated_location.get('city_cd'):
        user_city = estimated_location['city_cd']
        sections['local_top10'] = [
            j for j in remaining 
            if j['job'].city_cd == user_city
        ][:10]
    else:
        # 推定できない場合は、都道府県内の求人から選択
        sections['local_top10'] = get_nearby_city_jobs(remaining, user_pref)[:10]
    
    # お得バイトTOP10: 特別な特典がある求人
    special_categories = ['日払い・週払い', '高時給', '未経験歓迎']
    sections['special_top10'] = [
        j for j in remaining
        if any(cat in j['job'].needs_categories for cat in special_categories)
    ][:10]
    
    # セクションタイトルの動的生成
    section_titles = generate_section_titles(estimated_location)
    
    return sections, section_titles

def generate_section_titles(estimated_location):
    """地域に応じたセクションタイトル生成"""
    
    titles = {}
    
    if estimated_location.get('pref_cd'):
        pref_name = get_prefecture_name(estimated_location['pref_cd'])
        titles['area_title'] = f"{pref_name}おすすめ求人TOP10"
    else:
        titles['area_title'] = "あなたのエリアのおすすめ求人TOP10"
    
    if estimated_location.get('city_cd'):
        city_name = get_city_name(estimated_location['city_cd'])
        titles['local_title'] = f"{city_name}で人気のバイト10選"
    else:
        titles['local_title'] = "近隣エリアで人気のバイト10選"
    
    return titles
```

## 4. バッチ処理詳細

### 4.1 データ収集バッチ (batch_01_import_jobs.py)
**実行時間**: 毎日 02:00
**処理時間目標**: 30分以内

```python
# 主要処理フロー
1. 外部API/CSVからデータ取得
2. データ検証・クレンジング
3. jobsテーブルへの一括インサート（ON CONFLICT UPDATE）
4. jobs_match_raw, jobs_contents_rawへの分割保存
5. 統計情報の更新
```

**エラーハンドリング**:
- API接続エラー: 3回リトライ後、前日データで代替
- データ不整合: 該当レコードをスキップし、ログに記録
- DB接続エラー: 5分間隔で最大10回リトライ

### 4.2 スコアリングバッチ (batch_02_scoring.py)
**実行時間**: 毎日 03:00
**処理時間目標**: 45分以内

```python
# 主要処理フロー
1. SEMRushキーワードの取得・更新
2. 各求人のスコア計算
   - キーワードマッチスコア（重み: 0.4）
   - 特徴スコア（重み: 0.3）
   - 給与スコア（重み: 0.2）
   - 鮮度スコア（重み: 0.1）
3. job_enrichmentテーブルへの保存
```

**スコア計算式**:
```python
total_score = (
    keyword_score * 0.4 +
    feature_score * 0.3 +
    salary_score * 0.2 +
    freshness_score * 0.1
) * boost_factor
```

### 4.3 マッチングバッチ (batch_03_matching.py)
**実行時間**: 毎日 04:00
**処理時間目標**: 60分以内（1万ユーザー処理）

```python
# 主要処理フロー
1. アクティブユーザーの取得
2. ユーザープロファイルの更新
3. パーソナライズドスコアの計算
4. 上位40件の選定
5. user_job_mappingへの保存
6. daily_job_picksの生成
```

**パーソナライゼーションアルゴリズム**（詳細は後述のセクション4.10参照）

### 4.4 メール生成バッチ (batch_04_email_generation.py)
**実行時間**: 毎日 05:00
**処理時間目標**: 30分以内

```python
# 主要処理フロー
1. daily_job_picksから配信対象取得
2. LLMによる文面生成
   - キャッチコピー生成
   - 求人タイトル最適化
   - 特別特典の抽出
3. メールテンプレートへの組み込み
4. daily_email_queueへの保存
```

**LLMプロンプト例**:
```python
prompt = f"""
求人情報から魅力的なメールタイトルを生成してください。
求人: {job_info}
条件:
- 20文字以内
- 具体的な数字を含める
- 緊急性を演出
- 絵文字1個まで
"""
```

### 4.5 メール配信バッチ (batch_05_send_emails.py)
**実行時間**: 毎日 06:00
**処理時間目標**: 120分以内

```python
# 主要処理フロー
1. daily_email_queueから未送信メール取得
2. SendGrid/SESへの一括送信（100件/バッチ）
3. 配信ステータスの更新
4. バウンス・配信停止処理
```

## 5. API仕様

### 5.1 内部API

#### 5.1.1 スコアリングAPI
```python
POST /api/v1/scoring/calculate
{
    "job_ids": [421505257, 421505258],
    "keyword_ids": [1, 2, 3],
    "force_recalc": false
}

Response:
{
    "status": "success",
    "results": [
        {
            "job_id": 421505257,
            "score": 104983,
            "details": {...}
        }
    ]
}
```

#### 5.1.2 マッチングAPI
```python
POST /api/v1/matching/execute
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "limit": 40,
    "date": "2024-08-29"
}

Response:
{
    "status": "success",
    "matched_jobs": [...],
    "total_score": 4199320
}
```

### 5.2 Webhook

#### 5.2.1 メール開封トラッキング
```python
POST /webhook/email/open
{
    "user_id": "...",
    "queue_id": "...",
    "timestamp": "2024-08-29T10:30:00+09:00"
}
```

#### 5.2.2 クリックトラッキング
```python
POST /webhook/email/click
{
    "user_id": "...",
    "job_id": 421505257,
    "source": "TOP5",
    "position": 1
}
```

## 6. パフォーマンス要件

### 6.1 処理速度要件
- **データインポート**: 10万件/30分（≈56件/秒）
- **スコアリング**: 10万件/45分（≈37件/秒）
- **マッチング**: 1万ユーザー×40件/60分（≈111件/秒）
- **メール生成**: 1万件/30分（≈6件/秒）
- **メール送信**: 1万件/120分（≈1.4件/秒）

### 6.2 データベース最適化
```sql
-- 必須インデックス
CREATE INDEX idx_jobs_match_raw_score ON jobs_match_raw(score DESC);
CREATE INDEX idx_jobs_match_raw_location ON jobs_match_raw(pref_cd, city_cd);
CREATE INDEX idx_job_enrichment_score ON job_enrichment(score DESC);
CREATE INDEX idx_user_actions_user_date ON user_actions(user_id, action_date DESC);
CREATE INDEX idx_user_job_mapping_user_score ON user_job_mapping(user_id, personalized_score DESC);

-- パーティショニング
CREATE TABLE user_actions_2024_08 PARTITION OF user_actions
FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
```

### 6.3 並列処理設定
```python
# Celery設定
CELERY_WORKER_CONCURRENCY = 16
CELERY_TASK_TIME_LIMIT = 3600
CELERY_TASK_SOFT_TIME_LIMIT = 3300

# バッチ処理並列化
BATCH_PARALLEL_WORKERS = 8
BATCH_CHUNK_SIZE = 1000
```

## 7. エラーハンドリング

### 7.1 エラーレベル定義
- **CRITICAL**: システム停止レベル（DB接続不可、メール配信API障害）
- **ERROR**: 機能停止レベル（LLM API障害、データ不整合）
- **WARNING**: 部分的影響（一部求人のスコアリング失敗）
- **INFO**: 通常ログ（処理件数、実行時間）

### 7.2 リトライ戦略
```python
# 指数バックオフ
retry_delays = [5, 15, 45, 135, 405]  # 秒

# API呼び出しリトライ
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=3, min=5, max=405),
    retry=retry_if_exception_type(RequestException)
)
def call_external_api():
    pass
```

### 7.3 フォールバック処理
- **LLM API障害時（メール文面生成）**: 事前生成済みテンプレート文面を使用
- **スコアリング失敗時**: 前日のスコアを使用
- **メール配信失敗時**: 代替配信サービスに切り替え

## 8. 監視・ログ要件

### 8.1 監視項目
```yaml
# Prometheusメトリクス
metrics:
  - batch_execution_time
  - batch_processed_count
  - batch_error_count
  - api_response_time
  - api_error_rate
  - db_connection_pool_usage
  - email_delivery_rate
  - user_engagement_rate
```

### 8.2 アラート設定
```yaml
alerts:
  - name: BatchExecutionDelayed
    condition: batch_execution_time > 7200
    severity: critical
    
  - name: EmailDeliveryRateLow
    condition: email_delivery_rate < 0.95
    severity: warning
    
  - name: DatabaseConnectionExhausted
    condition: db_connection_pool_usage > 0.9
    severity: error
```

### 8.3 ログ出力仕様
```python
# ログフォーマット
LOG_FORMAT = {
    "timestamp": "ISO8601",
    "level": "INFO|WARNING|ERROR|CRITICAL",
    "service": "batch|api|worker",
    "trace_id": "UUID",
    "user_id": "UUID (optional)",
    "message": "string",
    "extra": {}
}

# ログローテーション
LOG_ROTATION = {
    "when": "midnight",
    "interval": 1,
    "backup_count": 30,
    "compress": True
}
```

## 9. セキュリティ考慮事項

### 9.1 データ保護
- PII（個人識別情報）の暗号化
- メールアドレスのハッシュ化
- アクセスログの90日自動削除

### 9.2 API認証
- JWT認証の実装
- Rate Limiting（100リクエスト/分）
- IP Whitelist設定

## 10. デプロイメント手順

### 10.1 環境変数設定
```bash
# .env.production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG...
SENTRY_DSN=https://...
```

### 10.2 初期セットアップ
```bash
# データベース初期化
python manage.py migrate

# マスターデータ投入
python manage.py load_masters

# インデックス作成
python manage.py create_indexes

# バッチジョブ登録
python manage.py schedule_batches
```

### 10.3 ヘルスチェック
```python
GET /health
Response: {"status": "healthy", "db": "connected", "redis": "connected"}
```

## 11. メール配信文面テンプレート

配信文面例は元仕様書の1.4節を参照してください。主要なセクション構成：

1. **ヘッダー部**: 日付、ユーザー名、推定活動エリア（応募履歴から推定）
2. **導入文**: キャッチフレーズ、概要説明
3. **おすすめ求人TOP5**: LLM生成の魅力的な説明付き
4. **地域別TOP10**: 応募頻度の高いエリアの求人
5. **市区町村別TOP10**: 応募頻度の高い市区町村の求人
6. **お得バイトTOP10**: 特典重視求人
7. **フッター部**: 配信停止リンク、運営情報

※注: ユーザーの居住地情報は取得せず、応募履歴から活動エリアを推定して表示

## 12. 実装優先順位

### Phase 1（MVP）- 2週間
1. データベース構築
2. 求人インポートバッチ
3. 基本スコアリング
4. シンプルなメール配信

### Phase 2（機能拡張）- 2週間
1. LLMスコアリング実装
2. パーソナライゼーション
3. メール文面のLLM生成
4. クリックトラッキング

### Phase 3（最適化）- 1週間
1. パフォーマンスチューニング
2. 監視システム構築
3. A/Bテスト機能
4. 分析ダッシュボード

## 13. 開発時の注意事項

### 13.1 Claude Code実装時のポイント
- 各バッチ処理は独立したPythonスクリプトとして実装
- Supabase SDKを使用してDB接続
- 環境変数による設定管理
- 十分なログ出力とエラーハンドリング
- ユニットテストの実装（pytest使用）

### 13.2 コーディング規約
```python
# ファイル命名規則
batch_XX_機能名.py  # バッチ処理
api_機能名.py       # API実装
model_テーブル名.py # ORMモデル

# 関数命名規則
def calculate_job_score(job_id: int) -> float:
    """求人スコアを計算する"""
    pass

# クラス命名規則
class JobScoringService:
    """求人スコアリングサービス"""
    pass
```

### 13.3 テスト要件
- カバレッジ: 80%以上
- 単体テスト: 全関数
- 統合テスト: 主要フロー
- 負荷テスト: 本番相当データ量

## 14. 付録

### 14.1 用語集
- **エンドクライアント**: 実際の求人企業
- **クライアント**: 求人媒体・代理店
- **スコア**: 求人の魅力度を数値化したもの
- **パーソナライズドスコア**: ユーザー個別に最適化されたスコア

### 14.2 参考資料
- Supabase公式ドキュメント: https://supabase.com/docs
- SendGrid APIリファレンス: https://docs.sendgrid.com/
- OpenAI APIドキュメント: https://platform.openai.com/docs

### 14.3 変更履歴
- v2.0 (2024-01-XX): Claude Code向け総合仕様書作成
- v1.0 (2024-08-XX): 初版作成

---

**本仕様書に関する問い合わせ先**
- プロジェクトリーダー: [担当者名]
- 技術サポート: [メールアドレス]