#!/usr/bin/env python3
"""T022: SEO Scoring Service"""
from typing import List, Dict, Any
from app.models.job import Job

class SEOScoringService:
    def __init__(self):
        self.field_weights = {"application_name": 1.5, "title": 1.2, "description": 1.0, "company": 0.8}

    async def normalize_keywords(self, keywords: List[str]) -> List[str]:
        return [k.lower().replace("-", " ").replace("_", " ") for k in keywords]

    async def generate_variations(self, keyword: str) -> List[str]:
        return [keyword, keyword.replace(" ", "-"), keyword.replace(" ", "_"), keyword.replace(" ", "")]

    async def calculate_seo_score(self, job: Job, semrush_keywords: List[Dict[str, Any]]) -> float:
        total_score = 0.0
        for kw_data in semrush_keywords:
            keyword = kw_data["keyword"].lower()
            volume = kw_data.get("search_volume", 1000)
            scores = []
            if hasattr(job, "application_name") and job.application_name and keyword in job.application_name.lower():
                scores.append(self.field_weights["application_name"])
            if hasattr(job, "title") and job.title and keyword in job.title.lower():
                scores.append(self.field_weights["title"])
            if scores:
                total_score += max(scores) * min(volume / 10000, 1.0) * 100
        return min(100, total_score)
