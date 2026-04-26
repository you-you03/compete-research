"""
Usage:
  python skills/dashboard.py

Generates reports/dashboard.html and reports/research/research_{date}.md
from cached research data.
"""

import json
import sys
from datetime import date
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from compete_research.agents.research_agent import load_all_latest_research, load_companies
from compete_research.config import settings

app = typer.Typer(add_completion=False)

TEMPLATES_DIR = Path(__file__).parent.parent / "compete_research" / "templates"


@app.command()
def main(
    html: bool = typer.Option(True, "--html/--no-html", help="Generate HTML dashboard"),
    md: bool = typer.Option(True, "--md/--no-md", help="Generate Markdown report"),
) -> None:
    research_data = load_all_latest_research()
    companies = {c["id"]: c for c in load_companies()}

    if not research_data:
        typer.echo("キャッシュが見つかりません。先に research.py を実行してください。", err=True)
        raise typer.Exit(1)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    (settings.reports_dir / "research").mkdir(exist_ok=True)

    if html:
        _generate_html(research_data, companies)

    if md:
        _generate_markdown(research_data, companies)


def _generate_html(research_data: list[dict], companies: dict) -> None:
    today = date.today().isoformat()
    html = _build_html(research_data, companies, today)
    out = settings.reports_dir / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    typer.echo(f"HTML生成: {out}")


def _build_companies_data(data: list[dict], companies: dict) -> list[dict]:
    result = []
    for item in data:
        cid = item.get("company_id", "")
        meta = companies.get(cid, {})
        result.append({
            "id": cid,
            "name": meta.get("name", cid),
            "url": meta.get("url", ""),
            "priority": meta.get("priority", "medium"),
            "summary": item.get("summary", ""),
            "details": item.get("details", {}),
            "scores": item.get("scores", {}),
            "data_gaps": item.get("data_gaps", []),
            "collected_at": item.get("collected_at", ""),
        })
    return result


def _build_html(data: list[dict], companies: dict, today: str) -> str:
    companies_list = _build_companies_data(data, companies)
    companies_json = json.dumps(companies_list, ensure_ascii=False, indent=2)
    template = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")
    return (
        template
        .replace("__COMPANIES_JSON__", companies_json)
        .replace("__TODAY__", today)
    )


def _generate_markdown(research_data: list[dict], companies: dict) -> None:
    today = date.today().isoformat()
    md = _build_markdown(research_data, companies, today)
    out = settings.reports_dir / "research" / f"research_{today}.md"
    out.write_text(md, encoding="utf-8")
    typer.echo(f"Markdown生成: {out}")


def _build_markdown(data: list[dict], companies: dict, today: str) -> str:
    lines = [f"# 競合リサーチレポート {today}\n"]
    lines.append("## 一覧\n")
    lines.append("| 企業 | ビジネスモデル | 差別化要因 | 脅威度 |")
    lines.append("|------|--------------|-----------|-------|")

    for item in data:
        cid = item.get("company_id", "")
        meta = companies.get(cid, {})
        name = meta.get("name", cid)
        details = item.get("details", {})
        bm = details.get("business_model", {}).get("revenue_type", "-")
        diff = details.get("differentiation", {})
        features = ", ".join(diff.get("unique_features", ["-"])[:2])
        threat = item.get("scores", {}).get("threat_level", "-")
        lines.append(f"| {name} | {bm} | {features} | {threat}/5 |")

    lines.append("\n---\n")

    for item in data:
        cid = item.get("company_id", "")
        meta = companies.get(cid, {})
        name = meta.get("name", cid)
        details = item.get("details", {})

        lines.append(f"## {name}\n")
        lines.append(f"**サマリー**: {item.get('summary', '-')}\n")

        bm = details.get("business_model", {})
        lines.append("### ビジネスモデル")
        lines.append(f"- 収益タイプ: {bm.get('revenue_type', '-')}")
        lines.append(f"- お金の流れ: {bm.get('money_flow', '-')}")
        lines.append(f"- 情報の流れ: {bm.get('info_flow', '-')}\n")

        svc = details.get("service", {})
        lines.append("### サービス内容")
        lines.append(f"- 概要: {svc.get('overview', '-')}")
        lines.append(f"- フロー: {svc.get('flow', '-')}")
        lines.append(f"- 提携業者: {svc.get('partners', '-')}")
        methods = ", ".join(svc.get("methods", []))
        lines.append(f"- 対応方式: {methods or '-'}")
        lines.append(f"- 最短査定: {svc.get('speed', '-')}\n")

        diff = details.get("differentiation", {})
        lines.append("### 差別化要因")
        for f in diff.get("unique_features", []):
            lines.append(f"- {f}")
        lines.append(f"- ターゲット: {diff.get('target_users', '-')}")
        lines.append(f"- メッセージ: {diff.get('brand_message', '-')}\n")

        news = details.get("news", [])
        if news:
            lines.append("### 最新動向")
            for n in news:
                lines.append(f"- {n}")
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


if __name__ == "__main__":
    app()
