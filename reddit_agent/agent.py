"""Main Reddit AI Agent implementation."""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import praw
import prawcore

from .models import UtilityMetrics
from .database import Database
from .analysis import ContentAnalyzer

logger = logging.getLogger(__name__)

class RedditAIAgent:
    """
    A utility-based learning agent for Reddit analysis that combines multiple agent types:
    - Model-based: Maintains internal state of subreddit patterns
    - Utility-based: Uses utility functions to make optimal decisions
    - Learning: Adapts behavior based on past interactions
    - Goal-based: Works towards specific objectives
    """
    
    def __init__(self, db_path: str = "reddit_memory.db"):
        """Initialize the Reddit AI Agent."""
        try:
            # Initialize Reddit client using environment variables
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT'),
                username=os.getenv('REDDIT_USERNAME'),
            )
            
            # Test the Reddit connection
            self.reddit.user.me()
            logger.info("Successfully connected to Reddit API")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {str(e)}")
            raise
        
        # Initialize components
        self.db = Database(db_path)
        self.analyzer = ContentAnalyzer()
        
        # Internal state for model-based reasoning
        self.subreddit_models = defaultdict(dict)
        self.learning_rate = float(os.getenv('LEARNING_RATE', '0.1'))
        self.utility_weights = {
            'engagement': float(os.getenv('WEIGHT_ENGAGEMENT', '0.4')),
            'sentiment': float(os.getenv('WEIGHT_SENTIMENT', '0.2')),
            'relevance': float(os.getenv('WEIGHT_RELEVANCE', '0.2')),
            'novelty': float(os.getenv('WEIGHT_NOVELTY', '0.2'))
        }
    
    def calculate_utility(self, metrics: UtilityMetrics) -> float:
        """
        Calculate utility score based on multiple metrics.
        Uses weighted sum of normalized metrics.
        """
        return (
            self.utility_weights['engagement'] * metrics.engagement_rate +
            self.utility_weights['sentiment'] * metrics.sentiment_score +
            self.utility_weights['relevance'] * metrics.relevance_score +
            self.utility_weights['novelty'] * metrics.novelty_score
        )
    
    def process_subreddit(self, subreddit_name: str, limit: int = 10) -> List[Dict]:
        """Process submissions from a subreddit and learn from them."""
        try:
            # Validate subreddit exists and is accessible
            subreddit = self.reddit.subreddit(subreddit_name)
            # Try to access subreddit info to verify it exists
            subreddit_type = subreddit.subreddit_type
            if subreddit_type == "private":
                logger.error(f"Subreddit {subreddit_name} is private and cannot be accessed")
                return []
            
            processed_submissions = []
            
            for submission in subreddit.new(limit=limit):
                try:
                    if not self.db.is_submission_processed(submission.id):
                        # Analyze submission
                        analysis = self.analyzer.analyze_submission(submission)
                        
                        # Calculate utility metrics
                        metrics = UtilityMetrics(
                            engagement_rate=self.analyzer.calculate_engagement_rate(submission),
                            sentiment_score=analysis['sentiment'],
                            relevance_score=self.analyzer.calculate_relevance(submission, analysis),
                            novelty_score=self.analyzer.calculate_novelty(submission, analysis)
                        )
                        
                        # Calculate overall utility
                        utility_score = self.calculate_utility(metrics)
                        
                        # Store submission with utility score
                        self.db.store_submission(submission, analysis, utility_score)
                        
                        # Update internal model
                        self.update_model(subreddit_name, {
                            'avg_engagement': metrics.engagement_rate,
                            'avg_sentiment': metrics.sentiment_score,
                            'avg_relevance': metrics.relevance_score,
                            'avg_novelty': metrics.novelty_score
                        })
                        
                        # Learn from high-utility submissions
                        if utility_score > 0.7:  # Only learn from high-quality submissions
                            self._learn_from_submission(submission, analysis, utility_score)
                        
                        processed_submissions.append({
                            'id': submission.id,
                            'title': submission.title,
                            'utility_score': utility_score,
                            'metrics': metrics.__dict__
                        })
                except Exception as e:
                    logger.error(f"Error processing submission {submission.id}: {str(e)}")
                    continue
            
            return processed_submissions
            
        except prawcore.exceptions.Redirect:
            logger.error(f"Subreddit {subreddit_name} does not exist")
            return []
        except prawcore.exceptions.Forbidden:
            logger.error(f"Access to subreddit {subreddit_name} is forbidden")
            return []
        except Exception as e:
            logger.error(f"Error processing subreddit {subreddit_name}: {str(e)}")
            return []
    
    def update_model(self, subreddit: str, new_data: Dict):
        """Update internal model for a subreddit based on new observations."""
        if subreddit not in self.subreddit_models:
            self.subreddit_models[subreddit] = new_data
        else:
            for key, value in new_data.items():
                if key == 'topics':  # Handle topics list separately
                    self.subreddit_models[subreddit][key] = value
                else:
                    try:
                        old_value = float(self.subreddit_models[subreddit].get(key, 0))
                        new_value = float(value)
                        self.subreddit_models[subreddit][key] = (
                            (1 - self.learning_rate) * old_value +
                            self.learning_rate * new_value
                        )
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not update model for key {key}: {str(e)}")
                        self.subreddit_models[subreddit][key] = value
    
    def _learn_from_submission(self, submission, analysis: Dict, utility_score: float):
        """Learn patterns from high-utility submissions."""
        pattern_data = {
            'title_length': len(submission.title),
            'content_length': len(submission.selftext),
            'post_time': datetime.fromtimestamp(submission.created_utc).hour,
            'topics': analysis['topics']
        }
        
        self.db.store_pattern(
            subreddit=str(submission.subreddit),
            pattern_type="successful_post",
            pattern_data=pattern_data,
            confidence=utility_score
        )
    
    def get_recommendations(self, subreddit: str) -> List[Dict]:
        """Generate recommendations based on learned patterns."""
        patterns = self.db.get_patterns(subreddit)
        model_data = self.subreddit_models.get(subreddit, {})
        
        recommendations = []
        if patterns and model_data:
            # Analyze patterns to generate recommendations
            best_patterns = sorted(
                patterns,
                key=lambda x: x['confidence'],
                reverse=True
            )[:5]
            
            for pattern in best_patterns:
                recommendations.append({
                    'type': pattern['pattern_type'],
                    'confidence': pattern['confidence'],
                    'suggestion': self._generate_suggestion(pattern, model_data)
                })
        
        return recommendations
    
    def _generate_suggestion(self, pattern: Dict, model_data: Dict) -> str:
        """Generate actionable suggestions based on patterns and model data."""
        pattern_data = pattern['pattern_data']
        
        if pattern['pattern_type'] == 'successful_post':
            return (
                f"Consider posting during hour {pattern_data['post_time']} "
                f"with content length around {pattern_data['content_length']} characters "
                f"focusing on topics: {', '.join(pattern_data['topics'])}"
            )
        
        return "No specific suggestion available"
