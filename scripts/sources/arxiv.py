"""arXiv論文収集モジュール"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
import re


ARXIV_API = "http://export.arxiv.org/api/query"

# 著者→人物識別子マッピング（主要研究者）
AUTHOR_PERSON_MAP = {
    "sam altman": "sam_altman",
    "dario amodei": "dario_amodei",
    "ilya sutskever": "ilya_sutskever",
    "yann lecun": "yann_lecun",
    "geoffrey hinton": "geoffrey_hinton",
}

# タイトル→企業識別子マッピング（キーワードベース）
TITLE_COMPANY_MAP = {
    "gpt": "openai",
    "chatgpt": "openai",
    "claude": "anthropic",
    "gemini": "google",
    "palm": "google",
    "bard": "google",
    "llama": "meta",
    "mistral": "mistral",
    "deepseek": "deepseek",
    "grok": "xai",
}


def fetch_arxiv_events(config: dict) -> list[dict]:
    """arXiv APIから新規LLM論文を取得する"""
    arxiv_cfg = config.get('arxiv', {})
    if not arxiv_cfg.get('enabled', True):
        print("  [arXiv] 無効化されています (config.yaml: arxiv.enabled: false)")
        return []

    categories = arxiv_cfg.get('categories', ['cs.CL', 'cs.AI'])
    keywords = arxiv_cfg.get('keywords', ['large language model', 'GPT', 'Claude'])
    max_results = arxiv_cfg.get('max_results', 10)
    importance_keywords = arxiv_cfg.get('importance_keywords', [])

    # クエリ構築: カテゴリ + キーワード
    cat_query = ' OR '.join(f'cat:{c}' for c in categories)
    kw_query = ' OR '.join(f'ti:"{k}" OR abs:"{k}"' for k in keywords[:5])
    search_query = f'({cat_query}) AND ({kw_query})'

    params = {
        'search_query': search_query,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending',
        'max_results': max_results,
    }

    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    print(f"  [arXiv] クエリ実行中... ({len(keywords)}キーワード, {max_results}件)")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"    ERROR: arXiv API呼び出し失敗: {e}")
        return []

    events = _parse_arxiv_response(content, importance_keywords)
    print(f"    {len(events)}件の論文を取得しました")
    return events


def _parse_arxiv_response(xml_content: str, importance_keywords: list) -> list[dict]:
    """arXiv APIレスポンス（Atom XML）をパースしてイベントリストを返す"""
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"    XMLパースエラー: {e}")
        return []

    events = []
    for entry in root.findall('atom:entry', ns):
        event = _parse_arxiv_entry(entry, ns, importance_keywords)
        if event:
            events.append(event)

    return events


def _parse_arxiv_entry(entry, ns: dict, importance_keywords: list) -> Optional[dict]:
    """arXiv Atomエントリをイベント辞書に変換する"""
    title_el = entry.find('atom:title', ns)
    summary_el = entry.find('atom:summary', ns)
    published_el = entry.find('atom:published', ns)
    id_el = entry.find('atom:id', ns)

    if title_el is None or id_el is None:
        return None

    title = (title_el.text or '').strip().replace('\n', ' ')
    summary = (summary_el.text or '').strip().replace('\n', ' ') if summary_el is not None else ''
    if len(summary) > 300:
        summary = summary[:297] + '...'

    # 日付
    date_str = ''
    if published_el is not None and published_el.text:
        try:
            dt = datetime.fromisoformat(published_el.text.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except ValueError:
            date_str = published_el.text[:10]

    # URL
    arxiv_id = (id_el.text or '').strip()

    # 著者
    authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)
               if a.find('atom:name', ns) is not None]
    person = None
    for author in authors:
        key = author.lower()
        if key in AUTHOR_PERSON_MAP:
            person = AUTHOR_PERSON_MAP[key]
            break

    # 企業推定（タイトルキーワードから）
    company = _infer_company(title)

    # 重要度
    importance = 'medium'
    title_lower = title.lower()
    for kw in importance_keywords:
        if kw.lower() in title_lower:
            importance = 'high'
            break

    # タグ
    tags = ['paper', 'arxiv', 'auto-collected']
    if company:
        tags.append(company)

    return {
        'date': date_str,
        'type': 'paper',
        'company': company,
        'person': person,
        'title': title,
        'description': summary,
        'source_url': arxiv_id,
        'tags': tags,
        'importance': importance,
        'auto_collected': True,
    }


def _infer_company(title: str) -> Optional[str]:
    """タイトルキーワードから企業を推定する"""
    title_lower = title.lower()
    for keyword, company in TITLE_COMPANY_MAP.items():
        if keyword in title_lower:
            return company
    return None
