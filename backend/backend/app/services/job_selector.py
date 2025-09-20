#!/usr/bin/env python3
"""T024: Job Selector Service"""
from typing import List, Dict
from app.models.job import Job
from app.models.user import User

class JobSelectorService:
    async def select_editorial_picks(self, jobs: List[Job], user: User) -> List[Job]:
        scored = [(j, j.fee * j.application_clicks) for j in jobs if hasattr(j, "fee") and hasattr(j, "application_clicks")]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [j for j, _ in scored[:5]]

    async def select_top5(self, jobs: List[Job], user: User) -> List[Job]:
        sorted_jobs = sorted(jobs, key=lambda j: getattr(j, "basic_score", 0), reverse=True)
        return sorted_jobs[:5]

    async def select_all_sections(self, jobs: List[Job], user: User) -> Dict[str, List[Job]]:
        used_ids = set()
        sections = {}

        # Editorial picks
        editorial = await self.select_editorial_picks(jobs, user)
        sections["editorial_picks"] = editorial
        used_ids.update(j.job_id for j in editorial)

        # Top 5
        remaining = [j for j in jobs if j.job_id not in used_ids]
        top5 = await self.select_top5(remaining, user)
        sections["top5"] = top5
        used_ids.update(j.job_id for j in top5)

        # Other sections (simplified)
        remaining = [j for j in jobs if j.job_id not in used_ids]
        sections["recommended"] = remaining[:5]
        sections["new_arrivals"] = remaining[5:10]
        sections["popular"] = remaining[10:15]
        sections["personalized"] = remaining[15:20]

        return sections
