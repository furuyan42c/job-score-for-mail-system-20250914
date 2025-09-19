"""
Keyword Scorer - Stage 2 of 3-stage scoring system.
Handles skills and requirements matching using keyword extraction and comparison.
"""
from typing import Dict, Any, List, Set
import re


class KeywordScorer:
    """Keyword scorer for skills and requirements matching."""

    def __init__(self):
        """Initialize KeywordScorer."""
        # Common technical keywords for extraction
        self.tech_keywords = {
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node', 'django', 'flask', 'spring', 'express', 'postgresql', 'mysql',
            'mongodb', 'redis', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'ci/cd', 'agile', 'scrum', 'html', 'css', 'sql', 'nosql',
            'rest', 'api', 'microservices', 'devops', 'linux', 'unix', 'bash'
        }

    def extract_keywords(self, job_data: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from job title, description, and requirements.

        Args:
            job_data: Job information containing title, description, requirements

        Returns:
            List of extracted keywords
        """
        text_fields = [
            job_data.get("title", ""),
            job_data.get("description", ""),
            job_data.get("requirements", "")
        ]

        # Combine all text and normalize
        combined_text = " ".join(text_fields).lower()

        # Extract words
        words = re.findall(r'\b\w+\b', combined_text)

        # Filter for technical keywords and common patterns
        keywords = []
        for word in words:
            if word in self.tech_keywords:
                keywords.append(word)
            # Add patterns for years of experience
            elif re.match(r'\d+\+?', word):
                keywords.append(word)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def match_skills(self, job_keywords: List[str], user_skills: List[str]) -> float:
        """
        Match job keywords against user skills.

        Args:
            job_keywords: Keywords extracted from job
            user_skills: User's skills list

        Returns:
            Match score between 0.0 and 1.0
        """
        if not job_keywords or not user_skills:
            return 0.0

        # Normalize to lowercase sets
        job_set = set(keyword.lower().strip() for keyword in job_keywords)
        user_set = set(skill.lower().strip() for skill in user_skills)

        # Calculate intersection
        matches = job_set.intersection(user_set)

        if not matches:
            return 0.0

        # Score based on percentage of job keywords matched
        match_ratio = len(matches) / len(job_set)

        # Bonus for having more skills than required
        skill_bonus = min(len(user_set) / len(job_set), 1.2) if len(job_set) > 0 else 1.0

        score = match_ratio * skill_bonus

        return min(score, 1.0)

    def calculate_score(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Calculate overall keyword score.

        Args:
            job_data: Job information
            user_preferences: User preferences containing skills

        Returns:
            Keyword match score between 0.0 and 1.0
        """
        job_keywords = self.extract_keywords(job_data)
        user_skills = user_preferences.get("skills", [])

        return self.match_skills(job_keywords, user_skills)