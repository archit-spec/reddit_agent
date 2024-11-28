"""Database operations for the Reddit AI Agent."""

import sqlite3
from datetime import datetime
import json
from typing import Dict, List, Optional

class Database:
    """Handles all database operations for the Reddit AI Agent."""
    
    def __init__(self, db_path: str):
        """Initialize database connection and create tables."""
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create necessary database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for storing processed submissions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    author TEXT,
                    subreddit TEXT,
                    created_utc INTEGER,
                    processed_at TIMESTAMP,
                    sentiment REAL,
                    topics TEXT,
                    engagement_score REAL,
                    utility_score REAL
                )
            """)
            
            # Table for storing learned patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subreddit TEXT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    confidence REAL,
                    utility_score REAL,
                    last_updated TIMESTAMP
                )
            """)
            
            # Table for storing action outcomes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_outcomes (
                    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT,
                    context TEXT,
                    outcome_score REAL,
                    timestamp TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def is_submission_processed(self, submission_id: str) -> bool:
        """Check if a submission has already been processed."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM submissions WHERE submission_id = ?",
                (submission_id,)
            )
            return cursor.fetchone() is not None
    
    def store_submission(self, submission, analysis: Dict, utility_score: float):
        """Store submission and its analysis in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (
                    submission_id, title, content, author, subreddit,
                    created_utc, processed_at, sentiment, topics,
                    engagement_score, utility_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                submission.id,
                submission.title,
                submission.selftext,
                str(submission.author),
                str(submission.subreddit),
                submission.created_utc,
                datetime.now().timestamp(),
                analysis['sentiment'],
                json.dumps(analysis['topics']),
                analysis.get('engagement_rate', 0.0),
                utility_score
            ))
            conn.commit()
    
    def store_pattern(self, subreddit: str, pattern_type: str, 
                     pattern_data: Dict, confidence: float):
        """Store a learned pattern in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learned_patterns (
                    subreddit, pattern_type, pattern_data, confidence, 
                    utility_score, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                subreddit,
                pattern_type,
                json.dumps(pattern_data),
                confidence,
                confidence,  # Using confidence as utility score for simplicity
                datetime.now().timestamp()
            ))
            conn.commit()
    
    def get_patterns(self, subreddit: str) -> List[Dict]:
        """Retrieve learned patterns from the database for a specific subreddit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern_id, pattern_type, pattern_data, confidence, 
                       utility_score, last_updated
                FROM learned_patterns
                WHERE subreddit = ?
                ORDER BY confidence DESC
            """, (subreddit,))
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append({
                    'pattern_id': row[0],
                    'pattern_type': row[1],
                    'pattern_data': json.loads(row[2]),
                    'confidence': row[3],
                    'utility_score': row[4],
                    'last_updated': row[5]
                })
            
            return patterns
