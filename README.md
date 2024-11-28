# Reddit AI Agent

A utility-based learning agent for Reddit analysis that combines multiple agent types:
- Model-based: Maintains internal state of subreddit patterns
- Utility-based: Uses utility functions to make optimal decisions
- Learning: Adapts behavior based on past interactions
- Goal-based: Works towards specific objectives
- LLM-powered: Uses Groq's LLM for advanced content analysis

## Features

- Process and analyze Reddit submissions
- Calculate engagement metrics
- Learn patterns from successful posts
- Generate recommendations based on learned patterns
- Store data and patterns in SQLite database
- Advanced content analysis using Groq's LLM:
  - Sentiment analysis
  - Topic extraction
  - Content relevance scoring
  - Novelty assessment
  - Actionable suggestions

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/reddit_agent.git
cd reddit_agent
```

2. Install the package:
```bash
pip install -e .
```

## Configuration

Create a `.env` file in the root directory with your Reddit API and Groq credentials:

```env
# Reddit API credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
REDDIT_USERNAME=your_username

# Groq API credentials
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192  # Optional, defaults to llama3-8b-8192

# Optional settings
LEARNING_RATE=0.1
WEIGHT_ENGAGEMENT=0.4
WEIGHT_SENTIMENT=0.2
WEIGHT_RELEVANCE=0.2
WEIGHT_NOVELTY=0.2
```

## Usage

1. Basic usage:

```python
from reddit_agent import RedditAIAgent

# Create an agent instance
agent = RedditAIAgent()

# Process submissions from a subreddit
processed = agent.process_subreddit("python", limit=5)

# Get recommendations
recommendations = agent.get_recommendations("python")
```

2. Run the main script:

```bash
python main.py
```

## Project Structure

```
reddit_agent/
├── reddit_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── analysis.py
│   ├── database.py
│   ├── models.py
│   └── llm.py
├── main.py
├── setup.py
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
