# LLM Timeline — AIの変遷を見える化

2017年Transformer論文から現在まで、LLMの歴史をインタラクティブなタイムラインで追跡・可視化するシステム。

## 動作要件

- **Python 3.11 以上**
- pip（requirements.txtからインストール）
- インターネット接続（RSS・arXiv収集用）

## 機能

- **タイムライン表示**: 企業ごとに色分けされたインタラクティブなタイムライン
- **自動収集**: RSS・arXiv・Twitter/X APIから毎日自動更新
- **フィルタ・検索**: 企業/種別/重要度/キーワードでフィルタリング
- **詳細表示**: イベントをクリックでソースリンク付き詳細を表示

## 追跡対象

### 企業
OpenAI / Anthropic / Google DeepMind / Meta AI / Mistral AI / xAI / DeepSeek

### 主要人物
Sam Altman / Dario Amodei / Demis Hassabis / Yann LeCun / Ilya Sutskever / Geoffrey Hinton / Elon Musk / Jensen Huang

## セットアップ・ローカル確認

### 1. 依存パッケージインストール
```bash
pip install -r requirements.txt
```

### 2. data.json の生成
```bash
python scripts/build.py
```
> `site/data.json` が生成される。これがタイムラインの描画データ。

### 3. ローカルサーバで確認
```bash
python -m http.server 8000 --directory site/
```
→ http://localhost:8000 を開く

### 4. 自動収集テスト（DRY-RUN）
```bash
python scripts/collect.py --dry-run
```
> ファイルを保存せず、取得できるイベントを標準出力で確認する。

### 5. 実際に収集
```bash
python scripts/collect.py           # 全ソースから収集
python scripts/collect.py --rss-only    # RSSのみ
python scripts/collect.py --arxiv-only  # arXivのみ
```
> 新規イベントが `data/events/YYYY-MM-DD_タイトル.md` として保存される。
> その後 `python scripts/build.py` を実行して `site/data.json` を更新すること。

## GitHub Pages デプロイ

### 初回設定
1. GitHubリポジトリの **Settings → Pages** を開く
2. **Source** を `GitHub Actions` に変更して保存
3. **Actions → LLM Timeline — 自動収集 & GitHub Pages デプロイ** を手動実行
   - `workflow_dispatch`（Run workflow ボタン）から実行可能
4. 完了後、`https://<username>.github.io/<repo>/` でサイトを確認

### 自動更新スケジュール
- 毎日 **JST 10:00（UTC 01:00）** に自動実行
- RSSフィード・arXiv・有効なAPIからイベントを収集 → コミット → GitHub Pagesへデプロイ

### GitHub Actions 手動実行
リポジトリの **Actions** タブ → ワークフロー選択 → **Run workflow** で随時実行可能。
`DRY-RUN` オプションを `true` にすると保存なしで動作確認できる。

## APIキーの設定（オプション）

### Twitter/X API
1. [developer.x.com](https://developer.x.com) で **Basic プラン以上**のアカウントを作成
2. プロジェクトを作成し **Bearer Token** を取得
3. GitHubリポジトリの **Settings → Secrets and variables → Actions** に `TWITTER_BEARER_TOKEN` を追加
4. `config.yaml` の `twitter.enabled` を `true` に変更

### NewsAPI
1. [newsapi.org](https://newsapi.org) で無料APIキーを取得（月500リクエスト）
2. GitHubリポジトリの **Settings → Secrets → Actions** に `NEWSAPI_KEY` を追加
3. `config.yaml` の `news.enabled` を `true` に変更

> APIキー未設定の場合も、RSS・arXivのみで自動収集は動作する。

## 追跡対象の追加・変更

### 企業を追加する
`data/config/companies.yaml` に追記する:
```yaml
companies:
  new_company:
    name: 新企業名
    color: "#RRGGBB"   # タイムラインの表示色
    url: https://example.com
    blog_rss: https://example.com/feed.xml  # RSSがあれば自動収集される
    founded: 2024
    description: 説明文
```

### 人物を追加する
`data/config/persons.yaml` に追記し、`config.yaml` の `twitter.tracked_users` にも Xのハンドルを追加する:
```yaml
persons:
  new_person:
    name: 氏名
    role: 役職
    company: company_id  # companies.yamlの識別子
    twitter_handle: handle_name
    twitter_id: null
    description: 説明文
```

## 手動でイベントを追加

`data/events/` に以下の形式でMarkdownファイルを作成:

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
追加の説明（任意）
```

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| タイムラインが表示されない | `data.json` がない | `python scripts/build.py` を実行 |
| `ModuleNotFoundError` | 依存パッケージ未インストール | `pip install -r requirements.txt` を実行 |
| RSSが取得できない | RSS URLの変更・ネットワークエラー | `config.yaml` のURLを確認、`--dry-run` で個別テスト |
| GitHub Actionsが失敗する | Secrets未設定やパーミッション不足 | Actions設定で `Read and write permissions` を有効化 |
| イベントが重複して保存される | `source_url` の変更 | `data/events/` 内の該当ファイルを手動削除 |
| Twitter収集が動かない | APIキー未設定またはプラン不足 | Bearer Token確認、または `twitter.enabled: false` のまま運用 |

## ファイル構成

```
llm-timeline/
├── data/
│   ├── events/        ← イベントMarkdownファイル（50件以上の初期データ入り）
│   └── config/
│       ├── companies.yaml
│       └── persons.yaml
├── scripts/
│   ├── collect.py     ← 自動収集
│   ├── build.py       ← data.json生成
│   └── sources/       ← RSS/arXiv/Twitter/News各モジュール
├── site/
│   ├── index.html
│   ├── js/timeline.js
│   ├── css/style.css
│   └── data.json      ← buildで生成（gitignoreしても可）
├── config.yaml        ← 収集設定
├── requirements.txt
└── .github/workflows/
    └── collect-and-deploy.yml
```
