"""
AI Scorer - Stage 3 of 3-stage scoring system.
Handles semantic matching using GPT-based analysis (optional).
"""
from typing import Dict, Any, Optional
import json
import logging

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

logger = logging.getLogger(__name__)


class AIScorer:
    """AI scorer for semantic job-user matching using GPT."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize AIScorer.

        Args:
            api_key: OpenAI API key (optional)
            model: OpenAI model to use for scoring
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        self.max_tokens = 10
        self.temperature = 0.1
        self.fallback_score = 0.0

        if self.api_key and OPENAI_AVAILABLE:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info(f"AIScorer initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def _create_prompt(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """
        Create prompt for GPT-based scoring.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            Formatted prompt string
        """
        job_summary = f"""
Job Title: {job_data.get('title', 'Unknown')}
Description: {job_data.get('description', 'No description')[:500]}
Requirements: {job_data.get('requirements', 'No requirements')[:300]}
Location: {job_data.get('location', 'Unknown')}
Category: {job_data.get('category', 'Unknown')}
"""

        user_summary = f"""
Experience Level: {user_preferences.get('experience_level', 'Unknown')}
Skills: {', '.join(user_preferences.get('skills', []))}
Preferred Location: {user_preferences.get('preferred_location', 'Unknown')}
Preferred Categories: {', '.join(user_preferences.get('preferred_categories', []))}
"""

        prompt = f"""
You are an expert job matching system. Analyze the job and user profile below and provide a compatibility score.

{job_summary}

User Profile:
{user_summary}

Consider:
1. Skill alignment and transferability
2. Experience level compatibility
3. Career growth potential
4. Cultural and role fit
5. Long-term career alignment

Respond with only a decimal number between 0.0 and 1.0 representing the compatibility score.
Do not include any explanation, just the number.
"""
        return prompt

    def calculate_score(self, job_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
        """
        Calculate AI-based compatibility score.

        Args:
            job_data: Job information
            user_preferences: User preferences

        Returns:
            AI-generated score between 0.0 and 1.0, or 0.0 if AI is not available
        """
        # Return default score if no API key or OpenAI not available
        if not self.api_key or not OPENAI_AVAILABLE or not self.client:
            logger.debug("AI scoring not available, returning fallback score")
            return self.fallback_score

        try:
            prompt = self._create_prompt(job_data, user_preferences)

            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a job matching expert. Respond only with a number between 0.0 and 1.0."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            score_text = response.choices[0].message.content.strip()

            # Parse the score
            try:
                score = float(score_text)
                # Ensure score is within valid range
                return max(0.0, min(1.0, score))
            except ValueError:
                logger.warning(f"Could not parse AI score: {score_text}")
                return 0.0

        except Exception as e:
            logger.warning(f"AI scoring failed: {e}")
            return self.fallback_score

    def set_fallback_score(self, score: float) -> None:
        """
        Set the fallback score for when AI is not available.

        Args:
            score: Fallback score between 0.0 and 1.0
        """
        if 0.0 <= score <= 1.0:
            self.fallback_score = score
        else:
            raise ValueError("Fallback score must be between 0.0 and 1.0")