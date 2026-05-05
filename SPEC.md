# Style Learning Feature - SPEC

## 1. Overview

This feature allows users to:
1. Scrape real Reddit posts from any subreddit or user
2. Write their own comments for these posts
3. The AI learns from the user's comment style
4. Future generated comments will match the user's personal style

## 2. Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Reddit Scraper  │ ──▶ │  Style Learner  │ ──▶ │ Comment Service │
│  (posts + votes) │     │  (analyzes)     │     │ (generates)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 3. Data Model

### StyleSample Table
```sql
CREATE TABLE style_sample (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_title TEXT,
    post_content TEXT,
    post_url TEXT,
    user_comment TEXT NOT NULL,
    upvotes INTEGER DEFAULT 0,
    analysis_data TEXT,  -- JSON: tone, length, vocabulary, etc.
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### StyleProfile Table
```sql
CREATE TABLE style_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    avg_length INTEGER,           -- average comment length
    avg_word_count INTEGER,
    common_words TEXT,            -- JSON array of frequent words
    tone_patterns TEXT,           -- JSON array of tone markers
    formality_score REAL,         -- 0-1 scale
    humor_score REAL,             -- 0-1 scale
    aggression_score REAL,        -- 0-1 scale
    emoji_usage_rate REAL,        -- emojis per comment
    sentence_style TEXT,          -- JSON: question_ratio, exclamation_ratio, etc.
    topic_keywords TEXT,          -- JSON array of topics they engage with
    sample_count INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

## 4. Components

### 4.1 Reddit Scraper (`app/services/reddit_scraper.py`)
- Fetch posts from subreddit via Reddit API
- Fetch user's comment history
- Store raw data in style_sample table
- Requires Reddit authentication (cookie-based)

### 4.2 Style Learner (`app/services/style_learner.py`)
- Analyze user's comments from style_sample
- Extract patterns:
  - Vocabulary (common words, slang, abbreviations)
  - Tone (formal/casual, aggressive/passive, humorous/serious)
  - Structure (sentence length, question usage, exclamation usage)
  - Engagement (emoji usage, mention patterns)
- Update style_profile with extracted patterns

### 4.3 Style-Informed Generation
- When generating comments, include style profile in the prompt
- Adjust temperature, length based on profile
- Match user's voice patterns

## 5. API Endpoints

### GET /api/style/posts
Fetch posts from subreddit for user to comment on.

Query params:
- `subreddit`: string (required)
- `sort`: hot|new|top (default: hot)
- `limit`: 1-25 (default: 10)

Response:
```json
{
  "success": true,
  "posts": [
    {
      "id": "post_123",
      "title": "Post title",
      "content": "Post body...",
      "url": "https://reddit.com/...",
      "score": 1234,
      "num_comments": 56,
      "subreddit": "askreddit"
    }
  ]
}
```

### POST /api/style/sample
Submit a user-written comment for a post (for learning).

Request:
```json
{
  "post_id": "post_123",
  "post_title": "Post title",
  "post_content": "Post body...",
  "post_url": "https://reddit.com/...",
  "user_comment": "This is my comment..."
}
```

### GET /api/style/profile
Get current user's style profile.

Response:
```json
{
  "success": true,
  "profile": {
    "sample_count": 25,
    "avg_length": 85,
    "tone": "casual",
    "formality_score": 0.3,
    "emoji_usage_rate": 0.4,
    "top_words": ["lol", "yeah", "btw"],
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### POST /api/style/analyze
Trigger style analysis (batch process user's samples).

### GET /api/style/samples
List user's style samples (paginated).

Query params:
- `page`: 1+
- `limit`: 1-50

## 6. User Flow

1. User opens Style Learning section
2. User selects subreddit to practice on
3. System shows real posts from that subreddit
4. User writes their own comment for each post
5. User submits comment → stored in style_sample
6. After 5+ samples, user can trigger "Analyze My Style"
7. System analyzes patterns and updates style_profile
8. Future comment generation uses style_profile

## 7. Integration with Chrome Extension

Add new section in popup:
- "Practice Mode" tab
- Fetch posts, user writes comments
- Submit to learn their style

## 8. Implementation Priority

1. **Phase 1**: Scraper + Sample storage (basic collection)
2. **Phase 2**: Style analysis (pattern extraction)
3. **Phase 3**: Style-informed generation
4. **Phase 4**: Chrome extension integration

## 9. Non-Goals

- Auto-scraping without user interaction
- Posting comments to Reddit automatically
- Analyzing other users' comments without permission