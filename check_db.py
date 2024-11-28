"""Script to check database contents."""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from reddit_agent.database import Database

def main():
    """Display contents of the database."""
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    db = Database("reddit_memory.db")
    
    # Get all subreddits
    print("\n=== Subreddits in Database ===")
    subreddits = db.get_all_subreddits()
    print(f"Total subreddits: {len(subreddits)}")
    for subreddit in subreddits:
        print(f"\nSubreddit: r/{subreddit.name}")
        print(f"Title: {subreddit.title}")
        print(f"Description: {subreddit.description[:100]}..." if subreddit.description else "No description")
        print(f"Subscribers: {subreddit.subscribers}")
        print(f"Last Updated: {subreddit.last_updated}")
    
    # Get all market insights
    print("\n=== Market Insights in Database ===")
    insights = db.get_all_market_insights()
    print(f"Total insights: {len(insights)}")
    for insight in insights:
        print(f"\nInsight ID: {insight.id}")
        print(f"Subreddit: r/{insight.subreddit_name}")
        print(f"Market: {insight.target_market}")
        print(f"Created: {insight.created_at}")
        print(f"Needs Found: {len(json.loads(insight.needs_found))}")
        print("-" * 50)

if __name__ == "__main__":
    main()
