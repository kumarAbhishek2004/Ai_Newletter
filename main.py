"""
AI Newsletter MCP Server - Fixed & Enhanced Version
Built with FastMCP for easy tool creation and management
"""

from fastmcp import FastMCP
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
import logging
from functools import wraps
import time

# External API imports
import arxiv
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("AI Newsletter Automation")

# ==================== CONFIGURATION ====================

class Config:
    """Configuration from environment variables"""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
    NEWSLETTER_FOLDER_ID = os.getenv("NEWSLETTER_FOLDER_ID")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    PRODUCT_HUNT_API_KEY = os.getenv("PRODUCT_HUNT_API_KEY")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")


# ==================== HELPER FUNCTIONS ====================

def rate_limit(calls_per_minute: int = 10):
    """Decorator to rate limit function calls"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = 60.0 / calls_per_minute - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_api_call(func):
    """Decorator for safe API calls with error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.Timeout:
            logger.error(f"{func.__name__}: Request timeout")
            return {"status": "error", "message": "Request timeout"}
        except requests.RequestException as e:
            logger.error(f"{func.__name__}: Request failed - {str(e)}")
            return {"status": "error", "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"{func.__name__}: Unexpected error - {str(e)}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}
    return wrapper


def get_google_service(service_name: str, version: str):
    """Create Google API service with credentials and automatic token refresh"""
    try:
        if not all([Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET, Config.GOOGLE_REFRESH_TOKEN]):
            raise ValueError("Missing required Google OAuth credentials")
        
        creds = Credentials(
            token=None,
            refresh_token=Config.GOOGLE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET
        )
        
        # Refresh token if needed
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
        
        return build(service_name, version, credentials=creds)
    
    except Exception as e:
        logger.error(f"Failed to create Google service: {str(e)}")
        raise


# ==================== RESEARCH PHASE TOOLS ====================

@mcp.tool()
@safe_api_call
def fetch_past_newsletters(folder_id: Optional[str] = None, count: int = 5) -> Dict:
    """
    Retrieve past newsletters from Google Drive to understand format and performance.
    
    Args:
        folder_id: Google Drive folder ID (uses env var if not provided)
        count: Number of past newsletters to fetch (default: 5)
    
    Returns:
        Dictionary containing newsletter metadata and performance metrics
    """
    if folder_id is None:
        folder_id = Config.NEWSLETTER_FOLDER_ID
    
    if not folder_id:
        return {
            "status": "error",
            "message": "No folder ID provided. Set NEWSLETTER_FOLDER_ID environment variable."
        }
    
    service = get_google_service('drive', 'v3')
    
    # Query files in the folder
    query = f"'{folder_id}' in parents and mimeType='text/html'"
    results = service.files().list(
        q=query,
        pageSize=count,
        orderBy='createdTime desc',
        fields="files(id, name, createdTime, description)"
    ).execute()
    
    files = results.get('files', [])
    
    newsletters = []
    for file in files:
        newsletters.append({
            "id": file['id'],
            "title": file['name'],
            "date": file['createdTime'],
            "drive_link": f"https://drive.google.com/file/d/{file['id']}/view"
        })
    
    logger.info(f"Fetched {len(newsletters)} past newsletters")
    
    return {
        "status": "success",
        "count": len(newsletters),
        "newsletters": newsletters
    }


@mcp.tool()
@safe_api_call
def scan_gmail_feedback(days_back: int = 7, keywords: Optional[List[str]] = None) -> Dict:
    """
    Scan Gmail for reader feedback and engagement metrics.
    
    Args:
        days_back: Number of days to look back (default: 7)
        keywords: Keywords to filter feedback emails (optional)
    
    Returns:
        Summary of feedback with themes and common requests
    """
    service = get_google_service('gmail', 'v1')
    
    # Build search query
    date_threshold = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    query = f"after:{date_threshold} subject:(newsletter OR feedback OR reply)"
    
    if keywords:
        keyword_query = " OR ".join(keywords)
        query += f" ({keyword_query})"
    
    # Search messages
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=50
    ).execute()
    
    messages = results.get('messages', [])
    
    feedback_data = {
        "total_responses": len(messages),
        "emails": []
    }
    
    # Fetch message details
    for msg in messages[:10]:  # Limit to first 10 for processing
        message = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        # Extract subject and snippet
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        
        feedback_data["emails"].append({
            "subject": subject,
            "snippet": message.get('snippet', ''),
            "date": message.get('internalDate', '')
        })
    
    logger.info(f"Scanned {len(messages)} feedback emails")
    
    return {
        "status": "success",
        "feedback_summary": feedback_data
    }


@mcp.tool()
@safe_api_call
@rate_limit(calls_per_minute=30)
def search_arxiv_papers(
    query: str = "artificial intelligence",
    max_results: int = 10,
    days_back: int = 7
) -> Dict:
    """
    Search arXiv for latest AI research papers.
    
    Args:
        query: Search query for papers (default: "artificial intelligence")
        max_results: Maximum number of results (default: 10)
        days_back: Papers published in last N days (default: 7)
    
    Returns:
        List of papers with titles, authors, summaries, and links
    """
    date_threshold = datetime.now() - timedelta(days=days_back)
    
    # Search arXiv
    search = arxiv.Search(
        query=query,
        max_results=max_results * 2,  # Fetch more to filter by date
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    papers = []
    for result in search.results():
        # Filter by date
        if result.published.replace(tzinfo=None) >= date_threshold:
            papers.append({
                "title": result.title,
                "authors": [author.name for author in result.authors[:3]],  # First 3 authors
                "summary": result.summary[:400] + "..." if len(result.summary) > 400 else result.summary,
                "published": result.published.strftime("%Y-%m-%d"),
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "categories": result.categories[:3]
            })
            
            if len(papers) >= max_results:
                break
    
    logger.info(f"Found {len(papers)} relevant papers on arXiv")
    
    return {
        "status": "success",
        "count": len(papers),
        "papers": papers,
        "query": query
    }


@mcp.tool()
@safe_api_call
@rate_limit(calls_per_minute=30)
def fetch_github_trending(
    language: str = "python",
    timeframe: str = "weekly",
    topic: str = "artificial-intelligence"
) -> Dict:
    """
    Fetch trending AI repositories from GitHub.
    
    Args:
        language: Programming language filter (default: "python")
        timeframe: Time period - daily, weekly, monthly (default: "weekly")
        topic: GitHub topic to filter (default: "artificial-intelligence")
    
    Returns:
        List of trending repositories with stats
    """
    # Calculate date for trending
    if timeframe == "daily":
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif timeframe == "weekly":
        date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    else:
        date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # GitHub API endpoint
    url = "https://api.github.com/search/repositories"
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if Config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {Config.GITHUB_TOKEN}"
    
    params = {
        "q": f"language:{language} created:>{date} topic:{topic}",
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    repos = []
    for item in data.get("items", []):
        repos.append({
            "name": item["name"],
            "full_name": item["full_name"],
            "description": item.get("description", "No description available"),
            "stars": item["stargazers_count"],
            "forks": item["forks_count"],
            "url": item["html_url"],
            "language": item.get("language", "N/A"),
            "topics": item.get("topics", [])[:5],
            "created_at": item["created_at"]
        })
    
    logger.info(f"Found {len(repos)} trending GitHub repositories")
    
    return {
        "status": "success",
        "count": len(repos),
        "repositories": repos,
        "timeframe": timeframe
    }


@mcp.tool()
@safe_api_call
@rate_limit(calls_per_minute=20)
def search_product_hunt(days_back: int = 7, limit: int = 10) -> Dict:
    """
    Search Product Hunt for new AI tools and products.
    
    Args:
        days_back: Products launched in last N days (default: 7)
        limit: Maximum number of products (default: 10)
    
    Returns:
        List of AI products with votes and details
    """
    if not Config.PRODUCT_HUNT_API_KEY:
        return {
            "status": "error",
            "message": "Product Hunt API key not configured. Set PRODUCT_HUNT_API_KEY environment variable."
        }
    
    # Product Hunt GraphQL API
    url = "https://api.producthunt.com/v2/api/graphql"
    
    headers = {
        "Authorization": f"Bearer {Config.PRODUCT_HUNT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      posts(order: VOTES, topic: "artificial-intelligence", first: %d) {
        edges {
          node {
            name
            tagline
            description
            votesCount
            url
            createdAt
            topics {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """ % limit
    
    response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    products = []
    for edge in data.get("data", {}).get("posts", {}).get("edges", []):
        node = edge["node"]
        products.append({
            "name": node["name"],
            "tagline": node["tagline"],
            "description": (node.get("description", "") or "")[:200],
            "votes": node["votesCount"],
            "url": node["url"],
            "launch_date": node["createdAt"]
        })
    
    logger.info(f"Found {len(products)} AI products on Product Hunt")
    
    return {
        "status": "success",
        "count": len(products),
        "products": products
    }


@mcp.tool()
@safe_api_call
@rate_limit(calls_per_minute=15)
def fetch_twitter_trends(
    hashtags: Optional[List[str]] = None,
    min_likes: int = 100,
    days_back: int = 7
) -> Dict:
    """
    Fetch viral AI-related tweets and trends.
    
    Args:
        hashtags: List of hashtags to track (default: ["AI", "MachineLearning", "LLM"])
        min_likes: Minimum likes threshold (default: 100)
        days_back: Tweets from last N days (default: 7)
    
    Returns:
        List of trending tweets with engagement metrics
    """
    if not Config.TWITTER_BEARER_TOKEN:
        return {
            "status": "error",
            "message": "Twitter API token not configured. Set TWITTER_BEARER_TOKEN environment variable."
        }
    
    if hashtags is None:
        hashtags = ["AI", "MachineLearning", "LLM", "ChatGPT", "GenerativeAI"]
    
    # Twitter API v2 endpoint
    url = "https://api.twitter.com/2/tweets/search/recent"
    
    headers = {
        "Authorization": f"Bearer {Config.TWITTER_BEARER_TOKEN}"
    }
    
    # Build query
    hashtag_query = " OR ".join([f"#{tag}" for tag in hashtags])
    query = f"({hashtag_query}) -is:retweet lang:en"
    
    params = {
        "query": query,
        "max_results": 100,
        "tweet.fields": "public_metrics,created_at,author_id",
        "expansions": "author_id",
        "user.fields": "username,name"
    }
    
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    tweets = []
    users = {user["id"]: user for user in data.get("includes", {}).get("users", [])}
    
    for tweet in data.get("data", []):
        metrics = tweet.get("public_metrics", {})
        if metrics.get("like_count", 0) >= min_likes:
            author = users.get(tweet["author_id"], {})
            tweets.append({
                "text": tweet["text"][:280],
                "author": f"@{author.get('username', 'unknown')}",
                "author_name": author.get('name', 'Unknown'),
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "created_at": tweet["created_at"],
                "url": f"https://twitter.com/{author.get('username', 'i')}/status/{tweet['id']}"
            })
    
    # Sort by engagement
    tweets.sort(key=lambda x: x["likes"] + x["retweets"] * 2, reverse=True)
    
    logger.info(f"Found {len(tweets)} trending AI tweets")
    
    return {
        "status": "success",
        "count": len(tweets),
        "trending_tweets": tweets[:10]
    }


# ==================== EDITING PHASE TOOLS ====================

@mcp.tool()
def create_newsletter_draft(research_content: Dict, issue_number: int = 1) -> Dict:
    """
    Create a structured newsletter draft from research content.
    
    Args:
        research_content: Dictionary containing all gathered research data
        issue_number: Newsletter issue number (default: 1)
    
    Returns:
        Structured newsletter draft with all sections organized
    """
    try:
        draft = {
            "metadata": {
                "issue_number": issue_number,
                "date": datetime.now().strftime("%B %d, %Y"),
                "title": f"CampusX AI Newsletter #{issue_number}"
            },
            "sections": {
                "big_story": {
                    "title": "",
                    "content": "",
                    "source": ""
                },
                "quick_updates": [],
                "top_papers": research_content.get("papers", [])[:5],
                "github_repos": research_content.get("repositories", [])[:5],
                "tutorials": research_content.get("tutorials", []),
                "ai_products": research_content.get("products", [])[:3],
                "tweets": research_content.get("tweets", [])[:3],
                "closing_notes": ""
            },
            "status": "draft",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created newsletter draft #{issue_number}")
        
        return {
            "status": "success",
            "draft": draft
        }
    
    except Exception as e:
        logger.error(f"Failed to create draft: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def organize_content_sections(
    raw_content: Dict,
    priorities: Optional[List[str]] = None
) -> Dict:
    """
    Organize research content into newsletter sections with priorities.
    
    Args:
        raw_content: Raw research data to organize
        priorities: List of section names in priority order
    
    Returns:
        Content organized by sections with prioritization applied
    """
    if priorities is None:
        priorities = ["big_story", "papers", "products", "repositories", "tweets"]
    
    organized = {
        "sections": {},
        "metadata": {
            "total_items": 0,
            "sections_count": 0
        }
    }
    
    for priority in priorities:
        if priority in raw_content:
            organized["sections"][priority] = raw_content[priority]
            organized["metadata"]["sections_count"] += 1
            if isinstance(raw_content[priority], list):
                organized["metadata"]["total_items"] += len(raw_content[priority])
    
    logger.info(f"Organized content into {organized['metadata']['sections_count']} sections")
    
    return {
        "status": "success",
        "organized_content": organized
    }


@mcp.tool()
def validate_newsletter_content(draft_content: Dict) -> Dict:
    """
    Validate newsletter content for completeness and quality.
    
    Args:
        draft_content: Newsletter draft to validate
    
    Returns:
        Validation results with warnings and errors
    """
    issues = []
    warnings = []
    
    sections = draft_content.get("sections", {})
    
    # Check for minimum content
    if len(sections.get("top_papers", [])) < 3:
        warnings.append("Less than 3 papers - consider adding more")
    
    if len(sections.get("github_repos", [])) < 3:
        warnings.append("Less than 3 GitHub repos - consider adding more")
    
    # Check for big story
    if not sections.get("big_story", {}).get("content"):
        issues.append("Big story content is missing")
    
    if not sections.get("big_story", {}).get("title"):
        issues.append("Big story title is missing")
    
    # Check metadata
    metadata = draft_content.get("metadata", {})
    if not metadata.get("issue_number"):
        issues.append("Issue number is missing")
    
    logger.info(f"Validation complete: {len(issues)} issues, {len(warnings)} warnings")
    
    return {
        "status": "success" if not issues else "warning",
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "sections_count": len(sections)
    }


@mcp.tool()
def preview_newsletter(draft_content: Dict) -> Dict:
    """
    Generate a text preview of the newsletter for quick review.
    
    Args:
        draft_content: Newsletter draft content
    
    Returns:
        Plain text preview with content summary
    """
    sections = draft_content.get("sections", {})
    metadata = draft_content.get("metadata", {})
    
    preview = f"""
{'='*60}
{metadata.get('title', 'Newsletter Preview')}
Issue #{metadata.get('issue_number', 'N/A')} | {metadata.get('date', '')}
{'='*60}

📊 CONTENT SUMMARY:
- Papers: {len(sections.get('top_papers', []))}
- GitHub Repos: {len(sections.get('github_repos', []))}
- Products: {len(sections.get('ai_products', []))}
- Tweets: {len(sections.get('tweets', []))}

🎯 BIG STORY:
{sections.get('big_story', {}).get('title', 'Not set')}

📄 TOP PAPERS:
"""
    
    for i, paper in enumerate(sections.get("top_papers", [])[:3], 1):
        preview += f"\n{i}. {paper.get('title', 'Untitled')}\n"
    
    preview += f"\n{'='*60}\n"
    
    return {
        "status": "success",
        "preview": preview,
        "word_count": len(preview.split())
    }


# ==================== DESIGNING PHASE TOOLS ====================

@mcp.tool()
def generate_html_newsletter(draft_content: Dict, template: str = "default") -> Dict:
    """
    Convert newsletter draft into HTML with design specifications.
    
    Args:
        draft_content: Newsletter draft content dictionary
        template: Template style to use (default, modern, minimal)
    
    Returns:
        Complete HTML newsletter ready for distribution
    """
    try:
        metadata = draft_content.get("metadata", {})
        sections = draft_content.get("sections", {})
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', 'Newsletter')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #4A90E2;
            margin: 0;
            font-size: 28px;
        }}
        .section {{
            margin-bottom: 35px;
        }}
        .section h2 {{
            color: #2C3E50;
            border-left: 4px solid #4A90E2;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .paper-item, .repo-item, .product-item, .tweet-item {{
            background-color: #f8f9fa;
            padding: 18px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 3px solid #4A90E2;
            transition: transform 0.2s;
        }}
        .paper-item:hover, .repo-item:hover, .product-item:hover, .tweet-item:hover {{
            transform: translateX(5px);
        }}
        .paper-item h3, .repo-item h3, .product-item h3 {{
            margin-top: 0;
            margin-bottom: 10px;
            color: #2C3E50;
            font-size: 18px;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        a {{
            color: #4A90E2;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .tweet-text {{
            font-style: italic;
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }}
        .engagement {{
            color: #888;
            font-size: 0.85em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            color: #666;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            margin-right: 5px;
            background: #e3f2fd;
            color: #1976d2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {metadata.get('title', 'AI Newsletter')}</h1>
            <p class="meta">Issue #{metadata.get('issue_number', '1')} | {metadata.get('date', '')}</p>
        </div>
"""
        
        # Add Big Story if available
        big_story = sections.get("big_story", {})
        if big_story.get("title"):
            html += f"""
        <div class="section">
            <h2>🌟 This Week's Big Story</h2>
            <div class="paper-item">
                <h3>{big_story.get('title', '')}</h3>
                <p>{big_story.get('content', '')}</p>
                {f'<a href="{big_story.get("source", "#")}" target="_blank">Read More →</a>' if big_story.get('source') else ''}
            </div>
        </div>
"""
        
        # Add papers
        if sections.get("top_papers"):
            html += """
        <div class="section">
            <h2>📄 Top AI Research Papers</h2>
"""
            for paper in sections.get("top_papers", [])[:5]:
                categories = ' '.join([f'<span class="badge">{cat}</span>' for cat in paper.get('categories', [])[:2]])
                html += f"""
            <div class="paper-item">
                <h3>{paper.get('title', 'Untitled')}</h3>
                <p class="meta">Authors: {', '.join(paper.get('authors', ['Unknown']))}</p>
                {f'<div class="meta">{categories}</div>' if categories else ''}
                <p>{paper.get('summary', 'No summary available')}</p>
                <a href="{paper.get('url', '#')}" target="_blank">Read Paper →</a>
                {f' | <a href="{paper.get("pdf_url", "#")}" target="_blank">Download PDF</a>' if paper.get('pdf_url') else ''}
            </div>
"""
            html += "        </div>\n"
        
        # Add GitHub repos
        if sections.get("github_repos"):
            html += """
        <div class="section">
            <h2>💻 Trending GitHub Repositories</h2>
"""
            for repo in sections.get("github_repos", [])[:5]:
                topics = ' '.join([f'<span class="badge">{topic}</span>' for topic in repo.get('topics', [])[:3]])
                html += f"""
            <div class="repo-item">
                <h3>⭐ {repo.get('name', 'Unnamed Repo')}</h3>
                <p>{repo.get('description', 'No description available')}</p>
                <p class="meta">⭐ {repo.get('stars', 0):,} stars | 🍴 {repo.get('forks', 0):,} forks | 💻 {repo.get('language', 'N/A')}</p>
                {f'<div class="meta">{topics}</div>' if topics else ''}
                <a href="{repo.get('url', '#')}" target="_blank">View Repository →</a>
            </div>
"""
            html += "        </div>\n"
        
        # Add products
        if sections.get("ai_products"):
            html += """
        <div class="section">
            <h2>🛠️ New AI Products & Tools</h2>
"""
            for product in sections.get("ai_products", [])[:3]:
                html += f"""
            <div class="product-item">
                <h3>{product.get('name', 'Unnamed Product')}</h3>
                <p><strong>{product.get('tagline', '')}</strong></p>
                <p>{product.get('description', 'No description available')}</p>
                <p class="meta">👍 {product.get('votes', 0):,} upvotes on Product Hunt</p>
                <a href="{product.get('url', '#')}" target="_blank">Check it out →</a>
            </div>
"""
            html += "        </div>\n"
        
        # Add tweets
        if sections.get("tweets"):
            html += """
        <div class="section">
            <h2>🐦 Trending AI Conversations</h2>
"""
            for tweet in sections.get("tweets", [])[:3]:
                html += f"""
            <div class="tweet-item">
                <p class="meta"><strong>{tweet.get('author_name', 'Unknown')}</strong> {tweet.get('author', '')}</p>
                <div class="tweet-text">{tweet.get('text', '')}</div>
                <p class="engagement">❤️ {tweet.get('likes', 0):,} likes | 🔄 {tweet.get('retweets', 0):,} retweets</p>
                <a href="{tweet.get('url', '#')}" target="_blank">View Tweet →</a>
            </div>
"""
            html += "        </div>\n"
        
        # Footer
        html += """
        <div class="footer">
            <p>Thanks for reading! 🙌</p>
            <p>Built with ❤️ by CampusX</p>
            <p style="font-size: 0.85em; color: #888; margin-top: 15px;">
                Stay curious, keep learning!
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        logger.info(f"Generated HTML newsletter ({len(html)} bytes)")
        
        return {
            "status": "success",
            "html": html,
            "size": len(html),
            "template": template
        }
    
    except Exception as e:
        logger.error(f"Failed to generate HTML: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
@safe_api_call
def save_to_drive(
    content: str,
    filename: str,
    folder_id: Optional[str] = None
) -> Dict:
    """
    Save generated newsletter to Google Drive.
    
    Args:
        content: Newsletter HTML content
        filename: Name for the file
        folder_id: Target folder ID (uses NEWSLETTER_FOLDER_ID if not provided)
    
    Returns:
        File ID and link to the saved newsletter
    """
    if folder_id is None:
        folder_id = Config.NEWSLETTER_FOLDER_ID
    
    if not folder_id:
        return {
            "status": "error",
            "message": "No folder ID provided. Set NEWSLETTER_FOLDER_ID environment variable."
        }
    
    service = get_google_service('drive', 'v3')
    
    # Create file metadata
    file_metadata = {
        'name': filename,
        'parents': [folder_id],
        'mimeType': 'text/html'
    }
    
    # Create file content using MediaIoBaseUpload (fixed from MediaFileUpload)
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/html',
        resumable=True
    )
    
    # Upload file
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    logger.info(f"Saved newsletter to Drive: {filename}")
    
    return {
        "status": "success",
        "file_id": file['id'],
        "url": file['webViewLink'],
        "filename": filename
    }


@mcp.tool()
def export_newsletter(content: Dict, format: str = "html") -> Dict:
    """
    Export newsletter in multiple formats (HTML, Markdown, JSON).
    
    Args:
        content: Newsletter content
        format: Output format (html, markdown, json)
    
    Returns:
        Exported content in requested format
    """
    try:
        if format == "markdown":
            # Convert to markdown
            md = convert_to_markdown(content)
            return {
                "status": "success",
                "content": md,
                "format": "markdown",
                "size": len(md)
            }
        elif format == "json":
            json_content = json.dumps(content, indent=2)
            return {
                "status": "success",
                "content": json_content,
                "format": "json",
                "size": len(json_content)
            }
        else:
            # HTML is default
            return generate_html_newsletter(content)
    
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def convert_to_markdown(content: Dict) -> str:
    """Helper function to convert newsletter content to Markdown"""
    metadata = content.get("metadata", {})
    sections = content.get("sections", {})
    
    md = f"""# {metadata.get('title', 'Newsletter')}
**Issue #{metadata.get('issue_number', 'N/A')}** | {metadata.get('date', '')}

---

"""
    
    # Big story
    big_story = sections.get("big_story", {})
    if big_story.get("title"):
        md += f"""## 🌟 This Week's Big Story

### {big_story['title']}

{big_story.get('content', '')}

{f"[Read More]({big_story['source']})" if big_story.get('source') else ''}

---

"""
    
    # Papers
    if sections.get("top_papers"):
        md += "## 📄 Top AI Research Papers\n\n"
        for i, paper in enumerate(sections["top_papers"][:5], 1):
            md += f"""### {i}. {paper.get('title', 'Untitled')}

**Authors:** {', '.join(paper.get('authors', ['Unknown']))}

{paper.get('summary', '')}

[Read Paper]({paper.get('url', '#')})

---

"""
    
    # Repos
    if sections.get("github_repos"):
        md += "## 💻 Trending GitHub Repositories\n\n"
        for repo in sections["github_repos"][:5]:
            md += f"""### ⭐ {repo.get('name', 'Unnamed')}

{repo.get('description', '')}

**Stats:** {repo.get('stars', 0):,} stars | {repo.get('forks', 0):,} forks | Language: {repo.get('language', 'N/A')}

[View Repository]({repo.get('url', '#')})

---

"""
    
    # Products
    if sections.get("ai_products"):
        md += "## 🛠️ New AI Products & Tools\n\n"
        for product in sections["ai_products"][:3]:
            md += f"""### {product.get('name', 'Unnamed')}

**{product.get('tagline', '')}**

{product.get('description', '')}

👍 {product.get('votes', 0):,} upvotes | [Check it out]({product.get('url', '#')})

---

"""
    
    md += "\n**Thanks for reading! 🙌**\n\n*Built with ❤️ by CampusX*\n"
    
    return md


# ==================== BATCH OPERATIONS ====================

@mcp.tool()
@safe_api_call
def fetch_all_research(config: Optional[Dict] = None) -> Dict:
    """
    Fetch all research content in one operation.
    
    Args:
        config: Optional configuration for research parameters
    
    Returns:
        Complete research data from all sources
    """
    if config is None:
        config = {
            "days_back": 7,
            "max_papers": 10,
            "max_repos": 10,
            "max_products": 10
        }
    
    results = {}
    errors = []
    
    logger.info("Starting batch research fetch...")
    
    # Fetch papers
    try:
        papers_result = search_arxiv_papers(
            max_results=config.get("max_papers", 10),
            days_back=config.get("days_back", 7)
        )
        if papers_result.get("status") == "success":
            results["papers"] = papers_result.get("papers", [])
        else:
            errors.append(f"Papers: {papers_result.get('message')}")
    except Exception as e:
        errors.append(f"Papers: {str(e)}")
    
    # Fetch repos
    try:
        repos_result = fetch_github_trending(timeframe="weekly")
        if repos_result.get("status") == "success":
            results["repositories"] = repos_result.get("repositories", [])
        else:
            errors.append(f"Repos: {repos_result.get('message')}")
    except Exception as e:
        errors.append(f"Repos: {str(e)}")
    
    # Fetch products (only if API key is configured)
    if Config.PRODUCT_HUNT_API_KEY:
        try:
            products_result = search_product_hunt(
                days_back=config.get("days_back", 7),
                limit=config.get("max_products", 10)
            )
            if products_result.get("status") == "success":
                results["products"] = products_result.get("products", [])
            else:
                errors.append(f"Products: {products_result.get('message')}")
        except Exception as e:
            errors.append(f"Products: {str(e)}")
    
    # Fetch tweets (only if API key is configured)
    if Config.TWITTER_BEARER_TOKEN:
        try:
            tweets_result = fetch_twitter_trends(
                days_back=config.get("days_back", 7)
            )
            if tweets_result.get("status") == "success":
                results["tweets"] = tweets_result.get("trending_tweets", [])
            else:
                errors.append(f"Tweets: {tweets_result.get('message')}")
        except Exception as e:
            errors.append(f"Tweets: {str(e)}")
    
    logger.info(f"Batch fetch complete: {len(results)} sources, {len(errors)} errors")
    
    return {
        "status": "success" if not errors else "partial",
        "research_data": results,
        "errors": errors,
        "sources_fetched": len(results),
        "config": config
    }


# ==================== PROMPTS ====================

@mcp.prompt()
def research_newsletter_prompt() -> str:
    """Prompt to guide through the research phase"""
    return """I need to gather content for this week's AI newsletter. Please help me:

1. Use `fetch_all_research()` to gather content from all sources at once, OR
2. Manually fetch from individual sources:
   - `search_arxiv_papers()` - Latest AI papers (last 7 days)
   - `fetch_github_trending()` - Trending AI repositories
   - `search_product_hunt()` - New AI products
   - `fetch_twitter_trends()` - Viral AI tweets

3. Optional: Check `fetch_past_newsletters()` to understand our format
4. Optional: Use `scan_gmail_feedback()` to see what readers want

Once you have the data, summarize key findings and suggest the "Big Story" for this week."""


@mcp.prompt()
def create_newsletter_prompt() -> str:
    """Prompt to guide through creating the newsletter"""
    return """Based on the research content gathered, create a complete newsletter:

1. Use `create_newsletter_draft()` with the research data
2. Select the most impactful story as the "Big Story"
3. Use `validate_newsletter_content()` to check for issues
4. Use `preview_newsletter()` to see a text preview
5. Use `generate_html_newsletter()` to create the HTML version
6. Use `save_to_drive()` to save to Google Drive

Make the content engaging, concise, and valuable for AI enthusiasts!"""


@mcp.prompt()
def full_automation_prompt() -> str:
    """Complete end-to-end newsletter creation prompt"""
    return """Let's create this week's AI newsletter from scratch:

**PHASE 1: Research**
- Run `fetch_all_research()` to gather all content

**PHASE 2: Create Draft**
- Run `create_newsletter_draft()` with the research data
- Analyze the content and pick the best "Big Story"
- Update the draft with the big story details

**PHASE 3: Quality Check**
- Run `validate_newsletter_content()` to check for issues
- Run `preview_newsletter()` to see the content

**PHASE 4: Generate & Save**
- Run `generate_html_newsletter()` to create HTML
- Run `save_to_drive()` to save to Google Drive

Provide a summary at each phase and ask for approval before moving to the next step."""


# ==================== VALIDATION & STARTUP ====================

def validate_config() -> bool:
    """Validate required environment variables on startup"""
    required = {
        "GOOGLE_CLIENT_ID": Config.GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": Config.GOOGLE_CLIENT_SECRET,
        "GOOGLE_REFRESH_TOKEN": Config.GOOGLE_REFRESH_TOKEN
    }
    
    optional = {
        "NEWSLETTER_FOLDER_ID": Config.NEWSLETTER_FOLDER_ID,
        "GITHUB_TOKEN": Config.GITHUB_TOKEN,
        "PRODUCT_HUNT_API_KEY": Config.PRODUCT_HUNT_API_KEY,
        "TWITTER_BEARER_TOKEN": Config.TWITTER_BEARER_TOKEN
    }
    
    missing_required = [key for key, value in required.items() if not value]
    missing_optional = [key for key, value in optional.items() if not value]
    
    if missing_required:
        logger.error(f"Missing REQUIRED configuration: {', '.join(missing_required)}")
        logger.error("Google OAuth credentials are required for basic functionality")
        return False
    
    if missing_optional:
        logger.warning(f"Missing optional configuration: {', '.join(missing_optional)}")
        logger.warning("Some features may be limited")
    
    logger.info("Configuration validation complete")
    return True


# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info("Starting AI Newsletter MCP Server...")
    
    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed. Please set required environment variables.")
        logger.error("Required: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN")
    else:
        logger.info("All required configuration present")
    
    logger.info("Server ready to accept connections")
    mcp.run()