# compete-research スキル

車買取一括査定サービスの競合をAIエージェントでリサーチし、HTMLダッシュボードとMarkdownレポートを生成します。

## セットアップ

```bash
cd "compete-research"
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 使い方

### 1社調査（まず試す）

```
python skills/research.py --company mota
```

→ Claude が WebSearch/WebFetch でリサーチを実行し、JSON形式で出力。

### 結果の保存

Claudeが調査結果をJSONで整理したら、以下で保存：

```
python skills/save_research.py --company mota --data '{"summary": "...", "details": {...}}'
```

### 文体整形（読みやすさ向上）

リサーチ結果のテキストを、自然な日本語に整形する:

```
python skills/polish.py --company mota
```

→ Claudeが整形後JSONを出力。その後 `save_research.py` で上書き保存する。

### ダッシュボード生成

```
python skills/dashboard.py
open reports/dashboard.html
```

### その他のオプション

```bash
# 企業一覧を確認
python skills/research.py --list

# 全社一括調査
python skills/research.py --all

# キャッシュを無視して再調査
python skills/research.py --company navicle --force

# 全社まとめて文体整形
python skills/polish.py --all

# Markdownレポートのみ生成
python skills/dashboard.py --no-html
```

## ファイル構成

```
compete-research/
├── data/
│   ├── companies.json          # 競合企業マスター（編集可）
│   ├── research_history.json   # 実行履歴（自動生成）
│   └── cache/                  # 調査結果キャッシュ（7日TTL）
├── skills/
│   ├── research.py             # 調査プロンプト出力 / キャッシュ参照
│   ├── save_research.py        # 調査結果の保存
│   ├── polish.py               # 文体整形プロンプト出力（research → dashboard の中間）
│   └── dashboard.py            # HTML/Markdown生成
└── reports/
    ├── dashboard.html          # メインダッシュボード
    └── research/               # Markdownレポート履歴
```

## 標準ワークフロー

```
research.py → [Claude リサーチ] → save_research.py
  → polish.py → [Claude 文体整形] → save_research.py
  → dashboard.py → dashboard.html
```

## 競合追加方法

`data/companies.json` に追記：

```json
{
  "id": "new_company",
  "name": "企業名",
  "url": "https://example.com",
  "parent": "親会社名",
  "listed": false,
  "priority": "high",
  "tags": ["car_appraisal"],
  "note": "メモ"
}
```

## 調査項目（優先度順）

| 優先度 | 項目 |
|-------|------|
| ★★★ | サービス内容・査定フロー・提携業者数 |
| ★★★ | ビジネスモデル（お金の流れ・情報の流れ） |
| ★★★ | 差別化要因・独自機能 |
| ★★ | 会社概要・財務情報 |
| ★★ | マーケティング・SEO |
| ★（将来）| 口コミ・評判（Grok API） |
