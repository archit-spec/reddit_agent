"""LLM integration for enhanced content analysis."""

import os
from typing import Dict, List, Tuple
import logging
import json
from groq import Groq

logger = logging.getLogger(__name__)

def safe_parse_json(json_str: str) -> Dict:
    """Safely parse JSON string, handling common LLM response issues."""
    try:
        # Try to parse as-is first
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Try to find JSON object within the text
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_obj = json_str[start_idx:end_idx]
                return json.loads(json_obj)
        except (json.JSONDecodeError, ValueError):
            pass
    
    logger.error(f"Failed to parse LLM response: {json_str}")
    return {}

class LLMAnalyzer:
    """Handles LLM-based content analysis using Groq."""
    
    def __init__(self):
        """Initialize the LLM analyzer."""
        self.client = Groq()
        self.model = os.getenv('GROQ_MODEL', 'llama3-8b-8192')
    
    def _get_completion(self, prompt: str, temperature: float = 0.7) -> str:
        """Get completion from Groq API."""
        try:
            messages = [
                {"role": "system", "content": """You are a helpful AI that provides analysis in JSON format. Always ensure your responses are valid JSON objects.
                When analyzing relevance, be inclusive rather than exclusive - if there's any possibility the content could be relevant, mark it as relevant."""},
                {"role": "user", "content": prompt}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            response = completion.choices[0].message.content
            logger.debug(f"LLM Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error getting LLM completion: {str(e)}")
            return "{}"
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using LLM."""
        prompt = f"""Analyze the sentiment of the following text and return a score between 0 and 1,
        where 0 is extremely negative and 1 is extremely positive. Return only the numeric score.
        
        Text: {text}"""
        
        try:
            response = self._get_completion(prompt, temperature=0.3)
            return float(response.strip())
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing sentiment score: {str(e)}")
            return 0.5
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text using LLM."""
        prompt = f"""Extract the main topics from the following text. Return only a comma-separated list of topics,
        with no additional text or punctuation.
        
        Text: {text}"""
        
        try:
            response = self._get_completion(prompt, temperature=0.5)
            topics = [topic.strip() for topic in response.split(',')]
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return ['general']
    
    def calculate_relevance(self, text: str, subreddit: str) -> float:
        """Calculate relevance of text to subreddit using LLM."""
        prompt = f"""On a scale of 0 to 1, how relevant is this text to the {subreddit} subreddit?
        Consider the typical content and discussions in this subreddit. Return only the numeric score.
        
        Text: {text}"""
        
        try:
            response = self._get_completion(prompt, temperature=0.3)
            return float(response.strip())
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing relevance score: {str(e)}")
            return 0.5
    
    def calculate_novelty(self, text: str, subreddit: str) -> float:
        """Calculate novelty of text for subreddit using LLM."""
        prompt = f"""On a scale of 0 to 1, how novel or unique is this content for the {subreddit} subreddit?
        Consider common topics and patterns in this subreddit. Return only the numeric score.
        
        Text: {text}"""
        
        try:
            response = self._get_completion(prompt, temperature=0.3)
            return float(response.strip())
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing novelty score: {str(e)}")
            return 0.5
    
    def generate_suggestion(self, pattern: Dict, model_data: Dict, subreddit: str) -> str:
        """Generate actionable suggestion based on pattern and model data."""
        prompt = f"""Generate a specific, actionable suggestion for posting in the {subreddit} subreddit
        based on the following pattern and model data. Be concise and specific.
        
        Pattern: {pattern}
        Model Data: {model_data}"""
        
        try:
            return self._get_completion(prompt, temperature=0.7)
        except Exception as e:
            logger.error(f"Error generating suggestion: {str(e)}")
            return "No specific suggestion available"
    
    def is_relevant_subreddit(self, description: str, target_market: str) -> Tuple[bool, float, str]:
        """
        Determine if a subreddit is relevant for finding product/market needs.
        Returns relevance (bool), confidence score (0-1), and reason.
        """
        prompt = f"""Analyze if this subreddit could potentially contain discussions about product needs, market opportunities, or user feedback related to {target_market}.
        Even if the connection seems indirect, consider how the community might discuss relevant topics.
        Return a JSON object with ONLY these fields:
        {{
            "is_relevant": boolean,
            "confidence": float between 0 and 1,
            "reason": string explaining the decision
        }}
        
        Target Market: {target_market}
        Subreddit description: {description}"""
        
        try:
            response = self._get_completion(prompt, temperature=0.3)
            analysis = safe_parse_json(response)
            logger.info(f"Relevance analysis: {analysis}")
            
            is_relevant = analysis.get('is_relevant', False)
            confidence = analysis.get('confidence', 0.0)
            reason = analysis.get('reason', 'No reason provided')
            
            return is_relevant, confidence, reason
        except Exception as e:
            logger.error(f"Error analyzing subreddit relevance: {str(e)}")
            return False, 0.0, str(e)
    
    def analyze_market_need(self, text: str) -> Tuple[bool, float, Dict]:
        """
        Analyze if the text discusses a product need or market opportunity.
        Returns:
        - is_need: Whether the text expresses a need/opportunity
        - confidence: Confidence score (0-1)
        - details: Dictionary with extracted details
        """
        prompt = """Analyze if this text contains any discussion of problems, needs, requests, or opportunities that could be addressed by products or services.
        Be inclusive - if there's any hint of a need or opportunity, include it.
        Return a JSON object with ONLY these fields:
        {
            "is_need": boolean,
            "confidence": float between 0 and 1,
            "need_type": "product" or "feature" or "service" or "improvement" or "other",
            "target_market": string describing who would use this,
            "problem": string describing the problem/need,
            "current_solutions": string describing existing solutions mentioned,
            "opportunity": string describing the potential opportunity
        }
        
        Text: """ + text
        
        try:
            response = self._get_completion(prompt, temperature=0.3)
            analysis = safe_parse_json(response)
            logger.debug(f"Market need analysis: {analysis}")
            return (
                analysis.get('is_need', False),
                analysis.get('confidence', 0.0),
                analysis
            )
        except Exception as e:
            logger.error(f"Error analyzing market need: {str(e)}")
            return False, 0.0, {}
    
    def extract_market_insights(self, posts: List[Dict]) -> Dict:
        """
        Analyze multiple posts to extract market insights.
        Returns aggregated insights about needs and opportunities.
        """
        posts_text = "\n\n".join([
            f"Title: {post.get('title', '')}\n"
            f"Content: {post.get('content', '')}\n"
            f"Comments: {post.get('top_comments', '')}"
            for post in posts
        ])
        
        prompt = """Analyze these posts and extract market insights.
        Return a JSON object with ONLY these fields:
        {
            "common_needs": list of strings,
            "user_segments": list of strings,
            "pain_points": list of strings,
            "competition": list of strings,
            "opportunities": list of strings,
            "recommendations": list of strings
        }
        
        Posts:
        """ + posts_text
        
        try:
            response = self._get_completion(prompt, temperature=0.7)
            return safe_parse_json(response)
        except Exception as e:
            logger.error(f"Error extracting market insights: {str(e)}")
            return {}
