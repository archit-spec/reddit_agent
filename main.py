"""Main script to run the Reddit AI Agent."""

import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
import argparse
from typing import List, Dict
import praw
from datetime import datetime

from reddit_agent import RedditAIAgent
from reddit_agent.llm import LLMAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def search_subreddits(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Search for subreddits in the CSV file."""
    # Convert all searchable columns to string and lowercase for case-insensitive search
    searchable_columns = ['name', 'title', 'description', 'topic']
    df_search = df.copy()
    
    for col in searchable_columns:
        if col in df_search.columns:
            df_search[col] = df_search[col].fillna('').astype(str).str.lower()
    
    # Split query into keywords
    keywords = query.lower().split()
    
    # Search across multiple columns
    mask = pd.Series([False] * len(df_search))
    for col in searchable_columns:
        if col in df_search.columns:
            for keyword in keywords:
                mask = mask | df_search[col].str.contains(keyword, na=False)
    
    return df.loc[mask].copy()  # Return original dataframe rows that match

def save_insights(insights: Dict, subreddit: str):
    """Save market insights to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_insights_{subreddit}_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(insights, f, indent=2)
        logger.info(f"Saved insights to {filename}")
    except Exception as e:
        logger.error(f"Error saving insights: {str(e)}")

def analyze_subreddit(reddit: praw.Reddit, subreddit_name: str, post_limit: int, llm: LLMAnalyzer) -> Dict:
    """Analyze a subreddit for market insights."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        insights = {
            'subreddit': subreddit_name,
            'title': subreddit.title,
            'description': subreddit.description,
            'subscribers': subreddit.subscribers,
            'needs_found': [],
            'opportunities': []
        }
        
        # Analyze different post categories
        categories = ['hot', 'new', 'top']
        posts_analyzed = 0
        
        for category in categories:
            logger.info(f"Analyzing {category} posts in r/{subreddit_name}")
            post_list = getattr(subreddit, category)(limit=post_limit // len(categories))
            
            for post in post_list:
                # Skip stickied posts
                if post.stickied:
                    continue
                
                # Combine post title, content, and top comments
                text = f"Title: {post.title}\n\nContent: {post.selftext}\n\n"
                post.comments.replace_more(limit=0)
                top_comments = [comment.body for comment in post.comments.list()[:3]]
                text += "Top Comments:\n" + "\n".join(top_comments)
                
                # Analyze for market needs
                is_need, confidence, details = llm.analyze_market_need(text)
                
                if is_need and confidence > 0.6:
                    need_info = {
                        'url': f"https://reddit.com{post.permalink}",
                        'title': post.title,
                        'score': post.score,
                        'confidence': confidence,
                        **details
                    }
                    insights['needs_found'].append(need_info)
                
                posts_analyzed += 1
                
        logger.info(f"Analyzed {posts_analyzed} posts in r/{subreddit_name}")
        return insights
        
    except Exception as e:
        logger.error(f"Error analyzing subreddit r/{subreddit_name}: {str(e)}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Reddit Market Research Tool')
    parser.add_argument('--market', required=True, help='Target market/domain to research')
    parser.add_argument('--search', help='Subreddit search query')
    parser.add_argument('--limit', type=int, default=5, help='Number of subreddits to analyze')
    parser.add_argument('--posts', type=int, default=100, help='Number of posts to analyze per subreddit')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT'),
        username=os.getenv('REDDIT_USERNAME')
    )
    
    # Initialize LLM analyzer
    llm = LLMAnalyzer()
    
    # Search for relevant subreddits
    logger.info(f"Searching for subreddits matching: {args.search}")
    
    # Get list of subreddits to analyze
    analyzed_subreddits = []
    total_needs = 0
    
    try:
        for subreddit in reddit.subreddits.search(args.search, limit=args.limit * 2):
            if len(analyzed_subreddits) >= args.limit:
                break
                
            # Check if subreddit is relevant
            is_relevant, confidence, reason = llm.is_relevant_subreddit(
                subreddit.description or subreddit.title,
                args.market
            )
            
            logger.info(f"Subreddit r/{subreddit.display_name}: Relevant={is_relevant}, Confidence={confidence:.2f}")
            logger.info(f"Reason: {reason}")
            
            if is_relevant and confidence > 0.3:  # Lower threshold for inclusivity
                insights = analyze_subreddit(reddit, subreddit.display_name, args.posts, llm)
                if insights and insights.get('needs_found'):
                    analyzed_subreddits.append(insights)
                    total_needs += len(insights['needs_found'])
                    save_insights(insights, subreddit.display_name)
    
    except Exception as e:
        logger.error(f"Error during subreddit analysis: {str(e)}")
    
    # Print summary
    print("\nMarket Research Summary:")
    print(f"Target Market: {args.market}")
    print(f"Analyzed Subreddits: {len(analyzed_subreddits)}")
    if analyzed_subreddits:
        print(f"Total Market Needs Found: {total_needs}")
        print("\nTop Subreddits:")
        for insights in analyzed_subreddits:
            print(f"- r/{insights['subreddit']}: {len(insights['needs_found'])} needs found")
    else:
        print("\nNo relevant market insights found. Try:")
        print("1. Broadening your search query")
        print("2. Adjusting the target market description")
        print("3. Increasing the number of subreddits to analyze")

if __name__ == '__main__':
    main()
