# 🤖 AI Newsletter Automation MCP Server

<div align="center">

![AI Newsletter Banner](https://img.shields.io/badge/AI-Newsletter-blue?style=for-the-badge&logo=openai&logoColor=white)
![MCP Server](https://img.shields.io/badge/MCP-Server-green?style=for-the-badge&logo=cloud&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python&logoColor=white)

**Automate your AI newsletter creation with intelligent research, curation, and publishing**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start-with-fastmcp-cloud) • [Usage](#-usage) • [Configuration](#-configuration)

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

## 🚀 Quick Start with FastMCP Cloud

### Option 1: Use Our Hosted Server (Recommended)

**No installation required!** Connect directly to our hosted MCP server:

#### Step 1: Open Claude Desktop Configuration

- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Step 2: Add This Configuration

```json
{
  "mcpServers": {
    "ai-newsletter": {
      "url": "https://linguistic-chocolate-grouse.fastmcp.app/mcp"
    }
  }
}
```

#### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. The AI Newsletter tools will now be available!

#### Step 4: Start Using It

Open a conversation with Claude and try:

```
Help me research and create this week's AI newsletter
```

Claude will automatically use the newsletter tools to gather content, organize it, and create a draft for you!

---

## 🛠️ Local Installation (For Developers)

### Prerequisites
- Python 3.8 or higher
- Google Cloud Project with OAuth credentials
- (Optional) API keys for Twitter, Product Hunt, GitHub

### Step 1: Clone the Repository
```bash
git clone https://github.com/kumarAbhishek2004/Ai_Newletter.git
cd Ai_Newletter
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
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

### Step 4: Run the Server Locally
```bash
python main.py
```

### Step 5: Configure Claude Desktop for Local Server
```json
{
  "mcpServers": {
    "ai-newsletter": {
      "command": "python",
      "args": ["/path/to/your/Ai_Newletter/main.py"]
    }
  }
}
```

---

## 📋 Usage

### Quick Start Workflow

Once connected, simply ask Claude:

**For Complete Newsletter Creation:**
```
Create this week's AI newsletter covering the latest papers, GitHub projects, and products
```

**For Specific Research:**
```
Search arXiv for papers about large language models from the past week
```

**For Organization:**
```
Organize my newsletter content into sections and prioritize the most important items
```

**For Publishing:**
```
Generate an HTML newsletter and save it to my Google Drive
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

**Conversation with Claude:**

> **You:** "Help me create this week's AI newsletter"

> **Claude:** *Uses fetch_all_research() to gather content from arXiv, GitHub, Product Hunt, etc.*

> **Claude:** "I've gathered 10 research papers, 8 trending repos, and 5 new products. Here's what I found..."

> **You:** "Great! Now organize this into sections and create a draft"

> **Claude:** *Uses create_newsletter_draft() to organize content*

> **Claude:** "I've created a draft with 5 sections. Would you like me to generate the HTML version?"

> **You:** "Yes, and save it to Google Drive"

> **Claude:** *Uses generate_html_newsletter() and save_to_drive()*

> **Claude:** "Done! Your newsletter has been saved to Google Drive. Here's the preview..."

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

## 📊 Sample Output

### Text Preview
```
============================================================
 AI Newsletter #4
Issue #4| November 02, 2025
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
- **Issues**: [Report Bug](https://github.com/kumarAbhishek2004/Ai_Newletter/issues)

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