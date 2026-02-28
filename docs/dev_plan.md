# LLM変遷 可視化システム 実装計画

## Context

LLM（大規模言語モデル）の歴史的変遷をリアルタイムで追跡・可視化するシステムを構築する。
2017年のTransformer論文から現在まで、主要企業のモデルリリース・発表・主要人物の発言を
Markdownファイルで管理し、GitHub Pages上で静的サイトとして公開する。

## 最終目標

データ収集（自動） → Markdownファイル保存 → 静的サイト生成 → GitHub Pages公開
↑
GitHub Actions（毎日自動実行）

## 追跡対象の選定

### 企業（必須）

識別子 企業名 色
openai OpenAI #00A67E
anthropic Anthropic #D4A017
google Google DeepMind #4285F4
meta Meta AI #0866FF
mistral Mistral AI #FF6B6B
xai xAI (Elon Musk) #1DA1F2
deepseek DeepSeek #7C3AED

### 主要人物（X追跡対象）

識別子 氏名 所属 Xアカウント
sam_altman Sam Altman OpenAI CEO @sama
dario_amodei Dario Amodei Anthropic CEO @DarioAmodei
demis_hassabis Demis Hassabis Google DeepMind CEO @demishassabis
yann_lecun Yann LeCun Meta AI Chief Scientist @ylecun
ilya_sutskever Ilya Sutskever SSI (元OpenAI) @ilyasut
geoffrey_hinton Geoffrey Hinton 独立研究者 @geoffreyhinton
elon_musk Elon Musk xAI @elonmusk
jensen_huang Jensen Huang NVIDIA CEO @jenshwang

### イベント種別

タイプ 説明
model_release モデルのリリース
announcement 企業発表（製品、API、価格等）
statement 主要人物の重要発言
paper 重要な研究論文
policy 政策・規制

## ディレクトリ構成

```
Lake/
└── llm-timeline/
    ├── data/
    │   ├── events/                    # イベントMarkdownファイル群
    │   │   ├── 2017-06-12_transformer.md
    │   │   ├── 2022-11-30_chatgpt.md
    │   │   └── ...
    │   └── config/
    │       ├── companies.yaml         # 企業定義
    │       └── persons.yaml           # 人物定義
    ├── scripts/
    │   ├── collect.py                 # メインの収集スクリプト
    │   ├── sources/
    │   │   ├── rss.py                 # RSSフィード収集
    │   │   ├── arxiv.py               # arXiv論文収集
    │   │   ├── twitter.py             # Twitter API（API取得後に有効化）
    │   │   └── news.py                # ニュースAPI収集
    │   └── build.py                   # Markdown→data.json生成
    ├── site/
    │   ├── index.html                 # メイン可視化ページ
    │   ├── js/
    │   │   └── timeline.js            # vis-timeline.js連携
    │   └── css/
    │       └── style.css
    ├── config.yaml                    # 収集設定（ソースURL、フィルタ等）
    ├── requirements.txt
    └── .github/
        └── workflows/
            └── collect-and-deploy.yml # GitHub Actions
```

## イベントMarkdownのフォーマット

---

date: 2023-03-14
type: model_release # model_release | announcement | statement | paper | policy
company: openai # companies.yamlの識別子
person: null # persons.yamlの識別子（または null）
title: "GPT-4 リリース"
description: "マルチモーダル対応。画像とテキストを統合処理..."
source_url: https://openai.com/research/gpt-4
tags: [gpt-4, multimodal, reasoning]
importance: high # high | medium | low（フィルタ用）
auto_collected: false # true=自動収集、false=手動追加

---

（任意：より詳細な説明）

## データソース

### RSSフィード（自動収集 - すぐ実装可能）

- OpenAI blog: https://openai.com/news/rss.xml
- Anthropic news: https://www.anthropic.com/rss.xml
- Google DeepMind blog: https://deepmind.google/blog/rss/
- Meta AI blog: https://ai.meta.com/blog/rss/
- Hugging Face blog: https://huggingface.co/blog/feed.xml
- Mistral blog: https://mistral.ai/news/rss

### arXiv API（自動収集）

- エンドポイント: http://export.arxiv.org/api/query
- カテゴリ: cs.CL, cs.AI, cs.LG
- キーワードフィルタ: GPT, Claude, Gemini, LLaMA, transformer等

### Twitter/X API v2（API取得後に有効化）

- エンドポイント: https://api.twitter.com/2/tweets/search/recent
- 追跡対象: 上記8名のアカウント
- フィルタ: AI/LLM関連キーワードが含まれる投稿のみ

### ニュースAPI（補完）

- NewsAPI: https://newsapi.org/v2/everything
- キーワード: "LLM", "GPT", "Claude", "Gemini", "large language model"
- ソース制限: TechCrunch, Wired, MIT Technology Review, The Verge等

## 静的サイト（可視化）

### 技術スタック

- HTML + JavaScript（フレームワーク不使用、依存最小化）
- vis-timeline.js — インタラクティブなタイムライン
- data.json — Markdownから生成されたデータ

### UI機能

1. タイムライン表示（企業ごとに色分け）
2. フィルタパネル（企業/人物/イベント種別/重要度）
3. キーワード検索
4. イベントクリックで詳細表示（ソースリンク付き）
5. ズーム機能（年単位〜月単位）

## 実装フェーズ

### Phase 1: 基盤構築

1. ディレクトリ構造の作成
2. companies.yaml, persons.yaml の作成
3. 過去の主要イベント（2017-2024）を手動でMarkdownファイルとして追加（約50件）

### Phase 2: 自動収集スクリプト

4. scripts/sources/rss.py — RSSフィード収集
5. scripts/sources/arxiv.py — arXiv API連携
6. scripts/sources/news.py — NewsAPI連携
7. scripts/sources/twitter.py — Twitter APIスタブ（後で有効化）
8. scripts/collect.py — 統合収集スクリプト
9. scripts/build.py — Markdown → data.json生成

### Phase 3: 静的サイト

10. site/index.html + site/js/timeline.js + site/css/style.css
11. vis-timeline.jsでタイムライン描画
12. フィルタ・検索機能実装

### Phase 4: 自動化

13. .github/workflows/collect-and-deploy.yml — 毎日自動収集+デプロイ
14. GitHub Pages設定

### 検証方法

1. python scripts/build.py でdata.jsonが生成されることを確認
2. python -m http.server 8000 でローカルサーバ起動
3. http://localhost:8000/site/ でタイムラインが表示されることを確認
4. python scripts/collect.py を手動実行してRSS収集が動作することを確認
5. GitHub Actionsのworkflow_dispatchで手動トリガーしてCI/CD確認

### 備考・決定事項

- 時間範囲: 2017年（Transformer論文）〜現在
- 言語: Python（スクレイパー）、HTML/JS（サイト）
- ホスティング: GitHub Pages（このリポジトリの llm-timeline/ ディレクトリ下）
- Twitter API: 取得予定。それまでは twitter.py はスタブとして実装し、APIキー設定後に自動で有効化される設計にする
- 重複排除: source_url をキーとして重複チェック
- 手動追加: 自動収集では取れない重要イベントは手動でMarkdownを追加できる設計
