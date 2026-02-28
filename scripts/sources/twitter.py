"""Twitter/X API収集モジュール（API取得後に有効化）

設定方法:
  1. https://developer.x.com でBearerTokenを取得（Basic以上のプラン）
  2. GitHub ActionsのSecretsに TWITTER_BEARER_TOKEN を設定
  3. config.yaml で twitter.enabled: true に変更
"""
import os
import re
import requests
from datetime import datetime, timezone
from typing import Optional


TWITTER_API_BASE = "https://api.twitter.com/2"

# X(Twitter)のユーザー名→人物識別子マッピング
HANDLE_PERSON_MAP = {
    "sama": "sam_altman",
    "darioamodei": "dario_amodei",
    "danielaamodei": "daniela_amodei",
    "demishassabis": "demis_hassabis",
    "ylecun": "yann_lecun",
    "ilyasut": "ilya_sutskever",
    "geoffreyhinton": "geoffrey_hinton",
    "elonmusk": "elon_musk",
    "jenshwang": "jensen_huang",
    "gdb": "greg_brockman",
}

# 人物→企業マッピング
PERSON_COMPANY_MAP = {
    "sam_altman": "openai",
    "dario_amodei": "anthropic",
    "daniela_amodei": "anthropic",
    "demis_hassabis": "google",
    "yann_lecun": "meta",
    "ilya_sutskever": None,
    "geoffrey_hinton": None,
    "elon_musk": "xai",
    "jensen_huang": "nvidia",
    "greg_brockman": "openai",
}


def fetch_twitter_events(config: dict) -> list[dict]:
    """X(Twitter) API v2からフォロー対象の発言を収集する"""
    twitter_cfg = config.get('twitter', {})
    if not twitter_cfg.get('enabled', False):
        print("  [Twitter] 無効化されています。APIキー取得後に config.yaml で enabled: true に変更してください")
        return []

    bearer_token_env = twitter_cfg.get('bearer_token_env', 'TWITTER_BEARER_TOKEN')
    bearer_token = os.environ.get(bearer_token_env)
    if not bearer_token:
        print(f"  [Twitter] 環境変数 {bearer_token_env} が設定されていません")
        return []

    tracked_users = twitter_cfg.get('tracked_users', [])
    ai_keywords = twitter_cfg.get('ai_keywords', ['AI', 'LLM', 'model'])
    max_per_user = twitter_cfg.get('max_per_user', 5)

    headers = {"Authorization": f"Bearer {bearer_token}"}
    events = []

    # ユーザーIDを取得
    user_ids = _get_user_ids(tracked_users, headers)

    for handle, user_id in user_ids.items():
        print(f"  [Twitter] @{handle} のツイートを取得中...")
        tweets = _get_recent_tweets(user_id, max_per_user, headers)
        for tweet in tweets:
            # AIキーワードフィルタ
            text = tweet.get('text', '')
            if not _contains_ai_keyword(text, ai_keywords):
                continue
            event = _tweet_to_event(tweet, handle)
            if event:
                events.append(event)

    print(f"  [Twitter] {len(events)}件の発言を取得しました")
    return events


def _get_user_ids(handles: list[str], headers: dict) -> dict[str, str]:
    """ユーザー名からユーザーIDを一括取得する"""
    if not handles:
        return {}

    usernames = ','.join(handles[:100])
    url = f"{TWITTER_API_BASE}/users/by?usernames={usernames}&user.fields=id,name,username"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {u['username'].lower(): u['id'] for u in data.get('data', [])}
    except Exception as e:
        print(f"    ERROR: ユーザーID取得失敗: {e}")
        return {}


def _get_recent_tweets(user_id: str, max_results: int, headers: dict) -> list[dict]:
    """指定ユーザーの最近のツイートを取得する"""
    url = (
        f"{TWITTER_API_BASE}/users/{user_id}/tweets"
        f"?max_results={max_results}"
        f"&tweet.fields=created_at,text,entities"
        f"&exclude=retweets,replies"
    )
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json().get('data', [])
    except Exception as e:
        print(f"    ERROR: ツイート取得失敗 (user_id={user_id}): {e}")
        return []


def _contains_ai_keyword(text: str, keywords: list[str]) -> bool:
    """テキストにAI関連キーワードが含まれるか確認する"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _tweet_to_event(tweet: dict, handle: str) -> Optional[dict]:
    """ツイート辞書をイベント辞書に変換する"""
    text = tweet.get('text', '').strip()
    tweet_id = tweet.get('id', '')
    created_at = tweet.get('created_at', '')

    # 日付
    date_str = ''
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
        except ValueError:
            date_str = created_at[:10]

    # 人物・企業
    handle_lower = handle.lower()
    person = HANDLE_PERSON_MAP.get(handle_lower)
    company = PERSON_COMPANY_MAP.get(person) if person else None

    # タイトル（ツイートの最初の100文字）
    title_text = text[:80] + ('...' if len(text) > 80 else '')
    title = f"@{handle}: {title_text}"

    # ツイートURL
    source_url = f"https://x.com/{handle}/status/{tweet_id}"

    return {
        'date': date_str,
        'type': 'statement',
        'company': company,
        'person': person,
        'title': title,
        'description': text,
        'source_url': source_url,
        'tags': ['twitter', 'statement', 'auto-collected', handle_lower],
        'importance': 'medium',
        'auto_collected': True,
    }
