"""
T093: メール生成テスト
"""

import sqlite3
from datetime import datetime

def generate_email_html(user_id):
    """ユーザー用のHTMLメールを生成"""
    
    conn = sqlite3.connect('development.db')
    cursor = conn.cursor()
    
    # ユーザー情報取得
    cursor.execute("SELECT email, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return None
    
    email, name = user
    
    # マッチング求人取得（セクション別）
    cursor.execute("""
        SELECT j.job_title, j.company_name, j.salary_min, j.salary_max, 
               m.section, js.total_score
        FROM user_job_matches m
        JOIN jobs j ON m.job_id = j.id
        LEFT JOIN job_scores js ON j.id = js.job_id
        WHERE m.user_id = ?
        ORDER BY m.section, js.total_score DESC
        LIMIT 40
    """, (user_id,))
    
    matches = cursor.fetchall()
    
    # HTML生成
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>あなたにおすすめの求人情報</title>
    <style>
        body {{ font-family: 'Hiragino Sans', sans-serif; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; }}
        .section {{ margin: 20px 0; }}
        .job-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
        .salary {{ color: #FF5722; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>こんにちは、{name or 'ユーザー'}様</h1>
        <p>本日のおすすめ求人をお届けします！</p>
    </div>
    
    <div class="section">
        <h2>🎯 トップピック（あなたにぴったり）</h2>
"""
    
    sections = {
        'top_picks': '🎯 トップピック',
        'high_salary': '💰 高時給求人',
        'nearby': '📍 近場の求人',
        'popular': '⭐ 人気の求人',
        'new': '🆕 新着求人',
        'recommended': '👍 おすすめ求人'
    }
    
    current_section = None
    for match in matches[:20]:  # 最初の20件
        job_title, company, sal_min, sal_max, section, score = match
        
        if section != current_section:
            if current_section:
                html += "</div>"
            current_section = section
            html += f'<div class="section"><h2>{sections.get(section, section)}</h2>'
        
        html += f"""
        <div class="job-card">
            <h3>{job_title or '求人'}</h3>
            <p>{company or '企業'}</p>
            <p class="salary">時給: ¥{sal_min or 1000}〜¥{sal_max or 2000}</p>
            <p>マッチ度: {score:.0f}%</p>
        </div>
        """
    
    html += """
    </div>
    <div style="text-align: center; margin: 30px;">
        <a href="#" style="background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px;">
            もっと見る
        </a>
    </div>
</body>
</html>
"""
    
    conn.close()
    return html

# テスト実行
print("=" * 60)
print("メール生成テスト")
print("=" * 60)

# ユーザー1のメール生成
html = generate_email_html(3)
if html:
    # ファイル保存
    with open('sample_email.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ メール生成成功")
    print(f"   ファイルサイズ: {len(html) / 1024:.1f}KB")
    print("   保存先: sample_email.html")
else:
    print("❌ メール生成失敗")

print("=" * 60)
