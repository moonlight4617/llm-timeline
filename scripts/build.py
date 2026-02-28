#!/usr/bin/env python3
"""
LLM Timeline - ビルドスクリプト
Markdownファイル群を読み込み、静的サイト用の data.json を生成する

使い方:
  python scripts/build.py
  python scripts/build.py --output site/data.json
"""
import sys
import json
import yaml
import re
import argparse
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent.parent
EVENTS_DIR = PROJECT_ROOT / 'data' / 'events'
CONFIG_DIR = PROJECT_ROOT / 'data' / 'config'
SITE_DIR = PROJECT_ROOT / 'site'

# 企業カラー（config読み込み前のフォールバック）
DEFAULT_COLORS = {
    'openai': '#00A67E',
    'anthropic': '#D4A017',
    'google': '#4285F4',
    'meta': '#0866FF',
    'mistral': '#FF6B6B',
    'xai': '#1DA1F2',
    'deepseek': '#7C3AED',
    'huggingface': '#FF9D00',
    'nvidia': '#76B900',
}

TYPE_ICONS = {
    'model_release': '🤖',
    'announcement': '📢',
    'statement': '💬',
    'paper': '📄',
    'policy': '🏛️',
}

IMPORTANCE_ORDER = {'high': 0, 'medium': 1, 'low': 2}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Markdownのフロントマター（YAML）を解析して(meta, body)を返す"""
    if not content.startswith('---'):
        return {}, content

    end = content.find('\n---', 3)
    if end == -1:
        return {}, content

    yaml_str = content[3:end].strip()
    body = content[end + 4:].strip()

    try:
        meta = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError as e:
        print(f"    YAML解析エラー: {e}")
        meta = {}

    return meta, body


def load_events() -> list[dict]:
    """eventsディレクトリからすべてのMarkdownを読み込む"""
    events = []
    md_files = sorted(EVENTS_DIR.glob('*.md'))

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            meta, body = parse_frontmatter(content)

            if not meta.get('date') or not meta.get('title'):
                print(f"  SKIP (date/titleなし): {md_file.name}")
                continue

            # 日付の正規化
            date_val = meta['date']
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)

            # タグをリストに正規化
            tags = meta.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]

            event = {
                'id': md_file.stem,
                'date': date_str,
                'type': meta.get('type', 'announcement'),
                'company': meta.get('company'),
                'person': meta.get('person'),
                'title': str(meta.get('title', '')),
                'description': str(meta.get('description', '')),
                'source_url': str(meta.get('source_url', '')),
                'tags': [str(t) for t in tags if t],
                'importance': meta.get('importance', 'medium'),
                'auto_collected': bool(meta.get('auto_collected', False)),
                'body': body,
            }
            events.append(event)

        except Exception as e:
            print(f"  ERROR ({md_file.name}): {e}")

    # 日付でソート
    events.sort(key=lambda e: (e['date'], IMPORTANCE_ORDER.get(e['importance'], 1)))
    return events


def load_companies() -> dict:
    """companies.yamlを読み込む"""
    path = CONFIG_DIR / 'companies.yaml'
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('companies', {})


def load_persons() -> dict:
    """persons.yamlを読み込む"""
    path = CONFIG_DIR / 'persons.yaml'
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    return data.get('persons', {})


def enrich_events(events: list[dict], companies: dict, persons: dict) -> list[dict]:
    """イベントに企業カラー・人物名などのメタ情報を付加する"""
    for event in events:
        company_id = event.get('company')
        person_id = event.get('person')

        # 企業情報
        company_info = companies.get(company_id, {}) if company_id else {}
        event['company_name'] = company_info.get('name', company_id or '')
        event['company_color'] = company_info.get('color', DEFAULT_COLORS.get(company_id, '#888888'))

        # 人物情報
        person_info = persons.get(person_id, {}) if person_id else {}
        event['person_name'] = person_info.get('name', person_id or '')

        # タイプアイコン
        event['type_icon'] = TYPE_ICONS.get(event['type'], '📌')

    return events


def build_data_json(events: list[dict], companies: dict, persons: dict) -> dict:
    """静的サイト用のデータオブジェクトを構築する"""
    # 統計情報
    type_counts = {}
    company_counts = {}
    for e in events:
        t = e['type']
        type_counts[t] = type_counts.get(t, 0) + 1
        c = e.get('company') or 'other'
        company_counts[c] = company_counts.get(c, 0) + 1

    # 企業リスト（色情報付き）
    company_list = []
    for cid, cinfo in companies.items():
        company_list.append({
            'id': cid,
            'name': cinfo.get('name', cid),
            'color': cinfo.get('color', DEFAULT_COLORS.get(cid, '#888888')),
        })

    # 人物リスト
    person_list = []
    for pid, pinfo in persons.items():
        person_list.append({
            'id': pid,
            'name': pinfo.get('name', pid),
            'company': pinfo.get('company'),
            'role': pinfo.get('role', ''),
        })

    return {
        'meta': {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_events': len(events),
            'type_counts': type_counts,
            'company_counts': company_counts,
        },
        'companies': company_list,
        'persons': person_list,
        'events': events,
    }


def main():
    parser = argparse.ArgumentParser(description='LLM Timeline data.json生成')
    parser.add_argument('--output', default=str(SITE_DIR / 'data.json'),
                        help='出力ファイルパス (デフォルト: site/data.json)')
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=== LLM Timeline ビルド開始 ===")
    print(f"  イベントディレクトリ: {EVENTS_DIR}")

    print("\n[1] イベント読み込み中...")
    events = load_events()
    print(f"  {len(events)}件のイベントを読み込みました")

    print("\n[2] 設定ファイル読み込み中...")
    companies = load_companies()
    persons = load_persons()
    print(f"  企業: {len(companies)}社, 人物: {len(persons)}名")

    print("\n[3] メタ情報付加中...")
    events = enrich_events(events, companies, persons)

    print("\n[4] data.json生成中...")
    data = build_data_json(events, companies, persons)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== ビルド完了 ===")
    print(f"  出力: {output_path}")
    print(f"  総イベント数: {data['meta']['total_events']}")
    print(f"  期間: {events[0]['date'] if events else 'N/A'} 〜 {events[-1]['date'] if events else 'N/A'}")
    for t, count in sorted(data['meta']['type_counts'].items()):
        print(f"    {t}: {count}件")


if __name__ == '__main__':
    main()
