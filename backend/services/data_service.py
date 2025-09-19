"""
データ管理サービス - T086-T090 データ操作のリファクタリング実装
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataService:
    """データ管理関連のビジネスロジック"""

    def __init__(self):
        # インメモリデータストア
        self.master_data = {
            "prefectures": [],
            "categories": [],
            "seo_keywords": []
        }
        self.jobs = [
            {"id": 1, "title": "Backend Developer", "company": "Tech Corp",
             "description": "Python developer needed", "salary": 500000},
            {"id": 2, "title": "Frontend Developer", "company": "Web Inc",
             "description": "React developer needed", "salary": 450000},
        ]
        self.job_id_counter = 3

    # マスタデータ管理
    def load_prefectures(self, prefectures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """都道府県マスタデータの読み込み"""
        self.master_data["prefectures"] = prefectures
        return {
            "loaded": len(prefectures),
            "timestamp": datetime.now().isoformat()
        }

    def load_categories(self, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """カテゴリマスタデータの読み込み"""
        self.master_data["categories"] = categories
        return {
            "loaded": len(categories),
            "timestamp": datetime.now().isoformat()
        }

    def load_seo_keywords(self, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """SEOキーワードデータの読み込み"""
        self.master_data["seo_keywords"] = keywords
        return {
            "loaded": len(keywords),
            "timestamp": datetime.now().isoformat()
        }

    def get_seo_keywords(self) -> Dict[str, Any]:
        """SEOキーワードデータの取得"""
        return {
            "keywords": self.master_data["seo_keywords"],
            "total": len(self.master_data["seo_keywords"])
        }

    # 求人データ管理
    def import_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """求人データのインポート"""
        imported = 0
        for job in jobs:
            job["id"] = self.job_id_counter
            job["imported_at"] = datetime.now().isoformat()
            self.jobs.append(job)
            self.job_id_counter += 1
            imported += 1

        return {
            "imported": imported,
            "total_jobs": len(self.jobs),
            "timestamp": datetime.now().isoformat()
        }

    def get_jobs(self) -> Dict[str, Any]:
        """求人リストの取得"""
        return {"jobs": self.jobs}

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """IDによる求人取得"""
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        return None

    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """求人の作成"""
        job_data["id"] = self.job_id_counter
        job_data["created_at"] = datetime.now().isoformat()
        self.jobs.append(job_data)
        self.job_id_counter += 1
        return job_data

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """求人の更新"""
        for job in self.jobs:
            if job["id"] == job_id:
                job.update(update_data)
                job["updated_at"] = datetime.now().isoformat()
                return job
        return None

    def delete_job(self, job_id: int) -> bool:
        """求人の削除"""
        original_count = len(self.jobs)
        self.jobs = [job for job in self.jobs if job["id"] != job_id]
        return len(self.jobs) < original_count

    # データ検証
    def validate_data_integrity(self) -> Dict[str, Any]:
        """データ整合性の検証"""
        master_count = len(self.master_data["prefectures"]) + len(self.master_data["categories"])
        job_count = len(self.jobs)

        # 参照整合性チェックのシミュレーション
        referential_issues = []
        for job in self.jobs:
            if "category" in job and job["category"] not in [c.get("name", "") for c in self.master_data["categories"]]:
                referential_issues.append(f"Job {job['id']}: invalid category")

        return {
            "validation_results": {
                "master_data": {
                    "status": "valid" if master_count > 0 else "empty",
                    "count": master_count
                },
                "job_data": {
                    "status": "valid" if job_count > 0 else "empty",
                    "count": job_count
                },
                "referential_integrity": {
                    "status": "valid" if len(referential_issues) == 0 else "issues_found",
                    "issues": len(referential_issues),
                    "details": referential_issues[:5]  # 最初の5件のみ
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def check_orphaned_records(self) -> Dict[str, Any]:
        """孤立レコードのチェック"""
        orphaned = []

        # カテゴリが存在しない求人をチェック
        valid_categories = [c.get("name", "") for c in self.master_data["categories"]]
        for job in self.jobs:
            if "category" in job and valid_categories and job["category"] not in valid_categories:
                orphaned.append({
                    "type": "job",
                    "id": job["id"],
                    "reason": "invalid_category"
                })

        return {
            "orphaned_records": len(orphaned),
            "details": orphaned[:10]  # 最初の10件のみ
        }


# シングルトンインスタンス
data_service = DataService()