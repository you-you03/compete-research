"""
Research agent utilities.

Python側の責務:
- companies.jsonの読み込み・検索
- キャッシュの読み書き（7日TTL）
- research_history.jsonへの履歴保存
- HTMLダッシュボード生成のためのデータ取得

推論・Web検索はClaude Code本体（WebSearch/WebFetch）が実施する。
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from compete_research.config import settings


def load_companies(industry: str | None = None) -> list[dict]:
    data = json.loads(settings.companies_file.read_text())
    companies = data.get("companies", [])
    if industry:
        companies = [c for c in companies if industry in c.get("tags", [])]
    return companies


def get_company(company_id: str) -> dict | None:
    for c in load_companies():
        if c["id"] == company_id:
            return c
    return None


def get_cache_path(company_id: str, for_date: date | None = None) -> Path:
    d = for_date or date.today()
    return settings.cache_dir / f"{company_id}_{d.isoformat()}.json"


def load_cached_research(company_id: str) -> dict | None:
    """Return cached research if it exists and is within TTL."""
    ttl = settings.research_cache_ttl_days
    for days_ago in range(ttl):
        target = date.today() - timedelta(days=days_ago)
        path = get_cache_path(company_id, target)
        if path.exists():
            return json.loads(path.read_text())
    return None


def save_research(company_id: str, data: dict) -> Path:
    """Save Claude's research result to cache and append to history."""
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    data["company_id"] = company_id
    data.setdefault("collected_at", datetime.now().isoformat())
    cache_path = get_cache_path(company_id)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    _append_history(company_id, cache_path)
    return cache_path


def _append_history(company_id: str, cache_path: Path) -> None:
    history_file = settings.research_history_file
    if history_file.exists():
        history = json.loads(history_file.read_text())
    else:
        history = {"runs": []}

    history["runs"].append({
        "run_id": str(uuid.uuid4()),
        "company_id": company_id,
        "timestamp": datetime.now().isoformat(),
        "cache_file": cache_path.name,
    })
    history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def load_all_latest_research() -> list[dict]:
    """Load the most recent cached research for each company."""
    results = []
    for company in load_companies():
        cached = load_cached_research(company["id"])
        if cached:
            results.append(cached)
    return results


def build_research_prompt(company: dict) -> str:
    """Return a structured research prompt for Claude to execute via WebSearch/WebFetch."""
    name = company["name"]
    url = company.get("url", "")
    tags = ", ".join(company.get("tags", []))
    ticker = company.get("ticker", "")
    parent = company.get("parent", "")
    listed = company.get("listed", False)

    ticker_line = f"- 証券コード: {ticker}" if ticker else ""
    parent_line = f"- 親会社・グループ: {parent}" if parent else ""
    edinet_note = (
        "\n- EDINETで有価証券報告書を検索し、売上高・営業利益・セグメント別売上を確認すること"
        if listed else ""
    )

    patents = company.get("patents", [])
    patent_step = ""
    if patents:
        patent_list = "\n".join(f"- {p}" for p in patents)
        patent_step = f"""
## STEP 4: 特許内容をJ-PlatPat / Google Patentsで確認してください

以下の特許番号について、**請求項（クレーム）** を必ず取得すること。
請求項は「何が法的に保護されているか」を定義する最重要部分です。

対象特許:
{patent_list}

調査方法:
1. WebFetch: https://patents.google.com/patent/JP{patents[0].replace('特許第','').replace('号','')}/ja
   （日本語で請求項・発明の詳細な説明が読める）
2. 404の場合: WebSearch「{patents[0]} 請求項 特許 内容」
3. 取得すべき情報:
   - 請求項1〜3（独立クレーム）の全文をそのまま引用
   - 保護されている技術の核心（競合がコピーできない範囲）
   - 出願日・登録日・出願人名
"""

    return f"""以下の企業について徹底的に調査してください。
WebSearchとWebFetchを使い、**LPや公式ページからの直接引用**を中心に情報を収集してください。
推測や要約ではなく、**ページに書いてある言葉をそのまま使うこと**を最優先にしてください。

## 調査対象
- 企業名: {name}
- URL: {url}
- 業種タグ: {tags}
{ticker_line}
{parent_line}

---

## STEP 1: まず以下の検索クエリを順番に実行してください

```
1. "{name} 仕組み 査定フロー 詳しく"
2. "{name} 買取業者 加盟 掲載料 成約手数料 費用"
3. "{name} 利用者数 査定件数 実績 万人"
4. "{name} 評判 口コミ site:detail.chiebukuro.yahoo.co.jp OR site:x.com"
5. "{name} プレスリリース 新機能 2024 2025"
6. "{name} CM 広告 タレント キャンペーン"
```{edinet_note}

---

## STEP 2: 公式サイトのページを網羅的に取得してください

### 2A: まずサイト構造を把握する
以下を順番に試し、ナビゲーション・全ページ一覧を確認すること:
```
- {url}/sitemap.xml
- {url}  （トップページのナビリンクをすべて確認する）
```

### 2B: ユーザー向け「サービス仕組み」ページを取得する（最重要）
以下のURLパターンを順番に試し、**最初に存在したURLを取得**すること:
```
- {url}/how  / {url}/guide  / {url}/flow  / {url}/service
- {url}/about-service  / {url}/mechanism  / {url}/feature
```
※見つからない場合はトップページの「仕組み」「ご利用の流れ」リンクをたどること。
このページには申し込みから成約までの詳細ステップが書いてあるはず。

### 2C: 買取業者向けページを取得する（最重要）
以下のURLパターンを順番に試すこと。**業者向けLPには費用・条件が記載されている**:
```
- {url}/partner  / {url}/dealer  / {url}/for-dealer  / {url}/member
- {url}/company-registration  / {url}/dealer-lp
```
見つからない場合: WebSearch「site:{url.split('//')[-1].split('/')[0]} 加盟 業者 掲載料」で検索する。

### 2D: FAQ・料金ページを取得する
```
- {url}/faq  / {url}/price  / {url}/plan
```
FAQには「費用はかかりますか？」「業者の費用は？」など重要な情報がある。

### 2E: プレスリリース一覧
```
- {url}/press  / {url}/news  / {url}/newsroom
```

---

## STEP 3: LPの内容を直接引用しながら以下を回答してください

**重要**: 各質問への回答は「〇〇ページに『△△』と記載されている」という形式にすること。
推測・要約ではなく、ページから読み取った言葉を使うこと。

### ★★★ A. サービス仕組みの詳細（LPから直接引用）

1. **サービスの核心的な仕組み**: 仕組みページのキャッチコピー・説明文を直接引用した上で、
   ユーザー申し込み〜成約までの全ステップを番号付きで説明すること
2. **申し込みに必要な情報**: 入力フォームまたはLPに記載されている必須項目を列挙
3. **査定方法の種類と違い**: 「オンライン査定」「出張査定」それぞれの仕組みと条件
4. **提携業者数と種類**: LPに記載の社数、大手・中小の構成
5. **ユーザーが受け取る情報**: 査定額はいつ・どんな形式で通知されるか
6. **対象外・除外条件**: LPまたはFAQに書かれている申し込みできない車・条件
7. **査定後〜引渡しまで**: 成約後の具体的な流れ（LPから引用）

### ★★★ B. 買取業者向けビジネスモデル（業者LPから直接引用）

1. **業者向けLPのURL**: 見つかったURLを明記すること
2. **業者への費用構造**: 掲載料・成約手数料・月額費用など。LPに記載の金額をそのまま引用
3. **業者が受け取る情報**: 何の情報がいつ開示されるか（入札前・入札後・成約後）
4. **業者の参加条件・審査基準**: 加盟に必要な条件（LPから）
5. **業者にとってのメリット訴求**: 業者LPでどんな価値提案をしているか（直接引用）
6. **ユーザーへの費用**: FAQまたはLPから「無料」「有料」の記載を引用

### ★★★ C. 差別化要因（LPの言葉で）

1. **トップページのキャッチコピー**: 大見出し・サブヘッドを直接引用
2. **「他社と違う点」の訴求**: LPで競合比較・差別化を説明している箇所を直接引用
3. **独自機能・特許**: 機能名・特許番号・どんな技術かをLPから引用
4. **ターゲットユーザー**: LPが想定している「こんな人に向いている」の記述を引用
5. **権威付け・実績**: No.1表記・受賞・メディア掲載などをLPから引用（根拠も確認）

### ★★ D. 規模感（LPまたはプレスリリースから）
1. **利用者数・査定件数**: LPまたはプレスリリースに記載の数字を出典付きで
2. **提携業者数の推移**: 時系列で把握できる範囲で
3. **サービス開始年**: 公式情報から

### ★★ E. マーケティング
1. **SEO実測**: 「車 一括査定」「車 売りたい」「車買取 比較」を実際に検索し、
   {name}（または関連サービス）が何位に表示されるか確認すること
2. **自社メディア**: ブログ・コンテンツサイトの有無とURL
3. **TVCM**: タレント名・放映時期・キャッチコピー
4. **SNS**: X・YouTube・Instagramのアカウント名とフォロワー数（実際にページを見ること）

### ★★ F. 会社概要
1. **設立年・代表者・資本金・従業員数**（会社概要ページから）
2. **関連事業**: 買取以外に何をやっているか
3. **上場/非上場**: 非上場なら売上・財務情報は無理に探さなくてよい

### ★★ G. 最新動向
1. **直近プレスリリース**: 2024〜2025年のリリースを時系列で
2. **新機能・サービス変更**: 最近の変化

### ★ H. ユーザー評判（一次ソース優先）
1. **X(Twitter)で「{name}」を検索**: 実際のユーザー投稿の傾向（ポジ/ネガ/頻出テーマ）
2. **知恵袋・口コミ**: 主な不満・満足ポイント
{patent_step}
---

## 出力形式

調査完了後、以下のJSON形式のみで出力してください（コメント・説明文は不要）:

```json
{{
  "summary": "4〜5文の詳細サマリー。LPの言葉・数字・固有名詞を含むこと",
  "details": {{
    "service": {{
      "overview": "サービス概要（LP直接引用を含む）",
      "lp_mechanism_quote": "仕組みページからの核心的な説明文（直接引用・出典URL付き）",
      "flow_steps": ["ステップ1（LPの言葉で）", "ステップ2", "..."],
      "required_inputs": "申し込み時の必須入力項目（LPから）",
      "partners": "提携業者数・主な業者名（LPから）",
      "assessment_types": ["オンライン査定", "出張査定"],
      "eligible_vehicles": "対象・除外車両条件（FAQまたはLPから）",
      "coverage_area": "対応エリア",
      "speed": "最短査定時間（LPから引用）",
      "post_assessment_flow": "査定後の契約・引渡しの流れ（LPから）"
    }},
    "business_model": {{
      "revenue_type": "収益モデルの種類",
      "user_cost": "ユーザーへの費用（LPまたはFAQから直接引用）",
      "dealer_lp_url": "業者向けLPのURL（見つからない場合はnull）",
      "dealer_lp_quote": "業者向けLPからの直接引用（費用・条件・メリット訴求）",
      "dealer_fee_details": "業者費用の詳細（金額・課金タイミング・条件）",
      "dealer_info_flow": "業者に何の情報がいつ開示されるか",
      "secondary_revenue": "副収益（保険・ローン等）"
    }},
    "differentiation": {{
      "lp_headline": "トップページの大見出し（直接引用）",
      "lp_catchcopy": "LPのキャッチコピー・差別化訴求（直接引用）",
      "unique_features": ["独自機能1（名称・仕組みをLPから）", "機能2"],
      "target_users": "LPが描くターゲットユーザー像（引用）",
      "authority_claims": ["No.1根拠（LPから・根拠確認済み）", "受賞"]
    }},
    "scale": {{
      "users": "累計/月間利用者数（出典URL付き）",
      "assessments": "査定件数（出典付き）",
      "partners_trend": "提携業者数の推移",
      "launch_year": "サービス開始年"
    }},
    "company": {{
      "founded": "設立年",
      "ceo": "代表者名",
      "parent": "親会社・グループ",
      "employees": "従業員数",
      "revenue": "売上規模（非上場なら『非公開』でよい）",
      "related_services": "関連事業・グループサービス"
    }},
    "marketing": {{
      "tv_cm": "TVCM詳細（タレント・時期・コピー）",
      "seo_rankings": "「車 一括査定」等のビッグKWでの実測順位",
      "owned_media": "自社メディア・コンテンツサイトのURL",
      "social_followers": {{
        "twitter_x": "アカウント名とフォロワー数",
        "youtube": "チャンネル名と登録者数",
        "instagram": "アカウント名とフォロワー数"
      }},
      "ad_theme": "広告クリエイティブの主な訴求テーマ"
    }},
    "patent": {{
      "patent_number": "特許番号",
      "claims": "請求項1〜3の全文引用",
      "protected_scope": "法的保護範囲の要約（競合がコピーでき��いもの）",
      "source_url": "J-PlatPatまたはGoogle PatentsのURL"
    }},
    "reputation": {{
      "positive_themes": ["好評ポイント（一次ソース優先）"],
      "negative_themes": ["不満ポイント（一次ソース優先）"],
      "review_sources": ["実際に確認したソースURL"]
    }},
    "news": [
      {{"date": "YYYY-MM", "title": "タイトル", "summary": "概要"}}
    ]
  }},
  "scores": {{
    "threat_level": 3,
    "service_completeness": 4,
    "marketing_strength": 3,
    "scoring_rationale": "スコア根拠の一言説明"
  }},
  "data_gaps": ["取得できなかった情報（試みたURLも記載）"],
  "collected_at": "ISO8601日時"
}}
```
"""
