"""Reddit AI Agent Package

A utility-based learning agent for Reddit analysis that combines multiple agent types:
- Model-based: Maintains internal state of subreddit patterns
- Utility-based: Uses utility functions to make optimal decisions
- Learning: Adapts behavior based on past interactions
- Goal-based: Works towards specific objectives
"""

from .agent import RedditAIAgent
from .models import UtilityMetrics

__version__ = "0.1.0"
__all__ = ["RedditAIAgent", "UtilityMetrics"]
