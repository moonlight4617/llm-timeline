"""RSSフィード収集モジュール"""
import feedparser
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import re


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text[:60]


def fetch_rss_events(config: dict, data_dir: Path) -> list[dict]:
    """RSSフィードから新規イベントを取得する"""
    feeds = config.get('rss_feeds', [])
    events = []

    for feed_cfg in feeds:
        company = feed_cfg['company']
        url = feed_cfg['url']
        name = feed_cfg['name']

        print(f"  [RSS] {name} ({url})")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:  # 最新10件
                event = _parse_entry(entry, company, name)
                if event:
                    events.append(event)
        except Exception as e:
            print(f"    ERROR: {e}")

    return events


def _parse_entry(entry, company: str, source_name: str) -> Optional[dict]:
    """feedパーサーのエントリをイベント辞書に変換する"""
    # 日付取得
    date_parsed = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
    if not date_parsed:
        return None
    date = datetime(*date_parsed[:6], tzinfo=timezone.utc)
    date_str = date.strftime('%Y-%m-%d')

    # タイトル・URL・説明
    title = getattr(entry, 'title', '').strip()
    source_url = getattr(entry, 'link', '')
    summary = getattr(entry, 'summary', '') or ''
    # HTMLタグ除去
    summary = re.sub(r'<[^>]+>', '', summary).strip()
    if len(summary) > 300:
        summary = summary[:297] + '...'

    if not title or not source_url:
        return None

    return {
        'date': date_str,
        'type': 'announcement',
        'company': company,
        'person': None,
        'title': title,
        'description': summary or f'{source_name}からの自動収集記事。',
        'source_url': source_url,
        'tags': [company, 'auto-collected'],
        'importance': 'medium',
        'auto_collected': True,
    }
