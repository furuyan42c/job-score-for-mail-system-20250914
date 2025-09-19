"""
メール配信サービス - T093-T096 メール配信機能のリファクタリング実装
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import random


class EmailService:
    """メール配信関連のビジネスロジック"""

    def __init__(self):
        self.distribution_status = {}
        self.distribution_lists = {}
        self.email_templates = {
            "default": {
                "subject": "{user_name}様へのおすすめ求人情報",
                "header": "こんにちは、{user_name}様\n\nあなたにぴったりの求人が見つかりました！",
                "footer": "\n\n今後ともよろしくお願いいたします。\n求人マッチングサービス"
            }
        }

    def generate_email(self, user_data: Dict[str, Any],
                      job_recommendations: List[Dict[str, Any]],
                      template_id: str = "default") -> Dict[str, Any]:
        """パーソナライズドメールの生成"""

        user_name = user_data.get("name", "ユーザー")
        template = self.email_templates.get(template_id, self.email_templates["default"])

        # テキスト版生成
        body_text = template["header"].format(user_name=user_name)
        body_text += "\n\nおすすめ求人:\n"

        for i, job in enumerate(job_recommendations[:5], 1):  # 最大5件
            body_text += (
                f"\n{i}. {job['title']} ({job['company']})\n"
                f"   場所: {job.get('location', '未指定')}\n"
                f"   給与: {job.get('salary', '要相談')}\n"
                f"   マッチ度: {job.get('match_score', 0)}%\n"
            )

        body_text += template["footer"]

        # HTML版生成
        body_html = self._generate_html_email(user_name, job_recommendations, template)

        # メールサイズの計算
        email_size = len(body_text.encode('utf-8')) + len(body_html.encode('utf-8'))

        return {
            "email": {
                "subject": template["subject"].format(user_name=user_name),
                "body_text": body_text,
                "body_html": body_html,
                "size_bytes": email_size,
                "recipient": user_data.get("email", ""),
                "generated_at": datetime.now().isoformat()
            },
            "metadata": {
                "template_id": template_id,
                "recommendations_count": len(job_recommendations),
                "personalization_fields": ["user_name", "recommendations"]
            }
        }

    def generate_distribution_list(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """配信リストの生成"""

        max_recipients = filters.get("max_recipients", 100)
        min_match_score = filters.get("min_match_score", 70)
        active_users_only = filters.get("active_users_only", True)

        distribution_list = []
        list_id = f"list_{uuid.uuid4().hex[:8]}"

        # ダミーデータ生成（実際はDBから取得）
        num_recipients = min(random.randint(50, 150), max_recipients)

        for i in range(num_recipients):
            recipient = {
                "user_id": i + 1,
                "email": f"user{i+1}@example.com",
                "name": f"ユーザー{i+1}",
                "status": "active" if active_users_only else random.choice(["active", "inactive"]),
                "job_recommendations": []
            }

            # 推奨求人の生成
            num_recommendations = random.randint(1, 5)
            for j in range(num_recommendations):
                score = random.randint(min_match_score, 100)
                recipient["job_recommendations"].append({
                    "job_id": j + 1,
                    "score": score,
                    "title": f"求人{j+1}",
                    "company": f"会社{j+1}"
                })

            # スコアでソート
            recipient["job_recommendations"].sort(key=lambda x: x["score"], reverse=True)
            distribution_list.append(recipient)

        # リストを保存
        self.distribution_lists[list_id] = {
            "id": list_id,
            "recipients": distribution_list,
            "filters": filters,
            "created_at": datetime.now().isoformat()
        }

        return {
            "distribution_list": distribution_list,
            "total_recipients": len(distribution_list),
            "list_id": list_id,
            "filters_applied": filters,
            "created_at": datetime.now().isoformat()
        }

    def simulate_batch_distribution(self, list_id: str, send_rate: int,
                                  total_recipients: int, test_mode: bool = True) -> Dict[str, Any]:
        """バッチ配信のシミュレーション"""

        # 配信時間の計算
        estimated_time = total_recipients / send_rate if send_rate > 0 else 0

        # 成功/失敗のシミュレーション
        failure_rate = 0.02  # 2%の失敗率
        failure_count = int(total_recipients * failure_rate)
        success_count = total_recipients - failure_count

        # ステータスを更新
        self.distribution_status[list_id] = {
            "status": "in_progress" if not test_mode else "simulated",
            "started_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(seconds=estimated_time)).isoformat(),
            "progress": 0
        }

        # キューの状態
        queue_metrics = {
            "queue_size": total_recipients,
            "processed": 0,
            "pending": total_recipients,
            "failed": 0,
            "retry_queue": 0
        }

        return {
            "simulation_results": {
                "estimated_time_seconds": estimated_time,
                "success_count": success_count,
                "failure_count": failure_count,
                "queue_status": "active",
                "send_rate": send_rate,
                "batches_required": (total_recipients // 1000) + 1,
                "test_mode": test_mode,
                "queue_metrics": queue_metrics
            },
            "performance_estimates": {
                "throughput": f"{send_rate} emails/second",
                "completion_time": f"{estimated_time/60:.1f} minutes",
                "success_rate": f"{(success_count/total_recipients)*100:.1f}%"
            }
        }

    def get_distribution_status(self, list_id: str) -> Dict[str, Any]:
        """配信ステータスの取得"""

        if list_id in self.distribution_status:
            status_data = self.distribution_status[list_id]

            # 進捗の計算（シミュレーション）
            if status_data["status"] == "in_progress":
                started = datetime.fromisoformat(status_data["started_at"])
                elapsed = (datetime.now() - started).total_seconds()
                progress = min(100, int(elapsed * 10))  # 10秒で100%
                status_data["progress"] = progress

                if progress >= 100:
                    status_data["status"] = "completed"
                    status_data["completed_at"] = datetime.now().isoformat()
        else:
            status_data = {
                "status": "pending",
                "progress": 0
            }

        return {
            "status": status_data["status"],
            "list_id": list_id,
            "progress": status_data.get("progress", 0),
            "details": status_data
        }

    def analyze_distribution_results(self, distribution_id: str,
                                    start_time: str, end_time: str) -> Dict[str, Any]:
        """配信結果の分析"""

        # ダミーデータ生成（実際は配信ログから集計）
        total_sent = random.randint(9000, 10000)
        delivery_rate = random.uniform(0.96, 0.99)
        open_rate = random.uniform(0.40, 0.55)
        click_rate = random.uniform(0.15, 0.30)
        conversion_rate = click_rate * random.uniform(0.3, 0.5)

        analysis = {
            "total_sent": total_sent,
            "total_delivered": int(total_sent * delivery_rate),
            "total_opened": int(total_sent * open_rate),
            "total_clicked": int(total_sent * click_rate),
            "delivery_rate": round(delivery_rate * 100, 1),
            "open_rate": round(open_rate * 100, 1),
            "click_rate": round(click_rate * 100, 1),
            "conversion_rate": round(conversion_rate * 100, 1),
            "average_open_time_minutes": round(random.uniform(20, 45), 1),
            "peak_engagement_hour": random.randint(9, 11),
            "distribution_id": distribution_id,
            "analysis_period": {
                "start": start_time,
                "end": end_time
            }
        }

        return {"analysis": analysis}

    def get_distribution_analytics(self, distribution_id: str) -> Dict[str, Any]:
        """詳細な配信分析の取得"""

        # エンゲージメント分析
        engagement_breakdown = {
            "by_hour": {
                str(h): random.randint(5, 30)
                for h in range(9, 18)
            },
            "by_job_category": {
                "飲食": random.randint(20, 40),
                "小売": random.randint(15, 35),
                "サービス": random.randint(10, 30),
                "IT": random.randint(15, 30),
                "その他": random.randint(5, 20)
            },
            "by_user_segment": {
                "active": random.randint(50, 70),
                "occasional": random.randint(20, 40),
                "new": random.randint(5, 15),
                "dormant": random.randint(5, 10)
            }
        }

        # 推奨事項の生成
        recommendations = self._generate_recommendations(engagement_breakdown)

        return {
            "distribution_id": distribution_id,
            "performance_summary": {
                "status": "completed",
                "total_recipients": random.randint(9500, 10000),
                "successful_deliveries": random.randint(9200, 9800),
                "engagement_score": round(random.uniform(70, 85), 1),
                "roi_estimate": round(random.uniform(2.5, 4.5), 2)
            },
            "engagement_breakdown": engagement_breakdown,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    # プライベートメソッド
    def _generate_html_email(self, user_name: str, recommendations: List[Dict[str, Any]],
                            template: Dict[str, str]) -> str:
        """HTML形式のメール生成"""

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .job-card {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .job-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
        .job-company {{ color: #7f8c8d; margin: 5px 0; }}
        .match-score {{ color: #27ae60; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ecf0f1; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>こんにちは、{user_name}様</h2>
        <p>あなたにぴったりの求人が見つかりました！</p>

        <div class="recommendations">
"""

        for i, job in enumerate(recommendations[:5], 1):
            html += f"""
            <div class="job-card">
                <div class="job-title">{i}. {job['title']}</div>
                <div class="job-company">{job['company']}</div>
                <div>場所: {job.get('location', '未指定')}</div>
                <div>給与: {job.get('salary', '要相談')}</div>
                <div class="match-score">マッチ度: {job.get('match_score', 0)}%</div>
            </div>
"""

        html += """
        </div>

        <div class="footer">
            <p>今後ともよろしくお願いいたします。</p>
            <p>求人マッチングサービス</p>
            <p style="font-size: 12px; color: #95a5a6;">
                このメールは自動送信されています。<br>
                配信停止をご希望の方は<a href="#">こちら</a>から
            </p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _generate_recommendations(self, engagement_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """配信改善の推奨事項生成"""

        recommendations = []

        # 時間帯の分析
        peak_hour = max(engagement_data["by_hour"], key=engagement_data["by_hour"].get)
        recommendations.append({
            "type": "timing",
            "priority": "high",
            "message": f"{peak_hour}時台の配信が最も効果的です"
        })

        # カテゴリ分析
        top_category = max(engagement_data["by_job_category"],
                          key=engagement_data["by_job_category"].get)
        recommendations.append({
            "type": "content",
            "priority": "medium",
            "message": f"{top_category}カテゴリの求人への関心が高いです"
        })

        # セグメント分析
        top_segment = max(engagement_data["by_user_segment"],
                         key=engagement_data["by_user_segment"].get)
        recommendations.append({
            "type": "segmentation",
            "priority": "medium",
            "message": f"{top_segment}ユーザーのエンゲージメント率が高いです"
        })

        # パフォーマンス向上の提案
        recommendations.append({
            "type": "optimization",
            "priority": "low",
            "message": "件名のA/Bテストを実施することを推奨します"
        })

        return recommendations


# シングルトンインスタンス
email_service = EmailService()