# 🤖 AI Newsletter Automation MCP Server

<div align="center">

![AI Newsletter Banner](https://img.shields.io/badge/AI-Newsletter-blue?style=for-the-badge&logo=openai&logoColor=white)
![MCP Server](https://img.shields.io/badge/MCP-Server-green?style=for-the-badge&logo=cloud&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python&logoColor=white)

**Automate your AI newsletter creation with intelligent research, curation, and publishing**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#-configuration)

</div>

---

## 📖 What is MCP?

**MCP (Model Context Protocol)** is a revolutionary framework that allows AI assistants like Claude to interact with external tools and services through standardized interfaces. Think of it as a "plugin system" for AI - it enables Claude to:

- 🔍 Search the web and fetch real-time data
- 📁 Access and manage files in Google Drive
- 📧 Read and send emails via Gmail
- 🛠️ Execute custom functions and APIs

This MCP server specifically provides Claude with tools to automate the entire AI newsletter creation process - from research to publication.

---

## ✨ Features

### 🔍 **Research Phase**
- **arXiv Papers**: Fetch latest AI research papers with summaries
- **GitHub Trending**: Discover trending AI repositories and projects
- **Product Hunt**: Track new AI tools and products
- **Twitter Trends**: Capture viral AI discussions and tweets
- **Gmail Feedback**: Analyze reader feedback and engagement
- **Past Newsletters**: Learn from previous newsletter performance

### ✍️ **Editing Phase**
- **Smart Content Organization**: Automatically categorize and prioritize content
- **Draft Creation**: Generate structured newsletter drafts
- **Content Validation**: Check completeness and quality
- **Text Preview**: Quick review before publishing

### 🎨 **Design Phase**
- **HTML Generation**: Beautiful, responsive email templates
- **Multi-Format Export**: HTML, Markdown, and JSON formats
- **Google Drive Integration**: Auto-save to cloud storage
- **Mobile-Friendly**: Responsive design for all devices

---

<div align="center">
<img src="https://raw.githubusercontent.com/anthropics/anthropic-cookbook/main/misc/mcp_diagram.png" alt="MCP Architecture" width="600"/>

*How MCP connects Claude with external services*
</div>

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Google Cloud Project with OAuth credentials
- (Optional) API keys for Twitter, Product Hunt, GitHub

### Step 1: Clone the Repository
```bash
git clone https://github.com/kumarAbhishek2004/ai-newsletter-mcp.git
cd ai-newsletter-mcp
```

### Step 2: Install Dependencies
```bash
pip install fastmcp arxiv requests google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
```

### Step 3: Set Up Environment Variables
Create a `.env` file in the project root:

```env
# Required: Google OAuth (for Drive & Gmail)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REFRESH_TOKEN=your_refresh_token_here

# Optional: Newsletter folder in Google Drive
NEWSLETTER_FOLDER_ID=your_folder_id_here

# Optional: External APIs
GITHUB_TOKEN=your_github_token_here
PRODUCT_HUNT_API_KEY=your_producthunt_key_here
TWITTER_BEARER_TOKEN=your_twitter_token_here
```

### Step 4: Run the Server
```bash
python ai_newsletter_server.py
```

---

## 📋 Usage

### Quick Start with Claude Desktop

1. **Configure Claude Desktop** to use this MCP server
2. **Start a conversation** with Claude
3. **Use built-in prompts** to guide the workflow:

```
Use the research_newsletter_prompt to gather this week's content
```

### Available Tools

#### Research Tools
- `fetch_all_research()` - Batch fetch from all sources
- `search_arxiv_papers()` - Get latest research papers
- `fetch_github_trending()` - Find trending repositories
- `search_product_hunt()` - Discover new AI products
- `fetch_twitter_trends()` - Track viral conversations
- `fetch_past_newsletters()` - Analyze previous issues
- `scan_gmail_feedback()` - Read reader responses

#### Editing Tools
- `create_newsletter_draft()` - Generate structured draft
- `organize_content_sections()` - Prioritize content
- `validate_newsletter_content()` - Quality check
- `preview_newsletter()` - Text preview

#### Publishing Tools
- `generate_html_newsletter()` - Create HTML version
- `save_to_drive()` - Upload to Google Drive
- `export_newsletter()` - Export in multiple formats

### Example Workflow

```python
# 1. Gather research content
research_data = fetch_all_research({
    "days_back": 7,
    "max_papers": 10
})

# 2. Create draft
draft = create_newsletter_draft(
    research_content=research_data["research_data"],
    issue_number=42
)

# 3. Validate content
validation = validate_newsletter_content(draft["draft"])

# 4. Generate HTML
html = generate_html_newsletter(draft["draft"])

# 5. Save to Drive
result = save_to_drive(
    content=html["html"],
    filename="newsletter_issue_42.html"
)
```

---

## ⚙️ Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Drive API** and **Gmail API**
4. Create OAuth 2.0 credentials
5. Generate refresh token using OAuth playground
6. Add credentials to `.env` file

### Optional API Keys

- **GitHub**: [Create personal access token](https://github.com/settings/tokens)
- **Product Hunt**: [Get API key](https://www.producthunt.com/v2/oauth/applications)
- **Twitter**: [Apply for developer access](https://developer.twitter.com)

---

<div align="center">
<img src="https://media.giphy.com/media/L1R1tvI9svkIWwpVYr/giphy.gif" alt="Newsletter Automation" width="400"/>

*Automate your newsletter workflow effortlessly*
</div>

---

## 🛠️ Advanced Features

### Rate Limiting
Built-in rate limiting prevents API abuse:
- arXiv: 30 calls/minute
- GitHub: 30 calls/minute
- Product Hunt: 20 calls/minute
- Twitter: 15 calls/minute

### Error Handling
All API calls are wrapped with:
- Timeout protection
- Retry logic
- Graceful failure handling
- Detailed error logging

### Content Validation
Automatic checks for:
- Minimum content requirements
- Missing sections
- Empty fields
- Proper formatting

---

## 📊 Sample Output

### Text Preview
```
============================================================
CampusX AI Newsletter #42
Issue #42 | November 02, 2025
============================================================

📊 CONTENT SUMMARY:
- Papers: 10
- GitHub Repos: 8
- Products: 5
- Tweets: 3

🎯 BIG STORY:
Breakthrough in Multi-Modal AI Reasoning

📄 TOP PAPERS:
1. Efficient Attention Mechanisms for Transformers
2. Zero-Shot Learning in Vision-Language Models
3. Reinforcement Learning for Real-World Robotics
```

### HTML Newsletter
- 📱 Mobile-responsive design
- 🎨 Modern, clean aesthetic
- 🔗 Clickable links to all sources
- 📊 Visual badges and metrics
- 💌 Professional email format

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Author



<div align="center">
<img src="./github_photo (1).png" alt="Kumar Abhishek" width="150" height="150" style="border-radius: 50%;" />

### **Kumar Abhishek**

**ML Engineer & Full Stack Developer**

🎓 BTech ECE @ IIIT Una  
💡 Specializing in AI/ML, GenAI, and Web Development

[![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white)](mailto:abhishek.kr0418@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/kumar-abhishek-6b5828288)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/kumarAbhishek2004)

</div>

---

## 📞 Contact & Support

- **Email**: abhishek.kr0418@gmail.com
- **GitHub**: [kumarAbhishek2004](https://github.com/kumarAbhishek2004)
- **LinkedIn**: [kumar-abhishek-6b5828288](https://linkedin.com/in/kumar-abhishek-6b5828288)
- **Issues**: [Report Bug](https://github.com/kumarAbhishek2004/ai-newsletter-mcp/issues)

---

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - Simplified MCP server creation
- [Anthropic](https://www.anthropic.com) - Claude AI and MCP framework
- [arXiv API](https://arxiv.org/help/api) - Research paper access
- [GitHub API](https://docs.github.com/en/rest) - Repository data
- [Product Hunt API](https://api.producthunt.com/v2/docs) - Product discovery

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with 🤖 AI &  Human creativity

</div>