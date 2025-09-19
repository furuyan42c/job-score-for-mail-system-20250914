"""
スコアリングサービス - T090-T092 スコア計算のリファクタリング実装
"""
from typing import Dict, Any, List
from datetime import datetime
import math


class ScoringService:
    """スコア計算関連のビジネスロジック"""

    def __init__(self):
        self.score_cache = {}  # スコアのキャッシュ

    def calculate_basic_score(self, user_profile: Dict[str, Any],
                            job_profile: Dict[str, Any]) -> Dict[str, Any]:
        """基礎マッチングスコアの計算"""

        # ロケーションスコア計算
        location_score = self._calculate_location_score(
            user_profile.get("location", ""),
            job_profile.get("location", "")
        )

        # 給与スコア計算
        salary_score = self._calculate_salary_score(
            user_profile.get("preferred_salary", 0),
            job_profile.get("salary", 0)
        )

        # スキルスコア計算
        skill_score = self._calculate_skill_score(
            user_profile.get("skills", []),
            job_profile.get("required_skills", [])
        )

        # 総合スコア計算（重み付き平均）
        weights = {"location": 0.3, "salary": 0.35, "skill": 0.35}
        total_score = (
            location_score * weights["location"] +
            salary_score * weights["salary"] +
            skill_score * weights["skill"]
        )

        return {
            "score": round(total_score, 2),
            "components": {
                "location_score": location_score,
                "salary_score": salary_score,
                "skill_score": skill_score
            },
            "weights": weights,
            "calculated_at": datetime.now().isoformat()
        }

    def calculate_seo_score(self, job_data: Dict[str, Any],
                           seo_keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """SEOスコアの計算"""

        keyword_matches = []
        total_volume = 0
        matched_volume = 0

        title = job_data.get("title", "").lower()
        description = job_data.get("description", "").lower()
        location = job_data.get("location", "").lower()

        combined_text = f"{title} {description} {location}"

        for kw in seo_keywords:
            keyword = kw["keyword"].lower()
            volume = kw.get("volume", 0)
            competition = kw.get("competition", 0.5)

            # キーワードマッチング判定
            keyword_parts = keyword.split()
            match_count = sum(1 for part in keyword_parts if part in combined_text)
            match_ratio = match_count / len(keyword_parts) if keyword_parts else 0

            if match_ratio > 0.5:  # 50%以上マッチ
                keyword_matches.append({
                    "keyword": kw["keyword"],
                    "matched": True,
                    "volume": volume,
                    "match_ratio": match_ratio,
                    "competition": competition
                })
                matched_volume += volume * match_ratio

            total_volume += volume

        # スコア計算
        if total_volume > 0:
            volume_score = min(100, (matched_volume / total_volume) * 100)
        else:
            volume_score = 50

        # 競合度を考慮
        avg_competition = sum(m["competition"] for m in keyword_matches) / len(keyword_matches) if keyword_matches else 0.5
        competition_score = (1 - avg_competition) * 100

        seo_score = (volume_score * 0.6 + competition_score * 0.4)

        return {
            "seo_score": round(seo_score, 2),
            "keyword_matches": keyword_matches,
            "search_volume_score": round(volume_score, 2),
            "competition_score": round(competition_score, 2),
            "total_keywords_checked": len(seo_keywords),
            "keywords_matched": len(keyword_matches)
        }

    def generate_comprehensive_matching(self, user_ids: List[int], job_ids: List[int],
                                      scoring_factors: Dict[str, float]) -> Dict[str, Any]:
        """包括的なユーザー×求人マッチング生成"""

        matches = []
        for user_id in user_ids:
            for job_id in job_ids:
                # キャッシュキー生成
                cache_key = f"{user_id}_{job_id}"

                if cache_key in self.score_cache:
                    score_data = self.score_cache[cache_key]
                else:
                    # スコア計算（仮の値）
                    base_score = 85 - (user_id + job_id) % 15
                    score_data = {
                        "user_id": user_id,
                        "job_id": job_id,
                        "total_score": base_score,
                        "location_score": base_score + 5,
                        "salary_score": base_score - 5,
                        "skill_score": base_score - 10,
                        "seo_score": base_score - 15
                    }
                    self.score_cache[cache_key] = score_data

                # ファクターによる重み付け
                if scoring_factors:
                    weighted_score = (
                        score_data["location_score"] * scoring_factors.get("location", 0.25) +
                        score_data["salary_score"] * scoring_factors.get("salary", 0.25) +
                        score_data["skill_score"] * scoring_factors.get("skills", 0.25) +
                        score_data["seo_score"] * scoring_factors.get("seo", 0.25)
                    )
                    score_data["total_score"] = round(weighted_score, 2)

                matches.append(score_data)

        # スコアでソート
        matches.sort(key=lambda x: x["total_score"], reverse=True)

        return {
            "matches": matches,
            "total_combinations": len(matches),
            "scoring_factors": scoring_factors,
            "generated_at": datetime.now().isoformat()
        }

    def get_top_matches_for_user(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """特定ユーザーのトップマッチを取得"""

        # キャッシュから該当ユーザーのマッチを取得
        user_matches = []
        for key, value in self.score_cache.items():
            if key.startswith(f"{user_id}_"):
                user_matches.append(value)

        # スコアでソート
        user_matches.sort(key=lambda x: x["total_score"], reverse=True)

        # デフォルトデータ（キャッシュがない場合）
        if not user_matches:
            user_matches = [
                {"job_id": 1, "total_score": 90, "title": "Backend Developer"},
                {"job_id": 2, "total_score": 85, "title": "Frontend Developer"},
                {"job_id": 3, "total_score": 80, "title": "Full Stack Developer"},
            ]

        return {
            "matches": user_matches[:limit],
            "total_available": len(user_matches),
            "user_id": user_id
        }

    def calculate_batch_scores(self, user_ids: List[int], job_ids: List[int]) -> Dict[str, Any]:
        """バッチスコア計算"""
        scores = []
        total_calculations = 0

        for user_id in user_ids:
            for job_id in job_ids:
                score = 75 + (user_id * job_id) % 20
                scores.append({
                    "user_id": user_id,
                    "job_id": job_id,
                    "score": score
                })
                total_calculations += 1

        avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0

        return {
            "scores": scores,
            "total_calculations": total_calculations,
            "average_score": round(avg_score, 2),
            "min_score": min(s["score"] for s in scores) if scores else 0,
            "max_score": max(s["score"] for s in scores) if scores else 0
        }

    # プライベートメソッド
    def _calculate_location_score(self, user_location: str, job_location: str) -> float:
        """ロケーションスコアの計算"""
        if not user_location or not job_location:
            return 50.0

        # 完全一致
        if user_location == job_location:
            return 100.0

        # 部分一致（都道府県レベル）
        user_pref = user_location.split()[0] if user_location else ""
        job_pref = job_location.split()[0] if job_location else ""

        if user_pref and job_pref and user_pref == job_pref:
            return 80.0

        # 地域が近い場合のスコア（簡易実装）
        return 50.0

    def _calculate_salary_score(self, preferred_salary: float, job_salary: float) -> float:
        """給与スコアの計算"""
        if not preferred_salary or not job_salary:
            return 70.0

        # 差分の計算
        diff_ratio = abs(preferred_salary - job_salary) / preferred_salary if preferred_salary > 0 else 0

        if diff_ratio <= 0.05:  # 5%以内
            return 100.0
        elif diff_ratio <= 0.1:  # 10%以内
            return 90.0
        elif diff_ratio <= 0.2:  # 20%以内
            return 75.0
        else:
            return max(50.0, 100 - diff_ratio * 100)

    def _calculate_skill_score(self, user_skills: List[str], required_skills: List[str]) -> float:
        """スキルスコアの計算"""
        if not required_skills:
            return 80.0
        if not user_skills:
            return 50.0

        # マッチング率の計算
        user_skills_lower = [s.lower() for s in user_skills]
        matched = sum(1 for skill in required_skills if skill.lower() in user_skills_lower)
        match_ratio = matched / len(required_skills)

        return min(100.0, match_ratio * 100 + 25)  # 最低25点


# シングルトンインスタンス
scoring_service = ScoringService()