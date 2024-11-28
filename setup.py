"""Setup file for the Reddit AI Agent package."""

from setuptools import setup, find_packages

setup(
    name="reddit_agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "praw",
        "pandas",
        "python-dotenv",
        "numpy",
        "groq",  # Added Groq dependency
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A utility-based learning agent for Reddit analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/reddit_agent",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
