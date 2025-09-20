#!/usr/bin/env python3
"""T025: Duplicate Control Service"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.models.job import Job

class DuplicateControlService:
    def __init__(self):
        self.window_days = 14

    async def filter_duplicates(self, jobs: List[Job], applications: List[Dict[str, Any]]) -> List[Job]:
        if not applications:
            return jobs

        # Get companies applied to within 2 weeks
        now = datetime.now()
        recent_companies = set()

        for app in applications:
            applied_at = app["applied_at"]
            if isinstance(applied_at, str):
                applied_at = datetime.fromisoformat(applied_at)

            days_ago = (now - applied_at).days
            if days_ago < self.window_days:
                recent_companies.add(app["company_id"])

        # Filter out jobs from recent companies
        return [j for j in jobs if getattr(j, "company_id", None) not in recent_companies]
