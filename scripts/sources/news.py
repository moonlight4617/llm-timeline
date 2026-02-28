"""NewsAPI収集モジュール（APIキー取得後に有効化）

設定方法:
  1. https://newsapi.org で無料APIキーを取得
  2. GitHub ActionsのSecretsに NEWSAPI_KEY を設定
  3. config.yaml で news.enabled: true に変更
"""
import os
import re
import requests
from datetime import datetime, timezone
from typing import Optional


NEWSAPI_BASE = "https://newsapi.org/v2/everything"

# タイトルキーワード→企業マッピング
TITLE_COMPANY_MAP = {
    "openai": "openai",
    "chatgpt": "openai",
    "gpt-4": "openai",
    "gpt-5": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "google deepmind": "google",
    "deepmind": "google",
    "gemini": "google",
    "meta ai": "meta",
    "llama": "meta",
    "mistral": "mistral",
    "deepseek": "deepseek",
    "grok": "xai",
    "xai": "xai",
}


def fetch_news_events(config: dict) -> list[dict]:
    """NewsAPIからLLM関連ニュースを収集する"""
    news_cfg = config.get('news', {})
    if not news_cfg.get('enabled', False):
        print("  [News] 無効化されています。config.yaml で news.enabled: true に変更してください")
        return []

    api_key_env = news_cfg.get('api_key_env', 'NEWSAPI_KEY')
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"  [News] 環境変数 {api_key_env} が設定されていません")
        return []

    keywords = news_cfg.get('keywords', ['large language model', 'GPT', 'Claude'])
    sources = news_cfg.get('sources', [])
    max_per_run = news_cfg.get('max_per_run', 20)

    query = ' OR '.join(f'"{kw}"' for kw in keywords[:5])
    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': max_per_run,
        'apiKey': api_key,
    }
    if sources:
        params['sources'] = ','.join(sources)

    print(f"  [News] NewsAPIクエリ実行中... ({len(keywords)}キーワード, {max_per_run}件)")
    try:
        resp = requests.get(NEWSAPI_BASE, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get('articles', [])
    except Exception as e:
        print(f"    ERROR: NewsAPI呼び出し失敗: {e}")
        return []

    events = []
    for article in articles:
        event = _article_to_event(article)
        if event:
            events.append(event)

    print(f"  [News] {len(events)}件のニュースを取得しました")
    return events


def _article_to_event(article: dict) -> Optional[dict]:
    """NewsAPIの記事をイベント辞書に変換する"""
    title = (article.get('title') or '').strip()
    url = (article.get('url') or '').strip()
    description = (article.get('description') or '').strip()
    content = (article.get('content') or '').strip()
    published_at = (article.get('publishedAt') or '').strip()

    if not title or not url or url == 'https://removed.com':
        return None

    # 日付
    date_str = ''
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except ValueError:
            date_str = published_at[:10]

    # 説明文の整理
    text = description or content or ''
    text = re.sub(r'\[\+\d+ chars\]', '', text).strip()
    if len(text) > 300:
        text = text[:297] + '...'

    # 企業推定
    company = _infer_company(title + ' ' + text)

    # タグ
    tags = ['news', 'auto-collected']
    if company:
        tags.append(company)

    return {
        'date': date_str,
        'type': 'announcement',
        'company': company,
        'person': None,
        'title': title,
        'description': text or f'NewsAPIから自動収集された記事。',
        'source_url': url,
        'tags': tags,
        'importance': 'medium',
        'auto_collected': True,
    }


def _infer_company(text: str) -> Optional[str]:
    """テキストキーワードから企業を推定する"""
    text_lower = text.lower()
    for keyword, company in TITLE_COMPANY_MAP.items():
        if keyword in text_lower:
            return company
    return None
