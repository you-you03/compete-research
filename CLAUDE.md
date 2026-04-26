# compete-research — 車買取一括査定 競合リサーチエージェント

車買取一括査定サービス（MOTA 等）の競合を AI でリサーチし、HTML ダッシュボードと Markdown レポートを生成する社内ツール。

## Critical Design Rule: Claude Code IS the Agent

**Python スクリプトは Anthropic SDK を呼ばない。** Claude Code セッション自体がエージェント。

- `research.py` → リサーチプロンプトを stdout に出力
- Claude → WebSearch / WebFetch でリサーチを実行し JSON を整理
- `save_research.py` → Claude が整理した JSON を保存

`ANTHROPIC_API_KEY` は不要。`XAI_API_KEY`（任意、Grok による X/Twitter センチメント）のみ。

---

## Repository Layout

```
compete_research/
  agents/research_agent.py  ← プロンプト生成・キャッシュ参照
  config.py                 ← Settings（キャッシュTTL・上限数）
skills/
  research.py               ← リサーチプロンプト出力 / キャッシュ参照
  save_research.py          ← 調査結果を data/cache/ に保存
  polish.py                 ← 文体整形プロンプト出力（中間ステップ）
  dashboard.py              ← HTML/Markdown 生成
data/
  companies.json            ← 競合企業マスター（手動編集）
  cache/{id}_{date}.json    ← 7日TTL リサーチキャッシュ
  research_history.json     ← 実行履歴
reports/
  dashboard.html            ← 生成ダッシュボード（open で確認）
  research/                 ← Markdown レポート履歴
```

---

## Skills & Workflow

詳細は [SKILL.md](SKILL.md) を参照。

```
research.py → [Claude: WebSearch/WebFetch] → save_research.py
  → polish.py → [Claude: 文体整形] → save_research.py
  → dashboard.py → reports/dashboard.html
```

| スキル | CLI | 出力 |
|---|---|---|
| リサーチ | `python skills/research.py --company mota` | プロンプトまたはキャッシュJSON |
| 保存 | `python skills/save_research.py --company mota --data '...'` | `data/cache/{id}_{date}.json` |
| 文体整形 | `python skills/polish.py --company mota` | 整形プロンプト（その後 save_research で上書き） |
| ダッシュボード | `python skills/dashboard.py` | `reports/dashboard.html` |

---

## 非自明な挙動

### research.py の出力が2パターンある

キャッシュ状態によって **stdout の内容が変わる**：

- **キャッシュなし（または --force）** → リサーチ用プロンプト文字列を出力  
  → Claude はこれを読んで WebSearch/WebFetch を実行し、JSON にまとめる
- **キャッシュあり（TTL 7日以内）** → 既存の JSON データをそのまま出力  
  → Claude は調査不要。そのまま save_research や dashboard に進む

stderr に `[キャッシュあり]` または `[調査開始]` が出るので判別できる。

### JSON スキーマ（リサーチ結果の構造）

```json
{
  "id": "company_id",
  "summary": "3〜5文の概要",
  "details": {
    "service": { "overview", "flow_steps", "partners", "speed", "coverage_area" },
    "business_model": { "revenue_type", "user_cost", "dealer_cost", "info_disclosure" },
    "differentiation": { "unique_features", "lp_catchcopy", "target_users", "authority_claims" },
    "scale": { "users", "assessments", "partners_trend" },
    "company": { "founded", "ceo", "parent", "employees" },
    "marketing": { "tv_cm", "seo_rankings", "ad_theme" },
    "reputation": { "positive_themes", "negative_themes" },
    "news": [{ "date": "YYYY-MM", "title", "summary" }],
    "hiring_signals": ["..."]
  },
  "data_gaps": ["取得できなかった情報"],
  "collected_at": "ISO8601"
}
```

### ダッシュボードのデータ渡し方

`dashboard.py` は `data/companies.json` のメタ情報と `data/cache/` の最新キャッシュを合体させ、`const COMPANIES_DATA = [...]` として HTML にインライン埋め込みする（外部 API 呼び出しなし）。

---

## 競合企業の追加

`data/companies.json` に追記するだけでスキルが認識する：

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

`priority`: `self`（自社） / `high` / `medium` / `low`  
`tags`: フィルタ用（`--industry` オプションで絞り込める）

---

## 調査優先度

| 優先度 | 項目 |
|---|---|
| ★★★ | サービス内容・査定フロー・提携業者数 |
| ★★★ | ビジネスモデル（お金の流れ・情報の流れ） |
| ★★★ | 差別化要因・独自機能 |
| ★★ | 会社概要・マーケティング・SEO |
| ★（将来） | 口コミ・評判（XAI_API_KEY が必要） |
