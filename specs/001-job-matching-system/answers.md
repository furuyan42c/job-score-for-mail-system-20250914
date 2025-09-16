# 📚 実装ガイド: バイト求人マッチングシステム - 全質問への回答

**作成日**: 2025-09-16  
**目的**: asks.md の全質問に対する実装可能な具体的回答  
**制約**: ユーザー情報は応募データとメールアドレスのみ（住所等のパーソナル情報なし）

## 🔴 優先度: 高（実装ブロッカー）の回答

### 1. スコアリングアルゴリズムの詳細

#### 1.1 基礎スコア計算式

```python
# 求人フィルタリング設定
VALID_EMPLOYMENT_TYPE_CDS = [1, 3,6,8]  # 1=アルバイト、 3=パートのみ（employment_type_view.csvより）
MIN_FEE_THRESHOLD = 500  # 500円以下のfeeは除外

def filter_jobs(jobs_df):
    """
    求人データのフィルタリング
    """
    # employment_type_cdでフィルタ
    filtered = jobs_df[jobs_df['employment_type_cd'].isin(VALID_EMPLOYMENT_TYPE_CDS)]
    
    # fee > 500でフィルタ（feeカラムが存在する場合）
    if 'fee' in filtered.columns:
        filtered = filtered[filtered['fee'] > MIN_FEE_THRESHOLD]
    
    return filtered

def calculate_basic_score(job, area_stats, company_popularity):
    """
    基礎スコアを0-100の範囲で計算
    福利厚生とアクセスを削除、feeを追加
    """
    # fee が500円以下の求人はスコア0
    if hasattr(job, 'fee') and job.fee <= MIN_FEE_THRESHOLD:
        return 0
    
    # 各要素を0-100に正規化
    # min_salaryとmax_salaryの平均を時給として使用
    avg_wage = (job.min_salary + job.max_salary) / 2 if job.min_salary and job.max_salary else 1200
    hourly_wage_score = normalize_hourly_wage(avg_wage, area_stats)
    fee_score = normalize_fee(job.fee)
    popularity_score = calculate_company_popularity_score(job.endcl_cd, company_popularity)
    
    # 加重平均で計算（3要素）
    basic_score = (
        hourly_wage_score * 0.40 +    # 時給
        fee_score * 0.30 +             # 応募単価報酬
        popularity_score * 0.30        # 企業人気度（endcl_cdベース）
    )
    
    return min(100, max(0, basic_score))

def normalize_hourly_wage(wage, area_stats):
    """時給の正規化（エリア平均を基準に）"""
    area_avg = area_stats['avg_salary']  # min_salary/max_salaryの平均
    area_std = area_stats['std_salary']
    
    # z-scoreを使って正規化し、0-100に変換
    z_score = (wage - area_avg) / area_std if area_std > 0 else 0
    # z-score -2 to +2 を 0 to 100 にマップ
    return min(100, max(0, (z_score + 2) * 25))

def normalize_fee(fee):
    """
    応募単価報酬（fee）の正規化
    500円以下は0点、5000円以上は100点
    """
    if fee <= 500:
        return 0
    elif fee >= 5000:
        return 100
    else:
        # 500-5000円を0-100にリニアマッピング
        return (fee - 500) / (5000 - 500) * 100

def calculate_company_popularity_score(endcl_cd, company_popularity):
    """
    企業人気度スコア（endcl_cdベース、360日データ）
    """
    if endcl_cd not in company_popularity:
        return 30  # デフォルト中間スコア
    
    stats = company_popularity[endcl_cd]
    
    # 360日間の応募率で判定
    application_rate = stats['applications_360d'] / max(1, stats['views_360d'])
    
    if application_rate >= 0.15:  # 15%以上が応募
        return 100
    elif application_rate >= 0.10:  # 10%以上
        return 80
    elif application_rate >= 0.05:  # 5%以上
        return 60
    elif application_rate >= 0.02:  # 2%以上
        return 40
    else:
        return 20

def calculate_editorial_popularity_score(job, user_location):
    """
    編集部おすすめ用の人気度スコア（fee × 応募クリック数）
    """
    # feeスコア
    if hasattr(job, 'fee'):
        fee_score = normalize_fee(job.fee)
    else:
        fee_score = 30
    
    # 応募クリック数スコア（recent_applicationsを使用）
    if hasattr(job, 'recent_applications'):
        click_score = min(100, job.recent_applications * 2)  # 応募1件=2点
    else:
        click_score = 30
    
    # 地域重み付け
    location_weight = get_location_weight(job, user_location)
    
    # 総合スコア
    return (fee_score * 0.5 + click_score * 0.5) * location_weight

def get_location_weight(job, user_location):
    """
    地域による重み付け
    市区町村: 1.0、周辺市区町村: 0.7、同じ都道府県: 0.5、それ以外: 0.3
    """
    if not user_location:
        return 1.0
    
    # 市区町村が完全一致
    if hasattr(job, 'city_cd') and job.city_cd == user_location.get('city_cd'):
        return 1.0
    
    # 周辺市区町村（簡易判定：同じ都道府県内の近いコード）
    if hasattr(job, 'city_cd') and user_location.get('nearby_cities'):
        if job.city_cd in user_location['nearby_cities']:
            return 0.7
    
    # 同じ都道府県
    if hasattr(job, 'pref_cd') and job.pref_cd == user_location.get('pref_cd'):
        return 0.5
    
    # それ以外
    return 0.3

def prepare_company_popularity_data(user_actions_df):
    """
    過去360日のuser_actionsからendcl_cd別の人気度を計算
    """
    from datetime import datetime, timedelta
    
    # 360日前の日付
    cutoff_date = datetime.now() - timedelta(days=360)
    
    # 期間内のデータをフィルタ
    recent_actions = user_actions_df[user_actions_df['action_date'] >= cutoff_date]
    
    # endcl_cd別に集計
    company_stats = recent_actions.groupby('endcl_cd').agg({
        'action_id': 'count',  # 総アクション数
        'user_id': lambda x: x[recent_actions.loc[x.index, 'action_type'] == 'applied'].nunique(),  # 応募ユーザー数
    }).rename(columns={
        'action_id': 'views_360d',
        'user_id': 'applications_360d'
    })
    
    return company_stats.to_dict('index')
```

#### 1.2 SEOスコアのマッチングロジック

```python
def preprocess_semrush_keywords(semrush_df):
    """
    SEMRUSHキーワードの前処理と加工
    """
    processed_keywords = []
    
    for _, row in semrush_df.iterrows():
        keyword = row['keyword'].lower()
        
        # キーワードの分解と正規化
        # 例: "コンビニ バイト" → ["コンビニ", "バイト", "コンビニバイト"]
        parts = keyword.split()
        variations = [
            keyword,  # 元のキーワード
            ''.join(parts),  # スペースなし版
            ' '.join(parts),  # スペースあり版
        ]
        
        # 各バリエーションを登録
        for var in variations:
            if var:  # 空文字列を除外
                processed_keywords.append({
                    'original': row['keyword'],
                    'processed': var,
                    'volume': row['volume'],
                    'difficulty': row.get('keyword_difficulty', 50),
                    'intent': row.get('intent', 'Informational')
                })
    
    return pd.DataFrame(processed_keywords)

# フィールドごとのSEOスコア重み定義
FIELD_WEIGHT_CONFIG = {
    'application_name': 1.5,    # 高い重み
    'company_name': 1.5,        # 高い重み
    'catch_copy': 1.0,          # 標準的な重み
    'salary': 0.3,              # 小さい重み
    'hours': 0.3,               # 小さい重み
    'features': 0.7,            # 中程度の重み
    'station_name_eki': 0.5     # 中程度の重み
}

def calculate_seo_score(job, processed_keywords_df):
    """
    SEOスコアの計算（フィールドごとの重み付け対応）
    """
    seo_score = 0
    matched_keywords = []
    
    # 全角・半角を統一する関数
    import unicodedata
    def normalize_text(text):
        if text is None:
            return ''
        return unicodedata.normalize('NFKC', str(text)).lower()
    
    # 各フィールドのテキストを準備
    field_texts = {}
    for field_name in FIELD_WEIGHT_CONFIG.keys():
        if hasattr(job, field_name):
            field_texts[field_name] = normalize_text(getattr(job, field_name))
    
    # キーワードマッチングとスコア計算
    for _, keyword_row in processed_keywords_df.iterrows():
        keyword = keyword_row['processed']
        matched = False
        max_field_score = 0
        matched_field = None
        
        # 各フィールドでキーワードをチェック
        for field_name, field_text in field_texts.items():
            if keyword in field_text:
                # 検索ボリュームと意図に応じた基本スコア
                volume = keyword_row['volume']
                intent = keyword_row['intent']
                
                # 基本スコア（ボリュームベース）
                if volume >= 10000:
                    base_score = 15
                elif volume >= 5000:
                    base_score = 10
                elif volume >= 1000:
                    base_score = 7
                elif volume >= 500:
                    base_score = 5
                else:
                    base_score = 3
                
                # 検索意図による調整
                intent_multiplier = {
                    'Commercial': 1.5,  # 商用意図は高価値
                    'Transactional': 1.3,  # 取引意図も価値高
                    'Informational': 1.0,  # 情報意図は標準
                    'Navigational': 0.8  # ナビゲーション意図は低め
                }.get(intent, 1.0)
                
                # フィールド重みを適用
                field_weight = FIELD_WEIGHT_CONFIG.get(field_name, 1.0)
                field_score = base_score * intent_multiplier * field_weight
                
                # 最も高いスコアのフィールドを採用
                if field_score > max_field_score:
                    max_field_score = field_score
                    matched_field = field_name
                    matched = True
        
        if matched:
            seo_score += max_field_score
            matched_keywords.append({
                'keyword': keyword_row['original'],
                'volume': keyword_row['volume'],
                'score': max_field_score,
                'matched_field': matched_field  # マッチしたフィールドを記録
            })
            
            # 最大7個のキーワードまで
            if len(matched_keywords) >= 7:
                break
    
    # 最大100点に正規化
    return min(100, seo_score), matched_keywords

def save_keyword_scoring(job_id, matched_keywords, processed_keywords_df):
    """
    keyword_scoringテーブルへのデータ保存（マッチフィールド情報付き）
    """
    scoring_records = []
    
    for match in matched_keywords:
        # 元のキーワードIDを取得
        original_keyword = processed_keywords_df[
            processed_keywords_df['original'] == match['keyword']
        ].iloc[0] if not processed_keywords_df[
            processed_keywords_df['original'] == match['keyword']
        ].empty else None
        
        if original_keyword is not None:
            scoring_records.append({
                'job_id': job_id,
                'keyword_id': original_keyword.get('keyword_id'),
                'processed_keyword': match['keyword'],
                'base_score': match['score'],
                'matched_field': match.get('matched_field', ''),  # マッチしたフィールド
                'field_weight': FIELD_WEIGHT_CONFIG.get(match.get('matched_field', ''), 1.0),  # 適用された重み
                'processed_at': datetime.now()
            })
    
    return scoring_records
```

#### 1.3 パーソナライズスコアの実数計算

```python
def calculate_personalized_score(job, user_profile):
    """
    user_profilesテーブルのデータに基づいた実数計算によるパーソナライズスコア
    協調フィルタリングではなく、ユーザーの過去の応募傾向との類似度で計算
    """
    if user_profile is None or user_profile.total_applications == 0:
        return 50  # デフォルトスコア（応募履歴がない場合）
    
    score_components = []
    weights = []
    
    # 1. 都道府県マッチング（applied_pref_cds）
    if user_profile.applied_pref_cds:
        pref_matches = calculate_location_match_score(
            job.pref_cd, 
            parse_frequency_string(user_profile.applied_pref_cds)
        )
        score_components.append(pref_matches)
        weights.append(0.20)
    
    # 2. 市区町村マッチング（applied_city_cds）
    if user_profile.applied_city_cds:
        city_matches = calculate_location_match_score(
            job.city_cd,
            parse_frequency_string(user_profile.applied_city_cds)
        )
        score_components.append(city_matches)
        weights.append(0.15)
    
    # 3. 職種大分類マッチング（applied_occupation_cd1s）
    if user_profile.applied_occupation_cd1s:
        occupation_matches = calculate_category_match_score(
            job.occupation_cd1,
            parse_frequency_string(user_profile.applied_occupation_cd1s)
        )
        score_components.append(occupation_matches)
        weights.append(0.20)
    
    # 4. 雇用形態マッチング（applied_employment_type_cds）
    if user_profile.applied_employment_type_cds:
        employment_matches = calculate_category_match_score(
            job.employment_type_cd,
            parse_frequency_string(user_profile.applied_employment_type_cds)
        )
        score_components.append(employment_matches)
        weights.append(0.10)
    
    # 5. 給与タイプマッチング（applied_salary_type_cds）
    if user_profile.applied_salary_type_cds:
        salary_type_matches = calculate_category_match_score(
            job.salary_type_cd,
            parse_frequency_string(user_profile.applied_salary_type_cds)
        )
        score_components.append(salary_type_matches)
        weights.append(0.10)
    
    # 6. 給与レンジマッチング（applied_salary_stats）
    if user_profile.applied_salary_stats:
        salary_stats = json.loads(user_profile.applied_salary_stats)
        salary_matches = calculate_salary_range_match(
            job.min_salary,
            job.max_salary,
            salary_stats
        )
        score_components.append(salary_matches)
        weights.append(0.15)
    
    # 7. エンドクライアント重複チェック（applied_endcl_cds）
    # 同じ企業への応募を抑制するためのネガティブスコア
    if user_profile.applied_endcl_cds:
        endcl_matches = calculate_exact_match_score(
            job.endcl_cd,
            parse_frequency_string(user_profile.applied_endcl_cds)
        )
        score_components.append(endcl_matches)
        weights.append(0.15)  # 重複抑制の重要度を上げる
    
    # 重み付き平均を計算
    if score_components:
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(score_components, weights))
        final_score = (weighted_score / total_weight) if total_weight > 0 else 50
    else:
        final_score = 50
    
    return min(100, max(0, final_score))

def parse_frequency_string(freq_str):
    """
    頻度文字列をパース
    例: "13:5,14:3,11:1" → {13: 5, 14: 3, 11: 1}
    """
    if not freq_str:
        return {}
    
    result = {}
    for item in freq_str.split(','):
        if ':' in item:
            code, count = item.split(':')
            try:
                result[int(code)] = int(count)
            except ValueError:
                continue
    return result

def calculate_location_match_score(job_value, user_frequencies):
    """
    地域マッチングスコア計算
    """
    if not user_frequencies:
        return 50
    
    total_count = sum(user_frequencies.values())
    if job_value in user_frequencies:
        # この地域への応募割合を計算
        ratio = user_frequencies[job_value] / total_count
        # 0-100にスケール（最大50%の応募率で100点）
        return min(100, ratio * 200)
    else:
        # 未応募地域は低スコア
        return 20

def calculate_category_match_score(job_value, user_frequencies):
    """
    カテゴリマッチングスコア計算
    """
    if not user_frequencies:
        return 50
    
    total_count = sum(user_frequencies.values())
    if job_value in user_frequencies:
        ratio = user_frequencies[job_value] / total_count
        # カテゴリは地域より重要度を高く
        return min(100, ratio * 250)
    else:
        return 30

def calculate_salary_range_match(job_min, job_max, user_stats):
    """
    給与レンジマッチングスコア計算
    """
    if not user_stats:
        return 50
    
    user_avg = user_stats.get('avg', 1200)
    user_min = user_stats.get('min', 1000)
    user_max = user_stats.get('max', 2000)
    
    job_avg = (job_min + job_max) / 2
    
    # ユーザーの好む給与レンジとの距離を計算
    if user_min <= job_avg <= user_max:
        # 範囲内は高スコア
        distance_from_avg = abs(job_avg - user_avg)
        max_distance = max(user_avg - user_min, user_max - user_avg)
        if max_distance > 0:
            score = 100 - (distance_from_avg / max_distance * 50)
        else:
            score = 100
    else:
        # 範囲外は距離に応じて減点
        if job_avg < user_min:
            distance = user_min - job_avg
        else:
            distance = job_avg - user_max
        
        # 500円離れるごとに10点減点
        score = max(20, 70 - (distance / 500 * 10))
    
    return score

def calculate_exact_match_score(job_value, user_frequencies):
    """
    完全一致スコア計算（企業コード）
    バイトでは同じ企業への重複応募を抑制
    """
    if not user_frequencies:
        return 50
    
    if job_value in user_frequencies:
        # 過去に応募済みの企業は低スコア（重複応募を避ける）
        repeat_count = user_frequencies[job_value]
        if repeat_count >= 3:
            return 10  # 3回以上応募済み：最低スコア
        elif repeat_count == 2:
            return 20  # 2回応募済み：低スコア
        else:
            return 30  # 1回応募済み：やや低スコア
    else:
        return 70  # 未応募の企業：高スコア（新しい企業を推奨）

# user_profilesテーブルの更新処理
def update_user_profiles(user_actions_df):
    """
    user_actionsからuser_profilesを計算・更新
    """
    profiles = []
    
    for user_id in user_actions_df['user_id'].unique():
        user_actions = user_actions_df[user_actions_df['user_id'] == user_id]
        
        # 応募アクションのみをフィルタ
        applications = user_actions[user_actions['action_type'] == 'applied']
        
        if len(applications) > 0:
            profile = {
                'user_id': user_id,
                'applied_pref_cds': format_frequency_dict(applications['pref_cd'].value_counts()),
                'applied_city_cds': format_frequency_dict(applications['city_cd'].value_counts()),
                'applied_occupation_cd1s': format_frequency_dict(applications['occupation_cd1'].value_counts()),
                'applied_occupation_cd2s': format_frequency_dict(applications['occupation_cd2'].value_counts()),
                'applied_occupation_cd3s': format_frequency_dict(applications['occupation_cd3'].value_counts()),
                'applied_jobtype_details': format_frequency_dict(applications['jobtype_detail'].value_counts()),
                'applied_employment_type_cds': format_frequency_dict(applications['employment_type_cd'].value_counts()),
                'applied_salary_type_cds': format_frequency_dict(applications['salary_type_cd'].value_counts()),
                'applied_salary_stats': json.dumps({
                    'min': applications['min_salary'].min(),
                    'max': applications['max_salary'].max(),
                    'avg': applications[['min_salary', 'max_salary']].mean().mean(),
                    'median': applications[['min_salary', 'max_salary']].median().median()
                }),
                'applied_station_cds': format_frequency_dict(applications['station_cd'].value_counts()),
                'applied_feature_codes': format_frequency_dict(
                    pd.Series([f for features in applications['feature_codes'].str.split(',') 
                              for f in features if f]).value_counts()
                ),
                'applied_endcl_cds': format_frequency_dict(applications['endcl_cd'].value_counts()),
                'total_applications': len(applications),
                'avg_applied_fee': applications['fee'].mean(),
                'first_application_at': applications['action_date'].min(),
                'last_application_at': applications['action_date'].max(),
                'profile_updated_at': datetime.now()
            }
            profiles.append(profile)
    
    return profiles

def format_frequency_dict(value_counts):
    """
    value_countsを頻度文字列にフォーマット
    例: {13: 5, 14: 3} → "13:5,14:3"
    """
    if value_counts.empty:
        return ""
    
    items = []
    for code, count in value_counts.head(10).items():  # 上位10個まで
        items.append(f"{code}:{count}")
    
    return ",".join(items)
```

### 2. カテゴリ分類ルール

#### 2.1 14ニーズカテゴリの判定条件
```python
NEEDS_CATEGORIES = {
    '日払い・週払い': {
        'keywords': ['日払い', '即日払い', '週払い', '日払OK', '即金'],
        'fields': ['application_name', 'salary', 'features', 'catch_copy'],
        'priority': 1,
        'logic': 'any'  # いずれかにマッチ
    },
    '短期・単発OK': {
        'keywords': ['短期', '単発', '1日のみ', '期間限定', '1day'],
        'fields': ['application_name', 'employment_type', 'features'],
        'priority': 2,
        'logic': 'any'
    },
    '高時給': {
        'keywords': ['高収入', '高時給', '高給'],
        'fields': ['application_name', 'catch_copy'],
        'priority': 3,
        'dynamic_check': lambda job, area_stats: ((job.min_salary + job.max_salary) / 2 if job.min_salary and job.max_salary else 1200) >= area_stats['avg_salary'] * 1.2
    },
    'シフト自由': {
        'keywords': ['シフト自由', 'シフト相談', '週1', '自由シフト', '好きな時間'],
        'fields': ['application_name', 'work_hours', 'features'],
        'priority': 4,
        'logic': 'any'
    },
    '未経験歓迎': {
        'keywords': ['未経験', '初心者', '経験不問', '未経験OK', '研修あり'],
        'fields': ['application_name', 'requirements', 'catch_copy'],
        'priority': 5,
        'logic': 'any'
    },
    '在宅・リモート': {
        'keywords': ['在宅', 'リモート', 'テレワーク', '完全在宅', 'remote'],
        'fields': ['application_name', 'work_location', 'features'],
        'priority': 6,
        'logic': 'any'
    },
    '学生歓迎': {
        'keywords': ['学生歓迎', '学生OK', '大学生', '専門学生'],
        'fields': ['application_name', 'requirements', 'features'],
        'priority': 7,
        'feature_code': 104  # feature_master参照
    },
    '高校生歓迎': {
        'keywords': ['高校生歓迎', '高校生OK', '高校生可'],
        'fields': ['application_name', 'age', 'features'],
        'priority': 8,
        'logic': 'any'
    },
    '主婦歓迎': {
        'keywords': ['主婦歓迎', '主婦・主夫', '主婦OK', '家事と両立'],
        'fields': ['application_name', 'requirements', 'features'],
        'priority': 9,
        'logic': 'any'
    },
    'シニア歓迎': {
        'keywords': ['シニア歓迎', 'シニアOK', '60歳以上', '中高年'],
        'fields': ['application_name', 'age', 'features'],
        'priority': 10,
        'logic': 'any'
    },
    '土日のみOK': {
        'keywords': ['土日のみ', '土日祝', '週末のみ', '土曜日', '日曜日'],
        'fields': ['application_name', 'work_days', 'features'],
        'priority': 11,
        'logic': 'any'
    },
    '副業・WワークOK': {
        'keywords': ['副業', 'Wワーク', 'ダブルワーク', '掛け持ち'],
        'fields': ['application_name', 'requirements', 'features'],
        'priority': 12,
        'logic': 'any'
    },
    '交通費支給': {
        'keywords': ['交通費', '交通費支給', '交通費全額'],
        'fields': ['application_name', 'benefits', 'features'],
        'priority': 13,
        'flag_check': 'transportation_allowance'
    },
    '即日勤務OK': {
        'keywords': ['即日勤務', '即日スタート', '今すぐ', '即開始'],
        'fields': ['application_name', 'start_date', 'features'],
        'priority': 14,
        'logic': 'any'
    }
}

def categorize_job(job, area_stats, occupation_master):

    """
    求人を14のニーズカテゴリ+職種カテゴリに分類
    複数該当する場合は制限なし（全て返す）
    """
    matched_categories = []
    
    for category_name, rules in NEEDS_CATEGORIES.items():
        # キーワードマッチング
        if 'keywords' in rules:
            for field in rules['fields']:
                field_value = str(getattr(job, field, '')).lower()
                if any(keyword in field_value for keyword in rules['keywords']):
                    matched_categories.append((rules['priority'], category_name))
                    break
        
        # フラグチェック
        if 'flag_check' in rules:
            if getattr(job, rules['flag_check'], False):
                matched_categories.append((rules['priority'], category_name))
        
        # 動的チェック
        if 'dynamic_check' in rules:
            if rules['dynamic_check'](job, area_stats):
                matched_categories.append((rules['priority'], category_name))
    
    # 優先度順にソートして返す（制限なし）
    matched_categories.sort(key=lambda x: x[0])
    needs_categories = [cat[1] for cat in matched_categories]
    
    # 職種カテゴリーも追加（実データに基づく）
    occupation_categories = get_occupation_categories(job, occupation_master)
    
    return {
        'needs_categories': needs_categories,  # 全該当カテゴリ
        'occupation_categories': occupation_categories  # 職種カテゴリ
    }

def get_occupation_categories(job, occupation_master):
    """
    実データに基づく職種カテゴリ判定
    occupation_cd1（大分類）に基づいて分類
    """
    # 実際のデータベースの職種コード（sample_job_data.csvより100単位の値を使用）
    OCCUPATION_CATEGORY_MAP = {
        100: 'コンビニ・スーパー',
        200: '飲食・フード',
        300: 'アパレル・ファッション',
        400: '軽作業・倉庫',
        500: 'オフィスワーク',
        600: 'イベント・キャンペーン',
        700: '教育・インストラクター',
        800: '医療・介護・福祉',
        900: 'デリバリー・配達',
        1000: '美容・エステ',
        1100: 'エンタメ・レジャー',
        1200: 'その他'
    }
    
    # jobのoccupation_cd1から対応するカテゴリを取得
    category = OCCUPATION_CATEGORY_MAP.get(job.occupation_cd1, 'その他')
    
    # 詳細分類も含める場合
    if hasattr(job, 'jobtype_detail'):
        detail = occupation_master.get_detail_name(job.occupation_cd1, job.jobtype_detail)
        return {'main': category, 'detail': detail}
    
    return {'main': category}
```

#### 2.2 高時給の判定基準
```python
def calculate_area_stats(jobs_df, granularity='prefecture'):
    """
    エリア別の時給統計を計算
    granularity: 'prefecture'（都道府県）または 'city'（市区町村）
    """
    if granularity == 'prefecture':
        group_col = 'prefecture_id'
    else:
        group_col = 'city_id'
    
    # min_salaryとmax_salaryの平均値で計算
    jobs_df['avg_salary'] = (jobs_df['min_salary'] + jobs_df['max_salary']) / 2
    area_stats = jobs_df.groupby(group_col).agg({
        'avg_salary': ['mean', 'std', 'median'],
        'job_id': 'count'
    }).reset_index()
    
    area_stats.columns = [group_col, 'avg_salary', 'std_salary', 
                          'median_salary', 'job_count']
    
    return area_stats

def is_high_wage(job, area_stats):
    """
    高時給判定（エリア平均の1.2倍以上）
    """
    # 都道府県レベルで判定
    area_avg = area_stats.loc[
        area_stats['prefecture_id'] == job.prefecture_id, 
        'avg_salary'
    ].values[0]
    
    # min_salaryとmax_salaryの平均値を使用
    avg_wage = (job.min_salary + job.max_salary) / 2 if job.min_salary and job.max_salary else 1200
    
    return avg_wage >= area_avg * 1.2

def convert_to_hourly_wage(job):
    """
    給与を時給に換算
    min_salaryとmax_salaryの平均値を使用
    """
    # min_salaryとmax_salaryの平均を返す
    if job.min_salary and job.max_salary:
        return (job.min_salary + job.max_salary) / 2
    elif job.min_salary:
        return job.min_salary
    elif job.max_salary:
        return job.max_salary
    else:
        return 1000  # デフォルト値
```


### 3. 40件選定アルゴリズム

#### 3.1 メール配信セクション構成

メール配信では以下の6セクションに求人を振り分けます（合計40件）：
1. **編集部おすすめの人気バイト（5件）**: fee × 応募クリック数のスコア上位
2. **あなたにおすすめ求人TOP5（5件）**: パーソナライズスコア上位
3. **地域別求人TOP10（10件）**: 都道府県内で職種マッチング
4. **近隣求人TOP8（8件）**: 市区町村周辺で職種マッチング
5. **高収入・日払いバイトTOP7（7件）**: 高時給・日払い条件の求人
6. **新着求人（5件）**: 過去1週間以内に投稿された求人＋スコア上位

全セクション共通条件：
- 2週間以内に応募した企業（endcl_cd）は除外
- 地域重み付け：市区町村 > 市区町村周辺 > 都道府県

#### 3.2 セクション間の重複処理
```python
class JobSelector:
    """
    40件の求人を5セクションに振り分けるクラス
    重複を除外し、各求人は1セクションのみに登場
    """
    
    def __init__(self, user, jobs_df, scores_df, area_stats):
        self.user = user
        self.jobs_df = jobs_df
        self.scores_df = scores_df
        self.area_stats = area_stats
        self.selected_job_ids = set()  # 重複防止用
        
    def select_40_jobs(self):
        """
        40件を選定し、6セクションに振り分け
        優先順位: 編集部 → TOP5 → 地域別 → 近隣 → 高収入 → 新着
        """
        sections = {
            'editorial_picks': [],
            'top5': [],
            'regional': [],
            'nearby': [],
            'high_income': [],
            'new': []
        }
        
        # 0. 編集部おすすめの選定（最優先）
        sections['editorial_picks'] = self._select_editorial_picks(5)
        
        # 1. TOP5の選定（パーソナライズ）
        sections['top5'] = self._select_top5()
        
        # 2. 地域別求人の選定（都道府県内）
        sections['regional'] = self._select_regional(10)
        
        # 3. 近隣求人の選定（市区町村周辺）
        sections['nearby'] = self._select_nearby(8)
        
        # 4. 高収入・日払い求人の選定
        sections['high_income'] = self._select_high_income(7)
        
        # 5. 新着求人の選定
        sections['new'] = self._select_new(5)
        
        # 40件に満たない場合の補充
        self._fill_shortage(sections)
        
        return sections
    
    def _select_editorial_picks(self, count):
        """編集部おすすめ：fee×応募クリック数の上位"""
        user_location = self._get_user_location()
        
        # 候補求人を取得
        candidates = self.jobs_df[
            ~self.jobs_df['job_id'].isin(self.selected_job_ids)
        ].copy()
        
        # 編集部おすすめスコアを計算
        candidates['editorial_score'] = candidates.apply(
            lambda job: calculate_editorial_popularity_score(job, user_location),
            axis=1
        )
        
        # スコア順でソート
        candidates = candidates.nlargest(count * 3, 'editorial_score')
        
        selected = []
        for _, job in candidates.iterrows():
            if len(selected) >= count:
                break
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
            
            selected.append(job.job_id)
            self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _select_top5(self):
        """TOP5: パーソナライズスコアの上位5件（2週間応募企業を除外）"""
        user_location = self._get_user_location()
        
        candidates = self.scores_df[
            (self.scores_df['user_id'] == self.user.id) &
            (~self.scores_df['job_id'].isin(self.selected_job_ids))
        ].copy()
        
        # 地域重み付けを適用
        candidates['weighted_score'] = candidates.apply(
            lambda row: row['total_score'] * get_location_weight(
                self.jobs_df[self.jobs_df['job_id'] == row['job_id']].iloc[0],
                user_location
            ),
            axis=1
        )
        
        candidates = candidates.nlargest(30, 'weighted_score')
        
        selected = []
        for _, row in candidates.iterrows():
            if len(selected) >= 5:
                break
            
            job = self.jobs_df[self.jobs_df['job_id'] == row['job_id']].iloc[0]
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
            
            # 過去7日以内に推薦していない
            if not self._was_recently_recommended(job.job_id):
                selected.append(job.job_id)
                self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _select_nearby(self, count):
        """近隣求人: ユーザーの推定市区町村とその隣接エリア"""
        user_city = self._estimate_user_city()
        nearby_cities = self._get_nearby_cities(user_city)
        
        candidates = self.jobs_df[
            (self.jobs_df['city_id'].isin(nearby_cities)) &
            (~self.jobs_df['job_id'].isin(self.selected_job_ids))
        ].copy()
        
        # 人気度（応募数）でソート
        candidates['popularity'] = candidates['recent_applications'] / candidates['recent_views'].clip(lower=1)
        candidates = candidates.nlargest(count * 2, 'popularity')
        
        selected = []
        for _, job in candidates.iterrows():
            if len(selected) >= count:
                break
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
                
            selected.append(job.job_id)
            self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _select_regional(self, count):
        """地域別求人: ユーザーの推定都道府県から（職種マッチング重視）"""
        user_prefecture = self._estimate_user_prefecture()
        user_profile = self._get_user_profile()
        
        candidates = self.jobs_df[
            (self.jobs_df['prefecture_id'] == user_prefecture) &
            (~self.jobs_df['job_id'].isin(self.selected_job_ids))
        ].copy()
        
        # パーソナライズスコア（職種マッチング含む）でソート
        if user_profile:
            candidates = candidates.merge(
                self.scores_df[['job_id', 'personalized_score']], 
                on='job_id'
            ).nlargest(count * 2, 'personalized_score')
        else:
            # プロファイルがない場合は基礎スコアでソート
            candidates = candidates.merge(
                self.scores_df[['job_id', 'basic_score']], 
                on='job_id'
            ).nlargest(count * 2, 'basic_score')
        
        selected = []
        for _, job in candidates.iterrows():
            if len(selected) >= count:
                break
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
                
            selected.append(job.job_id)
            self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _select_high_income(self, count):
        """高収入・日払いバイト：高時給または日払い可能な求人"""
        user_location = self._get_user_location()
        
        candidates = self.jobs_df[
            ~self.jobs_df['job_id'].isin(self.selected_job_ids)
        ].copy()
        
        # 高収入スコアを計算
        area_avg_salary = self.area_stats.get('avg_salary', 1200)
        candidates['high_income_score'] = 0
        
        # 高時給スコア
        if 'min_salary' in candidates.columns and 'max_salary' in candidates.columns:
            candidates['avg_salary'] = (candidates['min_salary'] + candidates['max_salary']) / 2
            # エリア平均の1.2倍以上を高時給とする
            candidates.loc[candidates['avg_salary'] >= area_avg_salary * 1.2, 'high_income_score'] += 50
        
        # 日払い可能スコア（feature_codesに212が含まれる場合）
        if 'feature_codes' in candidates.columns:
            candidates['has_daily_payment'] = candidates['feature_codes'].apply(
                lambda x: '212' in str(x).split(',') if x else False
            )
            candidates.loc[candidates['has_daily_payment'], 'high_income_score'] += 50
        
        # 地域重み付けを適用
        candidates['weighted_score'] = candidates.apply(
            lambda job: job.high_income_score * get_location_weight(job, user_location),
            axis=1
        )
        
        # スコアが高い順にソート
        candidates = candidates[candidates['weighted_score'] > 0].nlargest(count * 2, 'weighted_score')
        
        selected = []
        for _, job in candidates.iterrows():
            if len(selected) >= count:
                break
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
                
            selected.append(job.job_id)
            self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _select_new(self, count):
        """新着求人: 過去1週間以内に投稿（スコア上位優先）"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=7)
        user_location = self._get_user_location()
        user_profile = self._get_user_profile()
        
        candidates = self.jobs_df[
            (self.jobs_df['posting_date'] >= cutoff_date) &
            (~self.jobs_df['job_id'].isin(self.selected_job_ids))
        ].copy()
        
        # スコアと地域重み付けを組み合わせてソート
        if user_profile:
            # パーソナライズスコアがある場合
            candidates = candidates.merge(
                self.scores_df[['job_id', 'personalized_score']], 
                on='job_id',
                how='left'
            )
            candidates['weighted_score'] = candidates.apply(
                lambda job: job.get('personalized_score', 50) * get_location_weight(job, user_location),
                axis=1
            )
        else:
            # 基礎スコアを使用
            candidates = candidates.merge(
                self.scores_df[['job_id', 'basic_score']], 
                on='job_id',
                how='left'
            )
            candidates['weighted_score'] = candidates.apply(
                lambda job: job.get('basic_score', 50) * get_location_weight(job, user_location),
                axis=1
            )
        
        # スコアが高い順でソート（新着の中での優先順位）
        candidates = candidates.nlargest(count * 3, 'weighted_score')
        
        selected = []
        for _, job in candidates.iterrows():
            if len(selected) >= count:
                break
            
            # 2週間以内の応募を除外
            if self._was_applied_within_2weeks(job.endcl_cd):
                continue
                
            selected.append(job.job_id)
            self.selected_job_ids.add(job.job_id)
        
        return selected
    
    def _fill_shortage(self, sections):
        """40件に満たない場合の補充"""
        total_count = sum(len(jobs) for jobs in sections.values())
        
        if total_count < 40:
            shortage = 40 - total_count
            
            # スコア順で未選定の求人から補充
            remaining = self.scores_df[
                (self.scores_df['user_id'] == self.user.id) &
                (~self.scores_df['job_id'].isin(self.selected_job_ids))
            ].nlargest(shortage, 'total_score')
            
            # 各セクションに均等に配分
            for i, (_, row) in enumerate(remaining.iterrows()):
                if i < shortage:
                    # ラウンドロビンで各セクションに追加
                    section_names = ['regional', 'nearby', 'high_income', 'new']
                    target_section = section_names[i % len(section_names)]
                    sections[target_section].append(row['job_id'])
                    self.selected_job_ids.add(row['job_id'])
    
    def _estimate_user_prefecture(self):
        """ユーザーの都道府県を応募履歴から推定"""
        # user_actionsテーブルから最頻出の都道府県を取得
        recent_applications = self._get_user_application_history()
        if recent_applications.empty:
            return 13  # デフォルト: 東京都
        
        prefecture_counts = recent_applications['prefecture_id'].value_counts()
        return prefecture_counts.index[0] if not prefecture_counts.empty else 13
    
    def _estimate_user_city(self):
        """ユーザーの市区町村を応募履歴から推定"""
        recent_applications = self._get_user_application_history()
        if recent_applications.empty:
            return 13101  # デフォルト: 東京都千代田区
        
        city_counts = recent_applications['city_id'].value_counts()
        return city_counts.index[0] if not city_counts.empty else 13101
    
    def _get_nearby_cities(self, city_id):
        """隣接市区町村のリストを取得（簡易版）"""
        # 実装では隣接マスターテーブルを使用
        # ここでは同じ都道府県の市区町村を返す簡易実装
        prefecture_id = city_id // 1000
        nearby = [city_id]  # 自身を含む
        
        # 同じ都道府県の他の市区町村を3つまで追加
        all_cities = self.jobs_df[
            self.jobs_df['prefecture_id'] == prefecture_id
        ]['city_id'].unique()
        
        for city in all_cities[:4]:
            if city != city_id:
                nearby.append(city)
        
        return nearby
    
    def _was_recently_recommended(self, job_id):
        """過去7日以内に推薦済みかチェック"""
        # job_processing_historyテーブルをチェック
        # 簡易実装ではFalseを返す
        return False
    
    def _was_applied_within_2weeks(self, endcl_cd):
        """過去2週間以内に応募済みかチェック"""
        from datetime import datetime, timedelta
        
        # user_actionsテーブルから2週間以内の応募をチェック
        cutoff_date = datetime.now() - timedelta(days=14)
        
        # 簡易実装：applied_endcl_cdsの内容と日付をチェック
        recent_applications = self._get_recent_applications(cutoff_date)
        return endcl_cd in recent_applications
    
    def _get_recent_applications(self, cutoff_date):
        """指定日以降に応募した企業リストを取得"""
        # user_actionsテーブルから取得
        # 簡易実装ではset()を返す
        return set()
    
    def _get_user_location(self):
        """ユーザーの地域情報を取得"""
        user_prefecture = self._estimate_user_prefecture()
        user_city = self._estimate_user_city()
        nearby_cities = self._get_nearby_cities(user_city)
        
        return {
            'pref_cd': user_prefecture,
            'city_cd': user_city,
            'nearby_cities': nearby_cities
        }
    
    def _get_user_application_history(self):
        """ユーザーの応募履歴を取得"""
        # user_actionsテーブルから取得
        # 簡易実装では空のDataFrameを返す
        import pandas as pd
        return pd.DataFrame()
    
    def _get_applied_companies(self):
        """過去に応募した企業のendcl_cdリストを取得"""
        # user_profilesテーブルのapplied_endcl_cdsから取得
        # またはuser_actionsテーブルから直接取得
        user_profile = self._get_user_profile()
        if user_profile and hasattr(user_profile, 'applied_endcl_cds'):
            # "EX12345678:3,EX87654321:1" 形式をパース
            endcl_freq_str = user_profile.applied_endcl_cds
            if endcl_freq_str:
                applied_companies = set()
                for item in endcl_freq_str.split(','):
                    if ':' in item:
                        endcl_cd, count = item.split(':')
                        applied_companies.add(endcl_cd)
                return applied_companies
        return set()
    
    def _get_user_profile(self):
        """ユーザープロファイルを取得"""
        # user_profilesテーブルから取得
        # 簡易実装ではNoneを返す
        return None
```

### 4. メール文面の5セクション切り分けロジック

#### 4.1 各セクションの表示内容（ERD準拠）
```python
EMAIL_SECTIONS_CONFIG = {
    'editorial_picks': {
        'title': '編集部おすすめの人気バイト',
        'count': 5,
        'display_fields': {
            'title': True,          # 求人タイトル
            'company': True,        # 会社名
            'salary': True,         # 給与
            'location': True,       # 勤務地
            'features': True,       # 特徴タグ（最大3個）
            'work_hours': True,     # 勤務時間
            'access': True,         # アクセス
            'popularity': True      # 人気度指標
        }
    },
    'top5': {
        'title': 'あなたにおすすめ求人TOP5',
        'count': 5,
        'display_fields': {
            'title': True,
            'company': True,
            'salary': True,
            'location': True,
            'features': True,       # 特徴タグ（最大3個）
            'work_hours': True,
            'access': True
        }
    },
    'regional': {
        'title': '{prefecture}のおすすめ求人TOP10',
        'count': 10,
        'display_fields': {
            'title': True,
            'company': True,
            'salary': True,
            'location': False,      # 都道府県は自明
            'features': True,       # 特徴タグ（最大2個）
            'work_hours': False,
            'access': True
        }
    },
    'nearby': {
        'title': '{city}周辺のおすすめバイトTOP10',
        'count': 8,  # 40件に収めるため調整
        'display_fields': {
            'title': True,
            'company': True,
            'salary': True,
            'location': False,      # 市区町村は自明
            'features': True,       # 特徴タグ（最大2個）
            'work_hours': True,
            'access': True
        }
    },
    'high_income': {
        'title': '高収入・日払いバイトTOP10',
        'count': 7,  # 40件に収めるため調整
        'display_fields': {
            'title': True,
            'company': True,
            'salary': True,         # 給与を強調
            'location': True,
            'features': True,       # 特徴タグ（最大3個）
            'work_hours': False,
            'access': False,
            'payment_type': True    # 日払い可否
        }
    },
    'new': {
        'title': '新着求人',
        'count': 5,
        'display_fields': {
            'title': True,
            'company': True,
            'salary': True,
            'location': True,
            'features': True,       # 特徴タグ（最大2個）
            'work_hours': False,
            'access': False,
            'posting_date': True    # 投稿日
        }
    }
}

def format_job_for_email(job, section_type, user_context=None):
    """
    セクションタイプに応じて求人情報をフォーマット
    """
    config = EMAIL_SECTIONS_CONFIG[section_type]
    display = config['display_fields']
    
    formatted = {
        'job_id': job.job_id,
        'url': f"https://example.com/jobs/{job.job_id}"
    }
    
    if display.get('title'):
        formatted['title'] = truncate_text(job.application_name, 50)
    
    if display.get('company'):
        formatted['company'] = job.company_name
    
    if display.get('salary'):
        formatted['salary'] = format_salary(job)
    
    if display.get('location'):
        formatted['location'] = f"{job.city_name}"
    
    if display.get('features'):
        max_tags = 3 if section_type in ['top5', 'benefits'] else 2
        formatted['features'] = extract_feature_tags(job)[:max_tags]
    
    if display.get('work_hours'):
        formatted['work_hours'] = remove_html_tags(job.hours) if hasattr(job, 'hours') else ''
    
    
    if display.get('access'):
        formatted['access'] = job.station_name_eki if hasattr(job, 'station_name_eki') else ''
    
    if display.get('benefits'):
        formatted['benefits'] = extract_benefits_detail(job)
    
    if display.get('posting_date'):
        formatted['posting_date'] = job.posting_date.strftime('%m月%d日')
    
    return formatted

def truncate_text(text, max_length):
    """テキストを指定文字数で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def format_salary(job):
    """給与表示のフォーマット"""
    # min_salaryとmax_salaryを使用
    if job.min_salary and job.max_salary:
        if job.min_salary == job.max_salary:
            return f"時給{job.min_salary:,}円"
        else:
            return f"時給{job.min_salary:,}円〜{job.max_salary:,}円"
    elif job.min_salary:
        return f"時給{job.min_salary:,}円〜"
    elif job.max_salary:
        return f"時給〜{job.max_salary:,}円"
    else:
        return job.salary_text

def extract_feature_tags(job):
    """求人の特徴タグを抽出（feature_codesから変換）"""
    if not hasattr(job, 'feature_codes') or not job.feature_codes:
        return []
    
    # feature_master定義
    feature_master = {
        '103': '未経験OK',
        '200': '交通費支給',
        '212': '日払いOK',
        '217': '週払いOK',
        '300': 'まかない有',
        '400': '制服貸与',
        '500': '社員割引',
        '600': '髪型自由',
        '700': 'シフト自由',
        '800': '短時間OK',
        '900': '駅チカ'  # 5分以内
    }
    
    tags = []
    # feature_codesはカンマ区切りの文字列（例: "103,200,300"）
    feature_codes = str(job.feature_codes).split(',') if job.feature_codes else []
    
    for code in feature_codes:
        code = code.strip()
        if code in feature_master:
            tags.append(feature_master[code])
    
    return tags

def remove_html_tags(text):
    """HTMLタグを除去してプレーンテキストを返す"""
    import re
    if not text:
        return ''
    # HTMLタグを除去
    clean_text = re.sub(r'<[^>]+>', '', str(text))
    # 複数の空白を単一スペースに置換
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

def extract_benefits_detail(job):
    """特典の詳細説明"""
    benefits = []
    
    if job.feature_bonus:
        benefits.append('入社祝い金あり')
    if job.meal_provided:
        benefits.append('まかない無料')
    if job.employee_discount:
        benefits.append('社員割引あり')
    if job.uniform_provided:
        benefits.append('制服無料貸与')
    
    return '、'.join(benefits)
```

## 🟡 優先度: 中（実装に影響）の回答

### 5. データ管理戦略

#### 5.1 重複求人の処理（endcl_cdベース）
```python
DUPLICATE_HANDLING = {
    'strategy': 'update',  # 'update', 'skip', 'version'
    'duplicate_key': ['endcl_cd', ],
    'update_fields': 'all',  # 'all' または特定フィールドリスト
    'keep_history': True
}

def handle_duplicate_jobs(new_job, existing_job):
    """
    重複求人の処理
    job_idが同じ場合: 更新
    内容が同じでIDが異なる場合: 重複キーで判定
    """
    if new_job.job_id == existing_job.job_id:
        # 同一IDの場合は更新
        if DUPLICATE_HANDLING['keep_history']:
            # 履歴を保存
            save_job_history(existing_job)
        
        # 全フィールド更新
        update_job(new_job)
        return 'updated'
    
    # 重複キーチェック
    is_duplicate = all(
        getattr(new_job, key) == getattr(existing_job, key)
        for key in DUPLICATE_HANDLING['duplicate_key']
    )
    
    if is_duplicate:
        if DUPLICATE_HANDLING['strategy'] == 'skip':
            return 'skipped'
        elif DUPLICATE_HANDLING['strategy'] == 'update':
            # より新しい情報で更新
            if new_job.posting_date > existing_job.posting_date:
                update_job(new_job)
                return 'updated'
        
    return 'new'
```

#### 5.2 データ更新戦略
```python
UPDATE_STRATEGY = {
    'method': 'soft_delete',    # 'soft_delete' or 'hard_delete'
    'update_type': 'full',      # 'full' or 'differential'
    'history_retention': 30,    # 履歴保持日数
    'archive_old_data': True
}

def update_existing_job(job_id, new_data):
    """既存求人の更新"""
    # ソフトデリート（is_activeフラグ）
    if UPDATE_STRATEGY['method'] == 'soft_delete':
        # is_activeをfalseに設定
        deactivate_job(job_id)
        # 新しいレコードとして挿入
        create_job(new_data)
    else:
        # 全フィールド上書き
        overwrite_job(job_id, new_data)
    
    # 変更履歴を記録
    if UPDATE_STRATEGY['archive_old_data']:
        archive_job_change(job_id, new_data)
```

### 6. エラーハンドリング

#### 6.1 バッチ処理の中断と再開
```python
BATCH_CONFIG = {
    'checkpoint_interval': 100,  # 100ユーザーごとにチェックポイント
    'retry_attempts': 3,
    'retry_delay': 60,  # 秒
    'failure_threshold': 0.1,  # 10%以上失敗で停止
    'recovery_mode': 'checkpoint'  # 'checkpoint' or 'restart'
}

class BatchProcessor:
    def __init__(self):
        self.checkpoint_file = 'batch_checkpoint.json'
        self.failed_users = []
        
    def process_batch(self, users):
        """バッチ処理のメイン"""
        checkpoint = self.load_checkpoint()
        start_index = checkpoint.get('last_processed_index', 0)
        
        for i, user in enumerate(users[start_index:], start=start_index):
            try:
                # ユーザー処理
                self.process_user(user)
                
                # チェックポイント保存
                if i % BATCH_CONFIG['checkpoint_interval'] == 0:
                    self.save_checkpoint({
                        'last_processed_index': i,
                        'failed_users': self.failed_users,
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                self.failed_users.append({
                    'user_id': user.id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                
                # 失敗率チェック
                failure_rate = len(self.failed_users) / (i + 1)
                if failure_rate > BATCH_CONFIG['failure_threshold']:
                    raise BatchProcessingError(f"失敗率が閾値を超えました: {failure_rate:.2%}")
        
        # 失敗ユーザーの再処理
        self.retry_failed_users()
    
    def retry_failed_users(self):
        """失敗したユーザーの再処理"""
        for attempt in range(BATCH_CONFIG['retry_attempts']):
            if not self.failed_users:
                break
                
            time.sleep(BATCH_CONFIG['retry_delay'])
            
            retry_list = self.failed_users.copy()
            self.failed_users = []
            
            for failed_user in retry_list:
                try:
                    user = get_user_by_id(failed_user['user_id'])
                    self.process_user(user)
                except Exception as e:
                    self.failed_users.append(failed_user)
```

#### 6.2 メール生成失敗時の処理
```python
EMAIL_ERROR_HANDLING = {
    'continue_on_failure': True,  # 一部失敗でも継続
    'max_retries': 3,
    'retry_delay': 30,  # 秒
    'log_location': 'logs/email_failures.json',
    'alert_threshold': 100  # 100件以上失敗でアラート
}

def generate_emails_with_error_handling(users):
    """エラーハンドリング付きメール生成"""
    results = {
        'success': [],
        'failed': [],
        'retried': []
    }
    
    for user in users:
        success = False
        last_error = None
        
        for attempt in range(EMAIL_ERROR_HANDLING['max_retries']):
            try:
                email_content = generate_email_for_user(user)
                save_to_queue(user.id, email_content)
                results['success'].append(user.id)
                success = True
                break
                
            except Exception as e:
                last_error = e
                if attempt < EMAIL_ERROR_HANDLING['max_retries'] - 1:
                    time.sleep(EMAIL_ERROR_HANDLING['retry_delay'])
                    results['retried'].append({
                        'user_id': user.id,
                        'attempt': attempt + 1,
                        'error': str(e)
                    })
        
        if not success:
            results['failed'].append({
                'user_id': user.id,
                'error': str(last_error),
                'timestamp': datetime.now().isoformat()
            })
            
            # エラーログ保存
            log_email_failure(user.id, last_error)
    
    # アラートチェック
    if len(results['failed']) >= EMAIL_ERROR_HANDLING['alert_threshold']:
        send_alert(f"メール生成失敗が{len(results['failed'])}件発生")
    
    return results
```

### 7. メール内容の詳細

#### 7.0 メール件名生成AI（GPT-5 nano）

```python
# GPT-5 nano 設定（参考文面を活用した学習付き）
AI_CONFIG = {
    'model': 'gpt-5-nano',
    'api_endpoint': 'https://api.openai.com/v1/chat/completions',
    'api_key_location': 'OPENAI_API_KEY',  # 環境変数で管理
    'max_tokens': 60,  # 件名は短いので60トークンで十分
    'temperature': 0.7,  # 適度な創造性（0.7）
    'top_p': 0.9,
    'frequency_penalty': 0.3,  # 繰り返しを避ける
    'presence_penalty': 0.3,
    'timeout': 5,  # 5秒でタイムアウト
    'retry_count': 2,
    'fallback_strategy': 'template'  # 失敗時はテンプレート使用
}

def generate_email_subject(user_data, job_selections):
    """
    GPT-5 nanoを使用してメール件名を生成
    """
    import openai
    import os
    
    # API設定
    openai.api_key = os.getenv(AI_CONFIG['api_key_location'])
    
    # コンテキスト準備
    context = prepare_subject_context(user_data, job_selections)
    
    # プロンプト構築
    prompt = build_subject_prompt(context)
    
    try:
        response = openai.ChatCompletion.create(
            model=AI_CONFIG['model'],
            messages=[
                {"role": "system", "content": "あなたは開封率の高いメール件名を作成する専門家です。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=AI_CONFIG['max_tokens'],
            temperature=AI_CONFIG['temperature'],
            top_p=AI_CONFIG['top_p'],
            frequency_penalty=AI_CONFIG['frequency_penalty'],
            presence_penalty=AI_CONFIG['presence_penalty'],
            timeout=AI_CONFIG['timeout']
        )
        
        subject = response.choices[0].message.content.strip()
        
        # 件名の検証
        if validate_subject(subject):
            return subject
        else:
            return generate_fallback_subject(context)
            
    except Exception as e:
        logger.error(f"GPT-5 nano エラー: {e}")
        return generate_fallback_subject(context)

def prepare_subject_context(user_data, job_selections):
    """
    件名生成用のコンテキストを準備
    """
    # ユーザーの推定地域（応募履歴から）
    user_area = estimate_user_area(user_data)
    
    # よく応募するカテゴリ（上位3つ）
    frequent_categories = get_frequent_categories(user_data, limit=3)
    
    # 最近の応募（5件分のタイトルのみ）
    recent_applications = get_recent_applications(user_data, limit=5)
    
    # TOP5求人のタイトル（最初の3つ）
    top5_titles = [job['title'][:20] for job in job_selections['top5'][:3]]
    
    # 最も特徴的な求人（最高スコアの1件）
    featured_job = job_selections['top5'][0]['title'] if job_selections['top5'] else None
    
    # 新着求人数
    new_count = len(job_selections.get('new', []))
    
    return {
        'user_area': user_area,
        'frequent_categories': frequent_categories,
        'recent_applications': recent_applications,
        'top5_jobs': top5_titles,
        'featured_job': featured_job,
        'new_count': new_count,
        'total_count': sum(len(jobs) for jobs in job_selections.values())
    }

def build_subject_prompt(context):
    """
    GPT-5 nano用のプロンプト構築（参考文面付き）
    """
    # 参考となる優良件名5つ
    reference_subjects = [
        '【バイト速報】渋谷エリアの高時給求人35件＋新着5件',
        '【今週の注目】未経験OK×日払い可の人気求人40件',
        '【新着あり】あなたの街の週1〜OKバイト38件',
        '【厳選40件】夏休み短期バイト＆高時給特集',
        '【本日配信】飲食・販売・オフィス系おすすめ求人'
    ]
    
    prompt = f"""
メール件名を1つ生成してください。

参考となる優良件名:
{chr(10).join(f"- {subject}" for subject in reference_subjects)}

条件:
- 最大50文字
- 絵文字は使用しない
- 【】で重要部分を囲む
- 数字を含める（求人数など）
- 参考件名のパターンを学習しつつ独自性も出す

ユーザー情報:
- 地域: {context['user_area']}
- よく見るカテゴリ: {', '.join(context['frequent_categories'][:2])}
- 推薦求人数: {context['total_count']}件

特徴的な求人:
- {context['featured_job']}

件名:"""
    
    return prompt

def validate_subject(subject):
    """
    生成された件名の検証
    """
    # 長さチェック
    if len(subject) > 50:
        return False
    
    # 禁止文字チェック
    forbidden_chars = ['😀', '🎉', '💰', '!', '！！']
    if any(char in subject for char in forbidden_chars):
        return False
    
    # 最低限の内容チェック
    if len(subject) < 10:
        return False
    
    return True

def generate_fallback_subject(context):
    """
    フォールバック用のテンプレート件名生成
    """
    templates = [
        '【バイト速報】{user_area}のおすすめ求人{total_count}件',
        '【{user_area}】今週の注目バイト{total_count}件をお届け',
        '【新着あり】{user_area}エリアの人気求人{total_count}件',
        '【{frequent_category}】他、おすすめ求人{total_count}件'
    ]
    
    import random
    template = random.choice(templates)
    
    # カテゴリ選択
    frequent_category = context['frequent_categories'][0] if context['frequent_categories'] else '人気'
    
    return template.format(
        user_area=context['user_area'],
        total_count=context['total_count'],
        frequent_category=frequent_category
    )

# バッチ処理の最適化
BATCH_AI_CONFIG = {
    'method': 'individual_with_cache',  # 個別生成だがキャッシュ活用
    'rate_limit': 100,  # 100リクエスト/分
    'cache_similar_users': True,  # 類似ユーザーで件名再利用
    'cache_ttl': 3600,  # 1時間キャッシュ
    'parallel_requests': 10,  # 並列リクエスト数
    'batch_size': 100  # 100ユーザーずつ処理
}

def generate_subjects_batch(users_batch):
    """
    バッチ処理での件名生成（並列処理対応）
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import hashlib
    
    results = {}
    cache = {}
    
    def get_cache_key(context):
        """類似ユーザー判定用のキャッシュキー生成"""
        key_parts = [
            context['user_area'],
            ','.join(sorted(context['frequent_categories'][:2])),
            str(context['total_count'] // 10 * 10)  # 10件単位で丸める
        ]
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    with ThreadPoolExecutor(max_workers=BATCH_AI_CONFIG['parallel_requests']) as executor:
        futures = {}
        
        for user in users_batch:
            context = prepare_subject_context(user.data, user.job_selections)
            cache_key = get_cache_key(context)
            
            # キャッシュチェック
            if BATCH_AI_CONFIG['cache_similar_users'] and cache_key in cache:
                results[user.id] = cache[cache_key]
                continue
            
            # 非同期実行
            future = executor.submit(generate_email_subject, user.data, user.job_selections)
            futures[future] = (user.id, cache_key)
        
        # 結果収集
        for future in as_completed(futures):
            user_id, cache_key = futures[future]
            try:
                subject = future.result(timeout=10)
                results[user_id] = subject
                
                # キャッシュ保存
                if BATCH_AI_CONFIG['cache_similar_users']:
                    cache[cache_key] = subject
                    
            except Exception as e:
                logger.error(f"User {user_id} 件名生成失敗: {e}")
                # フォールバック
                context = prepare_subject_context(
                    get_user_by_id(user_id).data,
                    get_user_by_id(user_id).job_selections
                )
                results[user_id] = generate_fallback_subject(context)
    
    return results

# A/Bテスト対応
AB_TEST_CONFIG = {
    'enabled': False,  # 初期は無効
    'variation_count': 2,  # A/B の2パターン
    'test_percentage': 10,  # 10%のユーザーでテスト
    'metrics': ['open_rate', 'click_rate']  # 追跡メトリクス
}

def generate_subject_with_ab_test(user_data, job_selections):
    """
    A/Bテスト対応の件名生成
    """
    if not AB_TEST_CONFIG['enabled']:
        return generate_email_subject(user_data, job_selections)
    
    # テスト対象ユーザーか判定
    import random
    if random.random() > AB_TEST_CONFIG['test_percentage'] / 100:
        return generate_email_subject(user_data, job_selections)
    
    # バリエーション生成
    variations = []
    for i in range(AB_TEST_CONFIG['variation_count']):
        # temperatureを変えて生成
        original_temp = AI_CONFIG['temperature']
        AI_CONFIG['temperature'] = 0.5 + i * 0.2  # 0.5, 0.7, 0.9...
        
        subject = generate_email_subject(user_data, job_selections)
        variations.append(subject)
        
        AI_CONFIG['temperature'] = original_temp
    
    # ランダムに1つ選択してトラッキング
    selected = random.choice(variations)
    track_ab_test(user_data['user_id'], selected, variations)
    
    return selected
```

#### 7.1 HTMLテンプレート構造
```python
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        /* インラインCSS（Gmailサポート） */
        body {{ font-family: 'Hiragino Sans', sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background: #4A90E2; color: white; padding: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #e0e0e0; }}
        .job-card {{ margin: 10px 0; padding: 10px; background: #f9f9f9; }}
        .tag {{ display: inline-block; padding: 2px 8px; background: #e3f2fd; 
                border-radius: 12px; font-size: 12px; margin: 0 4px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>バイト速報 - {date}</h1>
        </div>
        
        <div class="greeting">
            <p>こんにちは！</p>
            <p>今週のおすすめバイト情報をお届けします。</p>
        </div>
        
        {sections_html}
        
        <div class="footer">
            <p>配信停止は<a href="{unsubscribe_url}">こちら</a></p>
            <p>© 2025 バイト速報</p>
        </div>
    </div>
</body>
</html>
"""
```

#### 7.2 文字数制限
```python
EMAIL_CONSTRAINTS = {
    'subject': {
        'max_chars': 50,  # 件名は50文字以内
        'template': '【バイト速報】{user_area}のおすすめ求人{count}件'
    },
    'job_description': {
        'max_chars': 100,  # 各求人の説明は100文字
        'truncate': True
    },
    'total_size': {
        'max_kb': 102,  # Gmail等の制限（102KB以下推奨）
        'warning_kb': 90  # 90KB超えで警告
    }
}

def validate_email_size(html_content):
    """メールサイズの検証"""
    size_kb = len(html_content.encode('utf-8')) / 1024
    
    if size_kb > EMAIL_CONSTRAINTS['total_size']['max_kb']:
        # サイズ超過時は画像を削除、説明を短縮
        html_content = reduce_email_size(html_content)
    elif size_kb > EMAIL_CONSTRAINTS['total_size']['warning_kb']:
        logger.warning(f"メールサイズが大きい: {size_kb:.1f}KB")
    
    return html_content
```

## 🟢 優先度: 低（最適化関連）の回答

### 8. パフォーマンス最適化

#### 8.1 メモリ管理の具体策
```python
MEMORY_OPTIMIZATION = {
    'pandas_dtypes': {
        'job_id': 'int32',
        'user_id': 'int32',
        'min_salary': 'float32',
        'max_salary': 'float32',
        'prefecture_id': 'int16',
        'city_id': 'int32',
        'is_active': 'bool',
        'company_name': 'category',  # カテゴリ型で大幅削減
        'job_category': 'category'
    },
    'chunk_size': 1000,  # 1000行ずつ処理
    'gc_frequency': 100  # 100イテレーションごとにGC
}

def optimize_dataframe_memory(df):
    """DataFrameのメモリ最適化"""
    for col, dtype in MEMORY_OPTIMIZATION['pandas_dtypes'].items():
        if col in df.columns:
            if dtype == 'category':
                df[col] = df[col].astype('category')
            else:
                df[col] = df[col].astype(dtype)
    
    # 不要カラムの即座削除
    unnecessary_cols = ['temp_col', 'debug_info']
    df.drop(columns=[col for col in unnecessary_cols if col in df.columns], inplace=True)
    
    return df
```

#### 8.2 キャッシュ戦略
```python
CACHE_CONFIG = {
    'backend': 'supabase',  # Supabase Edge Functionsのキャッシュ
    'ttl': {
        'user_preferences': 3600,    # 1時間
        'area_stats': 86400,         # 24時間
        'job_scores': 1800,          # 30分
        'als_model': 21600           # 6時間
    },
    'key_pattern': 'job_match:{type}:{id}:{date}'
}

def get_cached_or_compute(cache_key, compute_func, ttl=3600):
    """キャッシュまたは計算"""
    # Supabaseのキャッシュチェック
    cached = supabase_cache.get(cache_key)
    
    if cached and not is_expired(cached, ttl):
        return cached['data']
    
    # 計算して保存
    result = compute_func()
    supabase_cache.set(cache_key, {
        'data': result,
        'timestamp': datetime.now().isoformat()
    }, ttl=ttl)
    
    return result
```

### 9. モニタリングUI

#### 9.1 認証方式
```python
AUTH_CONFIG = {
    'method': 'supabase_auth',  # Supabase Auth使用
    'allowed_roles': ['admin', 'operator'],
    'session_timeout': 3600,  # 1時間
    'require_2fa': False
}

# Next.js middleware.ts
async function authenticate(req) {
    const token = req.headers.authorization?.split(' ')[1]
    
    if (!token) {
        return { authorized: false }
    }
    
    // Supabase Auth検証
    const { data: user, error } = await supabase.auth.getUser(token)
    
    if (error || !AUTH_CONFIG['allowed_roles'].includes(user.role)) {
        return { authorized: false }
    }
    
    return { authorized: true, user }
}
```

#### 9.2 リアルタイム更新
```python
REALTIME_CONFIG = {
    'method': 'supabase_realtime',  # Supabaseのリアルタイム機能
    'channels': ['batch_progress', 'error_alerts'],
    'polling_fallback': 5000,  # 5秒（フォールバック）
}

# フロントエンド（React）
useEffect(() => {
    const channel = supabase
        .channel('batch_progress')
        .on('postgres_changes', {
            event: 'UPDATE',
            schema: 'public',
            table: 'batch_status'
        }, (payload) => {
            setProgress(payload.new.progress)
        })
        .subscribe()
    
    return () => {
        supabase.removeChannel(channel)
    }
}, [])
```

### 10. テストデータ

#### 10.1 テストデータ生成戦略（仮ユーザーデータ付き）


```python
TEST_DATA_CONFIG = {
    'job_count': 100000,
    'user_count': 10000,
    'method': 'specified_users_plus_faker',  # 指定ユーザー + Faker生成
    'seed': 42,  # 再現性確保
    'realistic_patterns': True
}

# 指定された9人のテストユーザー
SPECIFIED_TEST_USERS = [
    {
        'email': 'koganei@gmail.com',
        'prefecture': '東京都',
        'pref_cd': 13,
        'city': '小金井市',
        'city_cd': 13210,
        'age': 24,
        'age_range': '20-24',
        'gender': '男性',
        'user_type': 'フリーター',
        'preferred_needs': '日払い',
        'preferred_occupation': None
    },
    {
        'email': 'shinjuku@gmail.com',
        'prefecture': '東京都',
        'pref_cd': 13,
        'city': '新宿区',
        'city_cd': 13104,
        'age': 22,
        'age_range': '20-24',
        'gender': '男性',
        'user_type': '大学生',
        'preferred_needs': '高収入',
        'preferred_occupation': None
    },
    {
        'email': 'machida@gmail.com',
        'prefecture': '東京都',
        'pref_cd': 13,
        'city': '町田市',
        'city_cd': 13209,
        'age': 25,
        'age_range': '25-29',
        'gender': '女性',
        'user_type': 'フリーター',
        'preferred_needs': None,
        'preferred_occupation': 'フード'
    },
    {
        'email': 'yokohama@gmail.com',
        'prefecture': '神奈川県',
        'pref_cd': 14,
        'city': '横浜市',
        'city_cd': 14100,
        'age': 26,
        'age_range': '25-29',
        'gender': '男性',
        'user_type': 'フリーター',
        'preferred_needs': '高収入',
        'preferred_occupation': None
    },
    {
        'email': 'ube@gmail.com',
        'prefecture': '山口県',
        'pref_cd': 35,
        'city': '宇部市',
        'city_cd': 35202,
        'age': 20,
        'age_range': '20-24',
        'gender': '男性',
        'user_type': '学生',
        'preferred_needs': None,
        'preferred_occupation': '軽作業'
    },
    {
        'email': 'osaka@gmail.com',
        'prefecture': '大阪府',
        'pref_cd': 27,
        'city': '大阪市',
        'city_cd': 27100,
        'age': 23,
        'age_range': '20-24',
        'gender': '女性',
        'user_type': 'フリーター',
        'preferred_needs': '日払い',
        'preferred_occupation': None
    },
    {
        'email': 'fukuoka@gmail.com',
        'prefecture': '福岡県',
        'pref_cd': 40,
        'city': '福岡市',
        'city_cd': 40130,
        'age': 24,
        'age_range': '20-24',
        'gender': '男性',
        'user_type': 'フリーター',
        'preferred_needs': '高収入',
        'preferred_occupation': None
    },
    {
        'email': 'kaigo@gmail.com',
        'prefecture': '東京都',
        'pref_cd': 13,
        'city': '小金井市',
        'city_cd': 13210,
        'age': 26,
        'age_range': '25-29',
        'gender': '女性',
        'user_type': 'フリーター',
        'preferred_needs': None,
        'preferred_occupation': '介護'
    },
    {
        'email': 'juku@gmail.com',
        'prefecture': '東京都',
        'pref_cd': 13,
        'city': '小金井市',
        'city_cd': 13210,
        'age': 26,
        'age_range': '25-29',
        'gender': '女性',
        'user_type': 'フリーター',
        'preferred_needs': None,
        'preferred_occupation': '塾'
    }
]

def generate_test_data():
    """テストデータ生成"""
    from faker import Faker
    import numpy as np
    
    fake = Faker('ja_JP')
    Faker.seed(TEST_DATA_CONFIG['seed'])
    np.random.seed(TEST_DATA_CONFIG['seed'])
    
    # リアルな分布パターン
    prefecture_weights = get_realistic_prefecture_distribution()
    category_weights = get_realistic_category_distribution()
    
    jobs = []
    for i in range(TEST_DATA_CONFIG['job_count']):
        job = {
            'job_id': i + 1,
            'company_name': fake.company(),
            'application_name': generate_realistic_job_title(fake, category_weights),
            'min_salary': np.random.normal(1000, 200),  # 正規分布
            'max_salary': np.random.normal(1400, 300),  # 正規分布
            'prefecture_id': np.random.choice(47, p=prefecture_weights),
            'posting_date': fake.date_between('-30d', 'today'),
            # ... 他のフィールド
        }
        jobs.append(job)
    
    # ユーザー行動のシミュレーション
    users = generate_users_with_behavior_patterns(TEST_DATA_CONFIG['user_count'])
    
    return jobs, users

def generate_users_with_behavior_patterns(count):
    """リアルな行動パターンを持つユーザー生成（指定ユーザー含む）"""
    import uuid
    from datetime import datetime, timedelta
    import random
    
    patterns = {
        'active': 0.2,      # 20%がアクティブユーザー
        'regular': 0.5,     # 50%が定期的
        'occasional': 0.3   # 30%が時々
    }
    
    users = []
    
    # まず指定された9人のユーザーを追加
    for i, spec_user in enumerate(SPECIFIED_TEST_USERS):
        user = {
            'user_id': str(uuid.uuid4()),
            'email': spec_user['email'],
            'age_range': spec_user['age_range'],
            'gender': spec_user['gender'],
            'is_active': True,
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365)),
            'updated_at': datetime.now()
        }
        users.append(user)
    
    # 残りのユーザーをFakerで生成
    fake = Faker('ja_JP')
    for i in range(len(SPECIFIED_TEST_USERS), count):
        pattern = np.random.choice(list(patterns.keys()), p=list(patterns.values()))
        user = {
            'user_id': str(uuid.uuid4()),
            'email': f'user{i+1}@example.com',
            'age_range': np.random.choice(['20-24', '25-29', '30-34', '35-39']),
            'gender': np.random.choice(['男性', '女性']),
            'is_active': True,
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365)),
            'updated_at': datetime.now()
        }
        users.append(user)
    
    return users

def generate_user_actions_for_test():
    """テストユーザーの応募履歴を生成"""
    import uuid
    from datetime import datetime, timedelta
    import random
    
    actions = []
    
    # 指定された9人のユーザー用の応募履歴
    for i, user in enumerate(SPECIFIED_TEST_USERS):
        # 各ユーザーに5-20件の応募履歴を生成
        num_applications = random.randint(5, 20)
        
        for j in range(num_applications):
            # ニーズに基づいた求人選択
            if user['preferred_needs'] == '日払い':
                salary_type_cd = random.choice([1, 2])  # 時給または日給
                fee = random.randint(0, 1000)
            elif user['preferred_needs'] == '高収入':
                salary_type_cd = 1  # 時給
                fee = random.randint(1000, 5000)
            else:
                salary_type_cd = random.choice([1, 2, 3])
                fee = random.randint(0, 3000)
            
            # 職種に基づいた選択（100単位のコードを使用）
            if user['preferred_occupation'] == 'フード':
                occupation_cd1 = 200  # 飲食・フード
            elif user['preferred_occupation'] == '軽作業':
                occupation_cd1 = 400  # 軽作業・倉庫
            elif user['preferred_occupation'] == '介護':
                occupation_cd1 = 800  # 医療・介護・福祉
            elif user['preferred_occupation'] == '塾':
                occupation_cd1 = 700  # 教育・インストラクター
            else:
                occupation_cd1 = random.choice([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
            
            action = {
                'action_id': str(uuid.uuid4()),
                'user_id': user['email'],  # emailを一時的にuser_idとして使用
                'job_id': random.randint(1000000, 9999999),
                'action_type': 'applied',
                'source_type': 'email',
                'pref_cd': user['pref_cd'],
                'city_cd': user['city_cd'],
                'occupation_cd1': occupation_cd1,
                'occupation_cd2': occupation_cd1,
                'occupation_cd3': occupation_cd1,
                'jobtype_detail': random.randint(1, 10),
                'employment_type_cd': random.choice([1, 3]),  # 1=アルバイト, 3=パートのみ
                'salary_type_cd': salary_type_cd,
                'min_salary': random.randint(1000, 1500),
                'max_salary': random.randint(1500, 2500),
                'station_cd': random.randint(1000000, 9999999),
                'feature_codes': ','.join([str(random.randint(100, 300)) for _ in range(3)]),
                'endcl_cd': f'EX{random.randint(1000000, 9999999):08d}',
                'fee': fee,
                'action_date': datetime.now() - timedelta(days=random.randint(1, 180)),
                'context': {'device': 'mobile', 'source': 'email'}
            }
            actions.append(action)
    
    return actions
```

## 📋 実装ガイドライン（algorithms.md として保存）

```yaml
# アルゴリズム仕様 v1.0

スコアリング:
  基礎スコア:
    時給の重み: 0.35
    アクセスの重み: 0.25
    福利厚生の重み: 0.20
    人気度の重み: 0.20
    正規化方法: z-score → 0-100変換
    
  SEOスコア:
    マッチング: 部分一致
    最大キーワード数: 5
    スコア計算: 検索ボリュームベース
    
  パーソナライズ:
    アルゴリズム: ALS（implicit）
    潜在因子: 20
    正則化: 0.1
    イテレーション: 10

カテゴリ分類:
  判定方法: キーワードマッチング + 動的チェック
  優先順位: 1-14（定義済み）
  最大カテゴリ数: 3

40件選定:
  重複処理: 除外（各求人は1セクションのみ）
  優先順位: TOP5 → 近隣 → 地域 → お得 → 新着
  補充ロジック: スコア順
  最低保証: 20件

メールセクション:
  TOP5: パーソナライズスコア上位
  地域別: 推定都道府県の基礎スコア上位
  近隣: 推定市区町村の人気順
  お得: 特典スコア上位
  新着: 3日以内の投稿日時順

エラー処理:
  バッチ処理: チェックポイント方式
  メール生成: 個別リトライ（最大3回）
  失敗閾値: 10%
  
パフォーマンス:
  メモリ: dtype最適化 + カテゴリ型
  キャッシュ: Supabase Edge Functions
  並列処理: ユーザーバッチ単位
```

## 📊 実装準備完了チェックリスト

### ✅ 即座に実装可能な項目
- [x] スコアリング計算式: 確定済み
- [x] カテゴリ判定ルール: 14カテゴリ定義済み
- [x] 40件選定アルゴリズム: 重複除外・優先順位確定
- [x] メールセクション: 5セクション仕様確定
- [x] エラーハンドリング: チェックポイント方式採用
- [x] データ管理: ソフトデリート + 履歴保持

### 📝 実装時の注意点
1. **ユーザー情報制限**: 応募履歴とメールアドレスのみから推定
2. **メモリ管理**: 10,000ユーザー処理時の4GB制限順守
3. **処理時間**: 30分以内完了必須
4. **テスト優先**: TDD（RED → GREEN → REFACTOR）
5. **継続的検証**: フロントエンドUIで随時確認

これらの回答により、tasks.mdの全タスクが実装可能になりました。