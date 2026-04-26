# 横断比較ビュー — 設計書

> このドキュメントは `compete_research/templates/compare.html` の実装指示書です。  
> Claude Code が直接このドキュメントを読み、コードを実装することを想定しています。

---

## 目的

現在の `dashboard.html` は「企業軸」（会社ごとに詳細を見る）。  
この新ページは「観点軸」（テーマごとに全社を横断比較する）。  
例えば「マーケティング戦略を全社一覧で見たい」「脅威度スコアで並べたい」といった用途に答える。

---

## 実装スコープ

| 対象 | 変更内容 |
|---|---|
| `compete_research/templates/compare.html` | 新規作成（本書の主題） |
| `skills/dashboard.py` | `compare.html` も同時生成するよう `_generate_compare_html()` 関数を追加 |
| `compete_research/templates/dashboard.html` | サイドバーにリンクを1行追加するだけ（詳細は後述） |

---

## データソース

`dashboard.py` が既に構築する `companies_list` をそのまま利用する。  
テンプレート内に `const COMPANIES_DATA = __COMPANIES_JSON__;` を埋め込む（`dashboard.html` と同じ置換方式）。  
`__TODAY__` も同様に置換する。

各企業オブジェクトの構造（抜粋、参照用）：

```
{
  id, name, url, priority,
  summary,
  scores: { threat_level, service_completeness, marketing_strength, scoring_rationale },
  data_gaps: [...],
  collected_at,
  details: {
    service:         { overview, flow_steps[], speed, partners, assessment_types[], coverage_area },
    business_model:  { revenue_type, user_cost, dealer_fee_details, dealer_info_flow },
    differentiation: { unique_features[], lp_headline, lp_catchcopy, target_users, authority_claims[] },
    scale:           { users, assessments, partners_trend },
    marketing:       { tv_cm, seo_rankings, owned_media, ad_theme },
    reputation:      { positive_themes[], negative_themes[] },
    news:            [{ date, title, summary }],
    hiring_signals:  [...],
    ir_analysis?:    { overview, revenue_trend[], midterm_plan_fy2025_2028, stability_assessment },
    patent?:         { patent_number, title, registered, summary }
  }
}
```

---

## デザイン言語（既存 dashboard.html から継承すること）

### CSS変数（全てコピー）
`:root` のカラー変数はすべて `dashboard.html` と同じ値を使う：
- `--bg: #f5f4f0` / `--bg-card: #fbfaf6` / `--ink: #14171c` etc.
- `--c-scale: #c2410c` / `--c-biz: #b91c1c` / `--c-diff: #047857` / `--c-mkt: #6d28d9` etc.

### タイポグラフィ
- フォント：`-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif`
- Eyebrow（セクション小見出し）：`font-size: 11-12px; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase;`
- 企業名：`font-weight: 800`

### コンポーネント
- `.tile`（`border-radius: 18px; padding: 22px 24px; background: var(--bg-card); border: 1px solid var(--rule);`）を使ってよい
- `.tile.accent::before`（左端 3px カラーストライプ）も使ってよい
- `mark` タグ（`background: rgba(14,165,233,0.13); border-radius: 3px; padding: 0 3px;`）で数字ハイライト
- アニメーション：`@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }`

---

## ページ構造

```
<body>
  <aside class="sidebar">   ← dashboard.html と同じ見た目
  <main class="main">
    <header class="topbar">
    <section class="compare-section" id="s-scores">    ← 観点ブロック × N
    <section class="compare-section" id="s-service">
    <section class="compare-section" id="s-biz">
    <section class="compare-section" id="s-diff">
    <section class="compare-section" id="s-marketing">
    <section class="compare-section" id="s-news">
```

---

## サイドバー仕様

`dashboard.html` のサイドバーとは役割が変わる。  
企業リストではなく、**観点セクションへのアンカーナビ**にする。

```
[EYEBROW] COMPETE RESEARCH
[TITLE]   横断比較ビュー

[SECTION LABEL] 観点ナビ

• スコア比較        → #s-scores
• サービスフロー比較 → #s-service
• ビジネスモデル比較 → #s-biz
• 差別化要因比較    → #s-diff
• マーケティング比較 → #s-marketing
• IR分析比較        → #s-ir
• ニュース横断      → #s-news

[FOOTER]
← 企業別ビューへ    → dashboard.html へのリンク
Generated: __TODAY__
```

### サイドバーのナビアイテム CSS
```css
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 10px;
  cursor: pointer; font-size: 15px; font-weight: 500;
  color: var(--ink-2); text-decoration: none;
  transition: background 0.14s;
}
.nav-item:hover { background: rgba(0,0,0,0.04); color: var(--ink); }
.nav-item.active { background: var(--bg); font-weight: 700; color: var(--ink); }
.nav-dot {
  width: 4px; height: 20px; border-radius: 2px;
  background: var(--rule-strong); flex-shrink: 0;
}
/* アクティブセクションに応じて .nav-dot を染める — JS で制御 */
```

スクロール連動でアクティブセクションの `.nav-dot` を対応カラーに染める（IntersectionObserver 使用）。

### dashboard.html 側の変更（最小限）
サイドバーの `.sb-footer` 直前に以下1行を追加：
```html
<a href="compare.html" class="sb-compare-link">横断比較ビュー →</a>
```
```css
.sb-compare-link {
  display: block; margin: 0 12px 16px; padding: 10px 14px;
  background: var(--bg); border: 1px solid var(--rule); border-radius: 10px;
  font-size: 13px; font-weight: 700; color: var(--ink-2);
  text-decoration: none; text-align: center;
  transition: background 0.14s;
}
.sb-compare-link:hover { background: #ece9e0; color: var(--ink); }
```

---

## 観点ブロック共通レイアウト

```
<section class="compare-section" id="s-{key}">
  <div class="cs-header">
    <span class="cs-eyebrow">{SECTION_NUMBER} {LABEL}</span>
    <h2 class="cs-title">{SECTION_TITLE_JA}</h2>
    <p class="cs-desc">{何を比較しているかの1行説明}</p>
  </div>
  <div class="cs-body">
    {各セクション固有のコンテンツ}
  </div>
</section>
```

```css
.compare-section {
  margin-bottom: 64px;
  scroll-margin-top: 24px;
}
.cs-header {
  display: flex; flex-direction: column; gap: 6px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--rule);
}
.cs-eyebrow {
  font-size: 11px; font-weight: 800; letter-spacing: 0.22em;
  text-transform: uppercase; color: var(--ink-3);
}
.cs-title {
  font-size: 26px; font-weight: 800;
  letter-spacing: -0.01em; color: var(--ink);
}
.cs-desc { font-size: 14px; color: var(--ink-3); }
```

---

## 各観点ブロック仕様

### 01. スコア比較（`#s-scores`）

**目的**: `scores.threat_level / service_completeness / marketing_strength` を全社横並びで比較。  
**レイアウト**: スコアマトリクステーブル。

#### ビジュアル
- テーブル：行 = スコア項目（3行）、列 = 企業（データある分だけ）
- 企業列は `priority` 順（self → high → medium → low）
- 自社（`priority: "self"`）列のヘッダーは `--c-scale` でハイライト
- スコア値（1〜5）は **大きいフォント（32px, weight 800）** で表示
- スコアに応じた塗り（`scoreColor` 関数で生成）:
  - 5 → `var(--c-diff)` (emerald)
  - 4 → `#16a34a`
  - 3 → `#ca8a04`
  - 2 → `var(--c-biz)` (red)
  - 1 → `#991b1b`
  - null/undefinedの場合 → `--ink-4` で `—` 表示
- 各スコア行の先頭セルは **行ラベル**（`脅威度`, `サービス完成度`, `マーケ強度`）

#### 行ラベルの定義
```js
const SCORE_ROWS = [
  { key: 'threat_level',          label: '脅威度',        unit: '/5', accent: '--c-biz' },
  { key: 'service_completeness',  label: 'サービス完成度', unit: '/5', accent: '--c-service' },
  { key: 'marketing_strength',    label: 'マーケ強度',     unit: '/5', accent: '--c-mkt' },
];
```

#### スコア下の `scoring_rationale` 展開
- テーブル下に「各社の評価コメント」をアコーディオン形式で表示
- 企業名をクリックするとそのコメントが展開する（CSS `details/summary` タグで実装）

```html
<details class="score-rationale">
  <summary>{企業名}</summary>
  <p>{scoring_rationale}</p>
</details>
```

---

### 02. サービスフロー比較（`#s-service`）

**目的**: 査定の仕組み・ステップ数・スピード・業者数を比較する。

#### レイアウト
企業ごとのカード（`.service-card`）を横並び（CSS Grid `repeat(auto-fill, minmax(280px, 1fr))`）。

#### 各社カード内コンテンツ

```
[企業名 + priority badge]
[メタ情報行] ステップ数: N | スピード: 翌日18時 | 業者: 1500社+
[フロー概要] overview の先頭150字
[ステップリスト] flow_steps の 各項目を箇条書き（最大5件、超える場合は省略）
```

- ステップリストの各項目は `①②③…` プレフィックスを `<span class="flow-num">` でスタイリング
- 業者数（`partners` フィールドの数字部分を正規表現で抽出）は大きく表示（28px）
- スピード値（`speed` フィールド）は `<mark>` タグでハイライト

```css
.service-card {
  background: var(--bg-card);
  border: 1px solid var(--rule);
  border-radius: 18px;
  padding: 22px 24px;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.service-card-name { font-size: 17px; font-weight: 800; }
.service-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: 12px; color: var(--ink-3);
  border-bottom: 1px solid var(--rule); padding-bottom: 12px;
}
.service-meta strong { color: var(--ink); font-size: 18px; font-weight: 800; }
.flow-steps { list-style: none; display: flex; flex-direction: column; gap: 4px; }
.flow-step { font-size: 13px; line-height: 1.5; color: var(--ink-2); }
.flow-num { font-weight: 800; color: var(--c-service); margin-right: 4px; }
```

---

### 03. ビジネスモデル比較（`#s-biz`）

**目的**: 収益タイプ・ユーザー費用・業者側コスト構造を比較する。

#### レイアウト
2カラムの分割テーブル構造：

```
| 企業名 | 収益タイプ | ユーザー費用 | 業者側コスト | 情報フロー |
```

- テーブル形式（`<table>`）で実装
- 企業列は priority 順に並べる
- `revenue_type` は色付きバッジとして表示:
  - `"成果報酬"` → `--c-diff` (green)
  - `"広告費"` / `"CPA"` → `--c-mkt` (violet)
  - `"SaaS"` / `"月額"` → `--c-service` (blue)
  - それ以外 → `--ink-3`
- 各セルの値は `highlightSummary()` を通してハイライトする
- データが null / 空 の場合は `—` 表示

```css
.biz-table { width: 100%; border-collapse: collapse; }
.biz-table th {
  text-align: left; font-size: 11px; font-weight: 800;
  letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-3); padding: 8px 14px;
  border-bottom: 2px solid var(--rule-strong);
}
.biz-table td {
  font-size: 13px; line-height: 1.5; vertical-align: top;
  padding: 14px; border-bottom: 1px solid var(--rule);
}
.biz-table tr:hover td { background: rgba(0,0,0,0.015); }
.biz-badge {
  display: inline-block; font-size: 11px; font-weight: 800;
  padding: 2px 8px; border-radius: 4px; border: 1px solid currentColor;
  margin-bottom: 4px;
}
```

---

### 04. 差別化要因比較（`#s-diff`）

**目的**: 各社の `unique_features[]` を横並びで比較し、どの会社がどの強みを持つかを把握する。

#### レイアウト
企業ごとのカード（`repeat(auto-fill, minmax(260px, 1fr))`）。

#### 各社カード内コンテンツ
```
[企業名]
[LPキャッチコピー] lp_headline または lp_catchcopy（引用スタイル）
[差別化フィーチャー] unique_features[] を Feature チップとして表示
[ターゲット] target_users
```

- `unique_features` の各項目は、最初の句点（。）または20字で truncate してチップ表示
- `lp_headline` は `font-style: italic; color: var(--ink-2)` の引用スタイル

```css
.diff-card {
  background: var(--bg-card);
  border: 1px solid var(--rule);
  border-radius: 18px;
  padding: 22px 24px;
  position: relative;
}
.diff-card::before {   /* accent strip — --c-diff 固定 */
  content: ''; position: absolute;
  left: 0; top: 22px; bottom: 22px;
  width: 3px; border-radius: 0 3px 3px 0;
  background: var(--c-diff);
}
.diff-quote {
  font-size: 13px; font-style: italic; color: var(--ink-2);
  line-height: 1.6; margin-bottom: 14px;
  border-left: 2px solid var(--rule-strong); padding-left: 12px;
}
.feature-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.feature-chip {
  font-size: 12px; padding: 4px 10px; border-radius: 6px;
  background: rgba(4,120,87,0.08); color: var(--c-diff);
  border: 1px solid rgba(4,120,87,0.2); font-weight: 600;
  max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.diff-target { font-size: 12px; color: var(--ink-3); }
.diff-target strong { color: var(--ink-2); font-weight: 700; }
```

---

### 05. マーケティング戦略比較（`#s-marketing`）

**目的**: TV CM・SEO・オウンドメディア・広告テーマを全社横断で比較する。

#### レイアウト
2段構成：

**上段: TV CM 有無バッジ行**
全社を横に並べ、`tv_cm` フィールドが null/空かどうかで「CMあり ✓」「CM なし」バッジを表示。
- CMあり → `background: rgba(109,40,217,0.1); color: var(--c-mkt); border: 1px solid ...` (violet)
- CMなし → `background: var(--bg); color: var(--ink-4); border: 1px solid var(--rule)`

**下段: マーケ詳細カード**
企業ごとのカード（`repeat(auto-fill, minmax(280px, 1fr))`）。

各カード内：
```
[企業名]
[メタ行] CMあり/なし バッジ | SEO あり/なし バッジ | オウンドメディア 有無
[広告テーマ] ad_theme の先頭100字
[SEO概要]   seo_rankings の先頭100字
```

```css
.mkt-badge-row {
  display: flex; flex-wrap: wrap; gap: 12px;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--rule);
}
.mkt-badge-item { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.mkt-badge-label { font-size: 11px; color: var(--ink-3); font-weight: 700; }
.mkt-badge-pill {
  font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 6px;
}

.mkt-card {
  background: var(--bg-card); border: 1px solid var(--rule);
  border-radius: 18px; padding: 22px 24px;
}
.mkt-card::before {
  content: ''; position: absolute;
  left: 0; top: 22px; bottom: 22px;
  width: 3px; border-radius: 0 3px 3px 0;
  background: var(--c-mkt);
}
.mkt-row { font-size: 13px; line-height: 1.6; color: var(--ink-2); margin-bottom: 10px; }
.mkt-row-label { font-size: 11px; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase; color: var(--ink-3); margin-bottom: 3px; }
```

---

### 06. IR分析比較（`#s-ir`）

**目的**: 上場企業・IR開示データを持つ会社の財務安定性・成長性を横断比較する。  
データが存在する会社だけコンテンツカードを表示し、未調査・非上場の会社は「非上場 / データなし」プレースホルダーを出す。

#### データ参照パス
`details.ir_analysis` が存在する場合にのみコンテンツを描画する。

```js
// IRデータを持つ会社とそれ以外を分類
const withIR    = companies.filter(c => c.details?.ir_analysis);
const withoutIR = companies.filter(c => !c.details?.ir_analysis);
```

現時点では ナビクル（エイチームHD）のみが `ir_analysis` を持つ想定。  
将来的にリクルート・LINEヤフー・楽天のキャッシュが追加されると複数社比較になる。

#### レイアウト: 3段構成

**上段: 安定性ヒートマップ（全社サマリー行）**

全社を横に並べた1行テーブル。IRデータがある会社は各セルに値を、ない会社は「—」を表示。

| 企業名 | 上場 | 親会社 | 売上規模 | 営業利益トレンド | 中期計画 |
|---|---|---|---|---|---|
| ナビクル | TSE Prime（3662） | エイチームHD | 34億目標 | 縮小→回復局面 | 2025-2028 |
| MOTA | 非上場 | — | — | — | — |
| … | 非上場 | — | — | — | — |

- 「上場」セルは `listed: true` の company から `parent` と `ticker` で生成する（`companies.json` のメタ情報を使う）
- ただし `ir_analysis.overview` が存在する場合はその記述を優先する
- 「営業利益トレンド」は `revenue_trend` 配列の最新2期を比較して ↑ / ↓ / → の矢印バッジで表示

```css
.ir-summary-table { width: 100%; border-collapse: collapse; margin-bottom: 28px; }
.ir-summary-table th {
  font-size: 11px; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-3); padding: 8px 14px; border-bottom: 2px solid var(--rule-strong);
  text-align: left;
}
.ir-summary-table td {
  font-size: 13px; padding: 12px 14px; border-bottom: 1px solid var(--rule);
  vertical-align: middle;
}
.ir-summary-table tr:hover td { background: rgba(0,0,0,0.015); }
.ir-trend-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 800; padding: 3px 9px; border-radius: 5px;
}
.ir-trend-badge.up   { background: rgba(4,120,87,0.1);  color: var(--c-diff); }
.ir-trend-badge.down { background: rgba(185,28,28,0.1); color: var(--c-biz);  }
.ir-trend-badge.flat { background: rgba(0,0,0,0.05);    color: var(--ink-3);  }
```

**中段: IR詳細カード（データがある会社のみ）**

IRデータを持つ各社について、全幅カードまたは `repeat(auto-fill, minmax(360px, 1fr))` のグリッドで表示。

各カードの内部構造:

```
[企業名 + 上場市場バッジ]          ← アクセント色 --c-ir
[概要テキスト] ir_analysis.overview（2〜3文）

[左ペイン: 売上推移]               [右ペイン: 中期計画目標]
  revenue_trend[] を               midterm_plan_fy2025_2028 の
  ミニ棒グラフテーブルで表示          KVリストで表示

[強み / リスク 2カラム]
  stability_assessment.strengths[]  → 緑チップ
  stability_assessment.risks[]      → 赤チップ

[成長見通し] growth_outlook（1文）
```

```css
.ir-detail-card {
  background: var(--bg-card); border: 1px solid var(--rule);
  border-radius: 18px; padding: 28px 30px; position: relative;
}
.ir-detail-card::before {
  content: ''; position: absolute;
  left: 0; top: 28px; bottom: 28px;
  width: 3px; border-radius: 0 3px 3px 0;
  background: var(--c-ir);  /* deep navy */
}
.ir-card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.ir-card-name { font-size: 20px; font-weight: 800; }
.ir-market-badge {
  font-size: 11px; font-weight: 800; padding: 3px 9px; border-radius: 5px;
  background: rgba(12,74,110,0.1); color: var(--c-ir); border: 1px solid rgba(12,74,110,0.2);
}
.ir-card-overview {
  font-size: 14px; line-height: 1.7; color: var(--ink-2); margin-bottom: 22px;
}
.ir-card-body {
  display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 22px;
}
/* 売上推移ミニグラフ */
.ir-mini-chart { display: flex; flex-direction: column; gap: 6px; }
.ir-mini-chart-title {
  font-size: 11px; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-3); margin-bottom: 8px;
}
.ir-mini-row { display: grid; grid-template-columns: 64px 1fr 56px; gap: 8px; align-items: center; }
.ir-mini-period { font-size: 11px; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.ir-mini-bar-wrap { height: 6px; background: var(--rule); border-radius: 3px; overflow: hidden; }
.ir-mini-bar { height: 100%; border-radius: 3px; background: var(--c-ir); transition: width 0.4s; }
.ir-mini-val { font-size: 12px; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }
/* 中期計画 KV */
.ir-plan-title {
  font-size: 11px; font-weight: 800; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--ink-3); margin-bottom: 8px;
}
.ir-plan-kv { display: flex; flex-direction: column; gap: 8px; }
.ir-plan-row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.ir-plan-label { font-size: 12px; color: var(--ink-3); }
.ir-plan-value { font-size: 18px; font-weight: 800; color: var(--ink); font-variant-numeric: tabular-nums; }
/* 強み/リスク */
.ir-assess { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.ir-assess-col-title {
  font-size: 11px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
  margin-bottom: 8px;
}
.ir-assess-col-title.pos { color: var(--c-diff); }
.ir-assess-col-title.neg { color: var(--c-biz); }
.ir-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.ir-chip {
  font-size: 12px; padding: 4px 10px; border-radius: 6px; font-weight: 600;
  max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ir-chip.pos { background: rgba(4,120,87,0.08);  color: var(--c-diff); border: 1px solid rgba(4,120,87,0.2); }
.ir-chip.neg { background: rgba(185,28,28,0.08); color: var(--c-biz);  border: 1px solid rgba(185,28,28,0.2); }
/* 成長見通し */
.ir-outlook {
  font-size: 13px; line-height: 1.6; color: var(--ink-2);
  border-left: 2px solid var(--c-ir); padding-left: 12px;
  font-style: italic;
}
```

**下段: 非上場・データなし企業の一覧**

IRデータがない会社は小さいプレースホルダー行でまとめる。

```
[企業名] 非上場 / IR調査データなし
```

```css
.ir-placeholder-list { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.ir-placeholder-item {
  font-size: 13px; color: var(--ink-3); padding: 8px 16px;
  border: 1px dashed var(--rule-strong); border-radius: 8px;
}
```

#### JS 実装例

```js
function irTrendBadge(trend) {
  if (!Array.isArray(trend) || trend.length < 2) return '';
  const last  = trend[trend.length - 1]?.op_profit_bn ?? 0;
  const prev  = trend[trend.length - 2]?.op_profit_bn ?? 0;
  if (last > prev) return '<span class="ir-trend-badge up">↑ 改善</span>';
  if (last < prev) return '<span class="ir-trend-badge down">↓ 悪化</span>';
  return '<span class="ir-trend-badge flat">→ 横ばい</span>';
}

function buildIrSection(companies) {
  const withIR    = companies.filter(c => c.details?.ir_analysis);
  const withoutIR = companies.filter(c => !c.details?.ir_analysis);

  const cards = withIR.map(c => {
    const ir    = c.details.ir_analysis;
    const trend = ir.revenue_trend || [];
    const mp    = ir.midterm_plan_fy2025_2028 || {};
    const sa    = ir.stability_assessment || {};
    const maxRev = Math.max(...trend.map(t => t.revenue_bn || 0), 1);

    const miniRows = trend.map(t => {
      const pct = Math.round(((t.revenue_bn || 0) / maxRev) * 100);
      return `<div class="ir-mini-row">
        <span class="ir-mini-period">${escapeHtml(t.period)}</span>
        <div class="ir-mini-bar-wrap"><div class="ir-mini-bar" style="width:${pct}%"></div></div>
        <span class="ir-mini-val">${t.revenue_bn}億</span>
      </div>`;
    }).join('');

    const planRows = [
      ['売上目標',   mp.revenue_target_bn   != null ? `${mp.revenue_target_bn}億円`   : null],
      ['売上CAGR',   mp.revenue_cagr_pct    != null ? `+${mp.revenue_cagr_pct}%/年`  : null],
      ['営業利益目標', mp.op_profit_target_bn != null ? `${mp.op_profit_target_bn}億円`: null],
      ['EBITDA目標', mp.ebitda_target_bn    != null ? `${mp.ebitda_target_bn}億円`    : null],
    ].filter(r => r[1] != null)
     .map(([l, v]) => `<div class="ir-plan-row">
       <span class="ir-plan-label">${escapeHtml(l)}</span>
       <span class="ir-plan-value">${escapeHtml(v)}</span>
     </div>`).join('');

    const shortName = c.name.replace(/（.*?）/, '');
    return `<!-- ir card for ${shortName} -->
    <div class="ir-detail-card">
      <div class="ir-card-head">
        <span class="ir-card-name">${escapeHtml(shortName)}</span>
        ${ir.market_badge ? `<span class="ir-market-badge">${escapeHtml(ir.market_badge)}</span>` : ''}
        ${irTrendBadge(trend)}
      </div>
      <p class="ir-card-overview">${escapeHtml(ir.overview || '')}</p>
      <div class="ir-card-body">
        <div class="ir-mini-chart">
          <div class="ir-mini-chart-title">売上推移</div>
          ${miniRows}
        </div>
        <div>
          <div class="ir-plan-title">中期計画目標</div>
          <div class="ir-plan-kv">${planRows || dash}</div>
        </div>
      </div>
      <div class="ir-assess">
        <div>
          <div class="ir-assess-col-title pos">強み・安定要因</div>
          <div class="ir-chips">${(sa.strengths || []).map(s => `<span class="ir-chip pos" title="${escapeHtml(s)}">${escapeHtml(s.substring(0, 18))}${s.length > 18 ? '…' : ''}</span>`).join('')}</div>
        </div>
        <div>
          <div class="ir-assess-col-title neg">リスク要因</div>
          <div class="ir-chips">${(sa.risks || []).map(r => `<span class="ir-chip neg" title="${escapeHtml(r)}">${escapeHtml(r.substring(0, 18))}${r.length > 18 ? '…' : ''}</span>`).join('')}</div>
        </div>
      </div>
      ${sa.growth_outlook ? `<div class="ir-outlook">${escapeHtml(sa.growth_outlook)}</div>` : ''}
    </div>`;
  }).join('');

  const placeholders = withoutIR.map(c => {
    const shortName = c.name.replace(/（.*?）/, '');
    return `<span class="ir-placeholder-item">${escapeHtml(shortName)} — 非上場 / データなし</span>`;
  }).join('');

  return `
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px;margin-bottom:24px;">
      ${cards}
    </div>
    <div class="ir-placeholder-list">${placeholders}</div>`;
}
```

#### `ir_analysis` に存在すると期待するフィールド（参照用）

```js
ir_analysis: {
  overview:                 string,          // 会社・事業の概要文
  market_badge:             string | null,   // 例: "TSE Prime（3662）"（任意）
  revenue_trend: [{
    period:       string,   // "FY2024/07" 形式
    revenue_bn:   number,   // 売上高（億円）
    op_profit_bn: number,   // 営業利益（億円）
  }],
  midterm_plan_fy2025_2028: {
    revenue_target_bn:    number | null,
    revenue_cagr_pct:     number | null,
    op_profit_target_bn:  number | null,
    op_profit_cagr_pct:   number | null,
    ebitda_target_bn:     number | null,
    ma_investment_target: string | null,
    shareholder_return:   string | null,
  },
  stability_assessment: {
    strengths:      string[],
    risks:          string[],
    growth_outlook: string,
  }
}
```

---

### 07. ニュース横断タイムライン（`#s-news`）

**目的**: 全社の最新ニュースを時系列で並べて、業界全体のトレンドを把握する。

#### レイアウト
- 全社の `details.news[]` を collect して `date` 降順でソート
- 単一列のタイムライン

#### 各アイテム
```
[date badge] [企業バッジ] タイトル
             サマリーテキスト（先頭150字）
```

- date が `YYYY-MM` 形式 → `"YYYY年MM月"` に変換して表示
- 企業バッジは priority カラーで塗る（self→`--c-scale`, high→`--c-biz`, medium→`--c-service`, low→`--ink-4`）
- データなし（`news` 配列が空）の企業は「調査データなし」としてフォールバック表示

```css
.news-timeline { display: flex; flex-direction: column; gap: 0; }
.news-item {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 16px; align-items: start;
  padding: 16px 0;
  border-bottom: 1px solid var(--rule);
}
.news-date {
  font-size: 12px; font-weight: 700; color: var(--ink-3);
  font-variant-numeric: tabular-nums; padding-top: 2px;
}
.news-content { display: flex; flex-direction: column; gap: 6px; }
.news-co-badge {
  display: inline-block; font-size: 10px; font-weight: 800;
  padding: 2px 8px; border-radius: 4px; border: 1px solid currentColor;
  width: fit-content; letter-spacing: 0.06em;
}
.news-title { font-size: 15px; font-weight: 700; color: var(--ink); line-height: 1.45; }
.news-summary { font-size: 13px; color: var(--ink-2); line-height: 1.6; }
```

#### JS 実装例
```js
function buildNewsTimeline(companies) {
  const items = [];
  companies.forEach(c => {
    const news = c.details?.news || [];
    const shortName = c.name.replace(/（.*?）/, '');
    news.forEach(n => {
      items.push({ date: n.date || '', title: n.title || '', summary: n.summary || '', co: c, shortName });
    });
  });
  // 降順ソート
  items.sort((a, b) => (b.date > a.date ? 1 : b.date < a.date ? -1 : 0));
  return items;
}
```

---

## トップバー仕様

```html
<div class="topbar">
  <span class="crumb">横断比較ビュー</span>
  <span class="timestamp">Generated: __TODAY__ ・ {N}社のデータ</span>
</div>
```

`{N}` は `COMPANIES_DATA.length` で動的に表示。

---

## dashboard.py の変更

### 追加する関数

```python
def _generate_compare_html(research_data: list[dict], companies: dict) -> None:
    today = date.today().isoformat()
    html = _build_compare_html(research_data, companies, today)
    out = settings.reports_dir / "compare.html"
    out.write_text(html, encoding="utf-8")
    typer.echo(f"Compare HTML生成: {out}")

def _build_compare_html(data: list[dict], companies: dict, today: str) -> str:
    companies_list = _build_companies_data(data, companies)
    companies_json = json.dumps(companies_list, ensure_ascii=False, indent=2)
    template = (TEMPLATES_DIR / "compare.html").read_text(encoding="utf-8")
    return (
        template
        .replace("__COMPANIES_JSON__", companies_json)
        .replace("__TODAY__", today)
    )
```

### `main()` への追加

```python
if html:
    _generate_html(research_data, companies)
    _generate_compare_html(research_data, companies)   # ← 追加
```

`--html/--no-html` フラグで両方まとめて制御する（compare だけ独立フラグは不要）。

---

## 実装上の注意点

### フォールバック
- `details` のフィールドは company によって欠損する。常に `?.` オプショナルチェーン or 空配列デフォルトで参照すること。
- スコアが `null` や `undefined` のケースは `—` 表示。スコアが `0` の場合も `—` とする（未評価扱い）。

### ソート順
- 全セクションで企業の表示順は `priority` 順（self → high → medium → low）に統一する。
- JS 側で `COMPANIES_DATA` を並び替える際は元の配列を変更せず、`.slice().sort()` でコピーを作ること。

### CSS の重複回避
- `compare.html` は独立した HTML ファイル。`dashboard.html` の CSS を `<link>` で参照するのではなく、必要な変数・ユーティリティを `<style>` 内に自己完結させること（CDN も使用しない）。
- `.tile`, `.tile.accent::before`, `mark`, `.empty-cell` などの共通クラスは同じ定義をコピーしてよい。

### アニメーション
- 各観点セクションは `fadeUp` アニメーション付きで登場させる（`animation-fill-mode: both; animation-delay` はセクション番号 × 0.06s）。

### スクロール連動サイドバー
```js
const sections = document.querySelectorAll('.compare-section');
const navItems = document.querySelectorAll('.nav-item');
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      navItems.forEach(n => n.classList.toggle('active', n.dataset.target === id));
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => observer.observe(s));
```

---

## ファイル配置まとめ

```
compete_research/templates/
  dashboard.html       ← 既存（サイドバーにリンク1行追加のみ）
  compare.html         ← 新規作成（本書の対象）
reports/
  dashboard.html       ← 生成済み
  compare.html         ← 新規生成
```

---

## チェックリスト（実装完了の確認）

- [ ] `compare.html` テンプレート作成
- [ ] `:root` CSS変数が `dashboard.html` と一致している
- [ ] サイドバーに6観点のアンカーナビが表示される
- [ ] サイドバーに「← 企業別ビューへ」リンクがある
- [ ] 各観点セクションが正しく描画される（01〜07）
- [ ] スコアが null のとき `—` が表示される（スコアなし企業がある場合）
- [ ] IRセクション: `ir_analysis` がある会社はカード表示、ない会社はプレースホルダー表示
- [ ] IRセクション: 売上推移ミニバーグラフが正しく比率計算されている
- [ ] IRセクション: 中期計画が null フィールドをスキップして表示される
- [ ] ニュースタイムラインが降順ソートされている
- [ ] `dashboard.py` が `compare.html` を同時生成する
- [ ] `dashboard.html` サイドバーに「横断比較ビュー」リンクが追加されている
- [ ] `python3 skills/dashboard.py` で両方が生成されてエラーが出ない
