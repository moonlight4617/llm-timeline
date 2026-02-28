#!/usr/bin/env python3
"""
LLM Timeline - メイン収集スクリプト

使い方:
  python scripts/collect.py              # 全ソースから収集
  python scripts/collect.py --rss-only   # RSSのみ
  python scripts/collect.py --dry-run    # 保存せずに確認
"""
import sys
import argparse
import yaml
import re
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from sources.rss import fetch_rss_events
from sources.arxiv import fetch_arxiv_events
from sources.twitter import fetch_twitter_events
from sources.news import fetch_news_events


def load_config() -> dict:
    config_path = PROJECT_ROOT / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_existing_urls(events_dir: Path) -> set[str]:
    """既存イベントのsource_urlを収集して重複チェック用セットを返す"""
    urls = set()
    for md_file in events_dir.glob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        # YAMLフロントマターからsource_urlを抽出
        match = re.search(r'^source_url:\s*(.+)$', content, re.MULTILINE)
        if match:
            url = match.group(1).strip()
            if url and url != 'null':
                urls.add(url)
    return urls


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text, flags=re.ASCII)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:50]


def event_to_markdown(event: dict) -> str:
    """イベント辞書をMarkdownフロントマター形式に変換する"""
    person = f'"{event["person"]}"' if event.get("person") else 'null'
    company = f'"{event["company"]}"' if event.get("company") else 'null'
    tags = ', '.join(event.get('tags', []))

    lines = [
        '---',
        f'date: {event["date"]}',
        f'type: {event["type"]}',
        f'company: {company}',
        f'person: {person}',
        f'title: "{event["title"].replace(chr(34), chr(39))}"',
        f'description: "{event["description"].replace(chr(34), chr(39))}"',
        f'source_url: {event["source_url"]}',
        f'tags: [{tags}]',
        f'importance: {event.get("importance", "medium")}',
        f'auto_collected: {str(event.get("auto_collected", True)).lower()}',
        '---',
    ]
    return '\n'.join(lines) + '\n'


def save_event(event: dict, events_dir: Path, dry_run: bool = False) -> bool:
    """イベントをMarkdownファイルとして保存する。成功したらTrueを返す"""
    date = event.get('date', 'unknown')
    title_slug = slugify(event.get('title', 'event'))
    filename = f"{date}_{title_slug}.md"
    filepath = events_dir / filename

    if filepath.exists():
        return False  # 同名ファイルが既に存在

    content = event_to_markdown(event)

    if dry_run:
        print(f"    [DRY-RUN] {filename}")
        print(f"      {event['title'][:60]}")
        return True

    filepath.write_text(content, encoding='utf-8')
    return True


def main():
    parser = argparse.ArgumentParser(description='LLM Timelineイベント収集')
    parser.add_argument('--rss-only', action='store_true', help='RSSのみ収集')
    parser.add_argument('--arxiv-only', action='store_true', help='arXivのみ収集')
    parser.add_argument('--twitter-only', action='store_true', help='Twitterのみ収集')
    parser.add_argument('--news-only', action='store_true', help='Newsのみ収集')
    parser.add_argument('--dry-run', action='store_true', help='保存せずに確認のみ')
    args = parser.parse_args()

    config = load_config()
    events_dir = PROJECT_ROOT / 'data' / 'events'
    events_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== LLM Timeline 収集開始 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    if args.dry_run:
        print("  *** DRY-RUN モード: ファイルは保存されません ***")

    # 既存URLを読み込み（重複排除用）
    existing_urls = load_existing_urls(events_dir)
    print(f"  既存イベント数: {len(list(events_dir.glob('*.md')))}件")

    all_events = []

    # 収集実行
    run_all = not any([args.rss_only, args.arxiv_only, args.twitter_only, args.news_only])

    if run_all or args.rss_only:
        print("\n[1] RSS収集...")
        all_events.extend(fetch_rss_events(config, events_dir))

    if run_all or args.arxiv_only:
        print("\n[2] arXiv収集...")
        all_events.extend(fetch_arxiv_events(config))

    if run_all or args.twitter_only:
        print("\n[3] Twitter収集...")
        all_events.extend(fetch_twitter_events(config))

    if run_all or args.news_only:
        print("\n[4] News収集...")
        all_events.extend(fetch_news_events(config))

    # 重複排除・保存
    print(f"\n=== 収集結果: {len(all_events)}件 ===")
    saved = 0
    skipped_dup = 0
    skipped_no_url = 0

    for event in all_events:
        url = event.get('source_url', '')
        if not url:
            skipped_no_url += 1
            continue
        if url in existing_urls:
            skipped_dup += 1
            continue

        if save_event(event, events_dir, dry_run=args.dry_run):
            saved += 1
            existing_urls.add(url)
        else:
            skipped_dup += 1

    print(f"  保存: {saved}件")
    print(f"  重複スキップ: {skipped_dup}件")
    print(f"  URL不明スキップ: {skipped_no_url}件")
    print(f"\n=== 完了 ===")


if __name__ == '__main__':
    main()
