# LLM Timeline — CLAUDE.md

LLMの歴史をインタラクティブなタイムラインで可視化するプロジェクト。
2017年Transformerから現在まで、モデルリリース・論文・声明・政策を追跡する。

## よく使うコマンド

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# site/data.json を生成（タイムライン描画データ）
python scripts/build.py

# ローカルサーバで確認 → http://localhost:8000
python -m http.server 8000 --directory site/

# 自動収集（ドライラン：保存なし）
python scripts/collect.py --dry-run

# 自動収集（実際に保存）
python scripts/collect.py
python scripts/collect.py --rss-only
python scripts/collect.py --arxiv-only
```

## アーキテクチャ

```
data/events/*.md      → scripts/build.py → site/data.json → site/index.html
data/config/*.yaml                                         → site/js/timeline.js
                                                           → site/css/style.css
scripts/collect.py    → data/events/*.md  （新イベント自動収集）
```

- **data/events/**: 各イベントのMarkdownファイル（フロントマター付き）
- **data/config/companies.yaml**: 企業定義（名前・色・RSS URL）
- **data/config/persons.yaml**: 人物定義（名前・役職・Twitter）
- **config.yaml**: 収集設定（RSS URL・arXiv・Twitter・NewsAPI）
- **scripts/build.py**: Markdownを読み込み `site/data.json` を生成
- **scripts/collect.py**: RSS/arXiv/Twitter/NewsAPIから新イベントを収集
- **scripts/sources/**: 各収集ソースのモジュール（rss.py, arxiv.py, twitter.py, news.py）
- **site/**: 静的サイト（HTML/CSS/JS）
- **.github/workflows/collect-and-deploy.yml**: 毎日JST10:00に自動収集＆GitHub Pagesデプロイ

## イベントファイルの形式

`data/events/YYYY-MM-DD_slug.md` のファイル名で保存：

```markdown
---
date: 2025-01-01
type: model_release  # model_release | announcement | statement | paper | policy
company: openai      # companies.yamlの識別子
person: null         # persons.yamlの識別子（または null）
title: "イベントタイトル"
description: "説明文"
source_url: https://example.com/source
tags: [tag1, tag2]
importance: high     # high | medium | low
auto_collected: false
---
追加本文（任意）
```

## 追跡対象

**企業**: openai / anthropic / google / meta / mistral / xai / deepseek / huggingface / nvidia

**人物**: Sam Altman / Dario Amodei / Demis Hassabis / Yann LeCun / Ilya Sutskever / Geoffrey Hinton / Elon Musk / Jensen Huang

## Python要件

- Python 3.11+
- feedparser, requests, pyyaml, python-frontmatter, arxiv, tweepy, python-dateutil

## GitHub Actions

- **スケジュール**: 毎日 UTC 01:00（JST 10:00）
- **手動実行**: Actions → Run workflow（DRY-RUNオプションあり）
- **必要なSecrets**: `TWITTER_BEARER_TOKEN`（任意）、`NEWSAPI_KEY`（任意）
- Twitter・NewsAPIは `config.yaml` で `enabled: false` のままでも RSS・arXiv のみで動作する
