"""
Usage (Claude Code skill entry point):
  python skills/polish.py --company mota
  python skills/polish.py --all

Reads cached research JSON and outputs a polish prompt for Claude to rewrite
text fields into natural, readable Japanese. After Claude outputs the polished
JSON, run save_research.py to overwrite the cache with the polished version.
"""

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from compete_research.agents.research_agent import (
    get_company,
    load_all_latest_research,
    load_cached_research,
    load_companies,
)

app = typer.Typer(add_completion=False)


@app.command()
def main(
    company: str = typer.Option("", "--company", "-c", help="Company ID to polish"),
    all_companies: bool = typer.Option(False, "--all", "-a", help="Polish all cached companies"),
) -> None:
    if all_companies:
        companies = load_companies()
        for c in companies:
            _print_polish_for(c["id"])
        return

    if company:
        _print_polish_for(company)
        return

    typer.echo("Error: --company または --all が必要です", err=True)
    raise typer.Exit(1)


def _print_polish_for(company_id: str) -> None:
    company = get_company(company_id)
    if not company:
        typer.echo(f"Error: '{company_id}' が companies.json に見つかりません", err=True)
        raise typer.Exit(1)

    cached = load_cached_research(company_id)
    if not cached:
        typer.echo(f"Error: '{company_id}' のキャッシュが見つかりません。先に research.py を実行してください。", err=True)
        raise typer.Exit(1)

    typer.echo(f"\n[文体整形] {company['name']}", err=True)
    print(build_polish_prompt(company, cached))


def build_polish_prompt(company: dict, research_data: dict) -> str:
    name = company["name"]
    raw_json = json.dumps(research_data, ensure_ascii=False, indent=2)

    return f"""以下は「{name}」の競合リサーチデータ（JSON）です。
このJSONの**テキストフィールドを、読み手に伝わりやすい自然な日本語に整形**してください。

## 整形の方針

**やること**:
- 助詞（が・を・に・は・で・から など）を補い、文として成立させる
- 箇条書きの断片（「査定後 引き渡し 完了」など）を文に整える
- LP直接引用の硬い表現を、内容を損なわず読みやすく言い換える
- 専門用語はそのまま残しつつ、前後の文脈を補って意味が伝わるようにする
- サマリーは4〜5文の完全な文章にする

**やらないこと**:
- 情報を省略・削除・要約しすぎること（全情報を保持すること）
- 新しい情報を追加・推測で補完すること
- 数字・固有名詞・URL・日付を変えること
- JSONの構造・キー名を変えること
- 整数値（スコア等）を文字列に変えること（またはその逆）

## 整形対象のフィールド

以下のフィールドのテキスト値のみ整形してください。リスト内の各文字列要素も対象です:
- `summary`
- `details.service` の各テキストフィールド（`flow_steps` リストを含む）
- `details.business_model` の各テキストフィールド
- `details.differentiation` の各テキストフィールド（`unique_features`, `authority_claims` リストを含む）
- `details.scale` の各テキストフィールド
- `details.company` の各テキストフィールド
- `details.marketing` の各テキストフィールド（`channels` リストを含む、`social_followers` 内も）
- `details.reputation` の `positive_themes`, `negative_themes` リスト
- `details.news` の各要素の `title`, `summary` フィールド
- `scores.scoring_rationale`
- `data_gaps` リストの各要素

整形しないフィールド（値をそのまま保持）:
- `company_id`, `collected_at`
- `scores.threat_level`, `scores.service_completeness`, `scores.marketing_strength`（整数値）
- URL文字列全般（`dealer_lp_url`, `source_url` 等）

---

## 入力JSON

```json
{raw_json}
```

---

## 出力形式

整形後のJSONのみを出力してください（コメント・説明文・コードブロック記法は不要）。
出力後、以下のコマンドで保存してください:

```
python skills/save_research.py --company {company["id"]} --data '<出力したJSON>'
```
"""


if __name__ == "__main__":
    app()
