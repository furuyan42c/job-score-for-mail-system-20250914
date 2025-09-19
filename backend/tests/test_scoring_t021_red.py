"""
T021-RED: Failing tests for 3-stage scoring implementation
Tests for basic scoring, keyword scoring, and AI scoring components.
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import the modules we'll implement
from app.scoring.basic_scorer import BasicScorer
from app.scoring.keyword_scorer import KeywordScorer
from app.scoring.ai_scorer import AIScorer
from app.services.scoring_service_t021 import ScoringService


class TestBasicScorer:
    """Tests for BasicScorer - location and category matching."""

    def test_basic_scorer_initialization(self):
        """Test BasicScorer can be initialized."""
        scorer = BasicScorer()
        assert scorer is not None

    def test_score_location_match_exact(self):
        """Test exact location match returns high score."""
        scorer = BasicScorer()
        job_data = {
            "location": "San Francisco, CA",
            "category": "Software Engineering"
        }
        user_preferences = {
            "preferred_location": "San Francisco, CA",
            "preferred_categories": ["Software Engineering"]
        }

        score = scorer.score_location(job_data, user_preferences)
        assert score >= 0.8  # High score for exact match

    def test_score_location_match_partial(self):
        """Test partial location match returns medium score."""
        scorer = BasicScorer()
        job_data = {
            "location": "San Francisco, CA"
        }
        user_preferences = {
            "preferred_location": "San Francisco"
        }

        score = scorer.score_location(job_data, user_preferences)
        assert 0.4 <= score < 0.8  # Medium score for partial match

    def test_score_location_no_match(self):
        """Test no location match returns low score."""
        scorer = BasicScorer()
        job_data = {
            "location": "New York, NY"
        }
        user_preferences = {
            "preferred_location": "San Francisco, CA"
        }

        score = scorer.score_location(job_data, user_preferences)
        assert score < 0.3  # Low score for no match

    def test_score_category_match_exact(self):
        """Test exact category match returns high score."""
        scorer = BasicScorer()
        job_data = {
            "category": "Software Engineering"
        }
        user_preferences = {
            "preferred_categories": ["Software Engineering", "Data Science"]
        }

        score = scorer.score_category(job_data, user_preferences)
        assert score >= 0.8  # High score for exact match

    def test_calculate_basic_score(self):
        """Test overall basic score calculation."""
        scorer = BasicScorer()
        job_data = {
            "location": "San Francisco, CA",
            "category": "Software Engineering"
        }
        user_preferences = {
            "preferred_location": "San Francisco, CA",
            "preferred_categories": ["Software Engineering"]
        }

        score = scorer.calculate_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestKeywordScorer:
    """Tests for KeywordScorer - skills and requirements matching."""

    def test_keyword_scorer_initialization(self):
        """Test KeywordScorer can be initialized."""
        scorer = KeywordScorer()
        assert scorer is not None

    def test_extract_keywords_from_job(self):
        """Test keyword extraction from job description."""
        scorer = KeywordScorer()
        job_data = {
            "title": "Senior Python Developer",
            "description": "We need a developer with Python, Django, and React experience",
            "requirements": "5+ years Python, 3+ years Django"
        }

        keywords = scorer.extract_keywords(job_data)
        assert isinstance(keywords, list)
        assert "python" in [k.lower() for k in keywords]
        assert "django" in [k.lower() for k in keywords]

    def test_match_skills_exact(self):
        """Test exact skill matching returns high score."""
        scorer = KeywordScorer()
        job_keywords = ["Python", "Django", "PostgreSQL"]
        user_skills = ["Python", "Django", "PostgreSQL", "React"]

        score = scorer.match_skills(job_keywords, user_skills)
        assert score >= 0.8  # High score for exact match

    def test_match_skills_partial(self):
        """Test partial skill matching returns medium score."""
        scorer = KeywordScorer()
        job_keywords = ["Python", "Django", "PostgreSQL", "Redis"]
        user_skills = ["Python", "Django"]

        score = scorer.match_skills(job_keywords, user_skills)
        assert 0.3 <= score < 0.8  # Medium score for partial match

    def test_match_skills_no_match(self):
        """Test no skill matching returns low score."""
        scorer = KeywordScorer()
        job_keywords = ["Java", "Spring", "Oracle"]
        user_skills = ["Python", "Django", "PostgreSQL"]

        score = scorer.match_skills(job_keywords, user_skills)
        assert score < 0.3  # Low score for no match

    def test_calculate_keyword_score(self):
        """Test overall keyword score calculation."""
        scorer = KeywordScorer()
        job_data = {
            "title": "Python Developer",
            "description": "Python and Django required",
            "requirements": "3+ years Python"
        }
        user_preferences = {
            "skills": ["Python", "Django", "React"]
        }

        score = scorer.calculate_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestAIScorer:
    """Tests for AIScorer - GPT-based semantic matching."""

    def test_ai_scorer_initialization(self):
        """Test AIScorer can be initialized."""
        scorer = AIScorer()
        assert scorer is not None

    def test_ai_scorer_with_api_key(self):
        """Test AIScorer initialization with API key."""
        scorer = AIScorer(api_key="test-key")
        assert scorer.api_key == "test-key"

    @patch('app.scoring.ai_scorer.openai')
    def test_generate_ai_score_success(self, mock_openai):
        """Test successful AI score generation."""
        mock_openai.ChatCompletion.create.return_value = Mock(
            choices=[Mock(message=Mock(content="0.85"))]
        )

        scorer = AIScorer(api_key="test-key")
        job_data = {
            "title": "Senior Python Developer",
            "description": "Advanced Python development role"
        }
        user_preferences = {
            "experience_level": "Senior",
            "skills": ["Python", "Django"]
        }

        score = scorer.calculate_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @patch('app.scoring.ai_scorer.openai')
    def test_ai_scorer_api_failure(self, mock_openai):
        """Test AI scorer handles API failures gracefully."""
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")

        scorer = AIScorer(api_key="test-key")
        job_data = {"title": "Test Job"}
        user_preferences = {"skills": ["Python"]}

        score = scorer.calculate_score(job_data, user_preferences)
        assert score == 0.0  # Default score on failure

    def test_ai_scorer_without_api_key(self):
        """Test AI scorer returns default score without API key."""
        scorer = AIScorer()
        job_data = {"title": "Test Job"}
        user_preferences = {"skills": ["Python"]}

        score = scorer.calculate_score(job_data, user_preferences)
        assert score == 0.0  # Default score without API key


class TestScoringService:
    """Tests for ScoringService - orchestrates 3-stage scoring."""

    def test_scoring_service_initialization(self):
        """Test ScoringService can be initialized."""
        service = ScoringService()
        assert service is not None
        assert hasattr(service, 'basic_scorer')
        assert hasattr(service, 'keyword_scorer')
        assert hasattr(service, 'ai_scorer')

    def test_calculate_composite_score(self):
        """Test composite score calculation from all three stages."""
        service = ScoringService()
        job_data = {
            "title": "Python Developer",
            "description": "Python development role",
            "location": "San Francisco, CA",
            "category": "Software Engineering"
        }
        user_preferences = {
            "preferred_location": "San Francisco, CA",
            "preferred_categories": ["Software Engineering"],
            "skills": ["Python", "Django"],
            "experience_level": "Mid"
        }

        score = service.calculate_composite_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_get_stage_scores(self):
        """Test getting individual stage scores."""
        service = ScoringService()
        job_data = {
            "title": "Python Developer",
            "description": "Python development role",
            "location": "San Francisco, CA",
            "category": "Software Engineering"
        }
        user_preferences = {
            "preferred_location": "San Francisco, CA",
            "preferred_categories": ["Software Engineering"],
            "skills": ["Python"],
            "experience_level": "Mid"
        }

        scores = service.get_stage_scores(job_data, user_preferences)
        assert isinstance(scores, dict)
        assert "basic_score" in scores
        assert "keyword_score" in scores
        assert "ai_score" in scores
        assert all(0.0 <= score <= 1.0 for score in scores.values())

    def test_scoring_service_with_weights(self):
        """Test scoring service with custom weights."""
        weights = {
            "basic_weight": 0.4,
            "keyword_weight": 0.4,
            "ai_weight": 0.2
        }
        service = ScoringService(weights=weights)

        job_data = {"title": "Test Job", "location": "Test City"}
        user_preferences = {"skills": ["Python"]}

        score = service.calculate_composite_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_scoring_service_batch_processing(self):
        """Test batch scoring of multiple jobs."""
        service = ScoringService()
        jobs = [
            {"id": 1, "title": "Python Developer", "location": "SF"},
            {"id": 2, "title": "Java Developer", "location": "NYC"},
            {"id": 3, "title": "Data Scientist", "location": "LA"}
        ]
        user_preferences = {
            "skills": ["Python"],
            "preferred_location": "SF"
        }

        scores = service.score_jobs_batch(jobs, user_preferences)
        assert isinstance(scores, list)
        assert len(scores) == len(jobs)
        assert all(isinstance(score, dict) for score in scores)
        assert all("job_id" in score and "composite_score" in score for score in scores)


# Edge cases and error handling
class TestScoringEdgeCases:
    """Test edge cases and error handling in scoring system."""

    def test_empty_job_data(self):
        """Test handling of empty job data."""
        service = ScoringService()
        job_data = {}
        user_preferences = {"skills": ["Python"]}

        score = service.calculate_composite_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_empty_user_preferences(self):
        """Test handling of empty user preferences."""
        service = ScoringService()
        job_data = {"title": "Python Developer"}
        user_preferences = {}

        score = service.calculate_composite_score(job_data, user_preferences)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_invalid_weights(self):
        """Test handling of invalid weight configurations."""
        with pytest.raises(ValueError):
            ScoringService(weights={
                "basic_weight": 0.3,
                "keyword_weight": 0.3,
                "ai_weight": 0.3  # Sum = 0.9, should equal 1.0
            })

    def test_negative_weights(self):
        """Test handling of negative weights."""
        with pytest.raises(ValueError):
            ScoringService(weights={
                "basic_weight": -0.1,
                "keyword_weight": 0.6,
                "ai_weight": 0.5
            })