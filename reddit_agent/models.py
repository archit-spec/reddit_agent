"""Data models for the Reddit AI Agent."""

from dataclasses import dataclass

@dataclass
class UtilityMetrics:
    """Metrics used to calculate utility of actions"""
    engagement_rate: float
    sentiment_score: float
    relevance_score: float
    novelty_score: float
