# 計画サマリー

## グラフに含める対象（確定）

- 企業 7社: OpenAI, Anthropic, Google DeepMind, Meta AI, Mistral, xAI, DeepSeek

- 人物 8名（X追跡）: Sam Altman, Dario Amodei, Demis Hassabis, Yann LeCun, Ilya Sutskever, Geoffrey Hinton, Elon Musk, Jensen Huang

- 期間: 2017年（Transformer論文）〜リアルタイム

## システム全体像

RSS/arXiv/Twitter/ニュース
↓（Python自動収集、毎日）
Markdownファイル群（data/events/）
↓（build.py）
data.json
↓
静的サイト（vis-timeline.js）
↓
GitHub Pages

## 実装順序

1. Phase 1 — ディレクトリ構成 + 過去の主要イベント手動入力（~50件）
2. Phase 2 — RSS/arXiv/News自動収集スクリプト（Twitter APIは取得後に有効化）
3. Phase 3 — 静的サイト（タイムライン、フィルタ、検索）
4. Phase 4 — GitHub Actions（毎日自動収集+デプロイ）
