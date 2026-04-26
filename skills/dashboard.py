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
from jinja2 import Environment, FileSystemLoader, select_autoescape

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


def _generate_markdown(research_data: list[dict], companies: dict) -> None:
    today = date.today().isoformat()
    md = _build_markdown(research_data, companies, today)
    out = settings.reports_dir / "research" / f"research_{today}.md"
    out.write_text(md, encoding="utf-8")
    typer.echo(f"Markdown生成: {out}")


def _score_bar(value: int, color: str = "#6366f1") -> str:
    pct = min(max(int(value) * 20, 0), 100) if str(value).isdigit() else 0
    return (
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar" style="width:{pct}%;background:{color}"></div>'
        f'</div><span class="score-num">{value}/5</span>'
    )


def _ul(items: list, cls: str = "") -> str:
    if not items:
        return "<p class='na'>データなし</p>"
    cls_attr = f' class="{cls}"' if cls else ""
    return "<ul" + cls_attr + ">" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def _kv(label: str, value: str) -> str:
    if not value or value == "-":
        return ""
    return f'<div class="kv"><span class="kv-label">{label}</span><span class="kv-val">{value}</span></div>'


def _section(title: str, emoji: str, content: str, open_: bool = False) -> str:
    open_attr = " open" if open_ else ""
    return (
        f'<details{open_attr}><summary>{emoji} {title}</summary>'
        f'<div class="section-body">{content}</div></details>'
    )


def _build_html(data: list[dict], companies: dict, today: str) -> str:
    cards = ""
    for item in data:
        cid = item.get("company_id", "")
        meta = companies.get(cid, {})
        name = meta.get("name", cid)
        priority = meta.get("priority", "medium")
        summary = item.get("summary", "データなし")
        d = item.get("details", {})
        svc = d.get("service", {})
        bm = d.get("business_model", {})
        diff = d.get("differentiation", {})
        scale = d.get("scale", {})
        mkt = d.get("marketing", {})
        rep = d.get("reputation", {})
        scores = item.get("scores", {})
        collected = item.get("collected_at", "")[:10]

        # ── スコアバー ──
        threat = str(scores.get("threat_level", "-"))
        svc_score = str(scores.get("service_completeness", "-"))
        mkt_score = str(scores.get("marketing_strength", "-"))
        score_html = f"""
          <div class="scores">
            <div class="score-item">
              <span class="score-label">脅威度</span>
              {_score_bar(threat, '#ef4444')}
            </div>
            <div class="score-item">
              <span class="score-label">サービス完成度</span>
              {_score_bar(svc_score, '#3b82f6')}
            </div>
            <div class="score-item">
              <span class="score-label">マーケ強度</span>
              {_score_bar(mkt_score, '#10b981')}
            </div>
          </div>
          {'<p class="score-rationale">' + scores.get('scoring_rationale','') + '</p>' if scores.get('scoring_rationale') else ''}
        """

        # ── LP キャッチコピー ──
        catchcopy = diff.get("lp_catchcopy", "")
        catchcopy_html = f'<blockquote class="catchcopy">"{catchcopy}"</blockquote>' if catchcopy else ""

        # ── サービス仕様 ──
        flow_steps = svc.get("flow_steps", [])
        flow_html = (
            "<ol>" + "".join(f"<li>{s}</li>" for s in flow_steps) + "</ol>"
            if flow_steps else "<p class='na'>データなし</p>"
        )
        svc_html = (
            _kv("概要", svc.get("overview", ""))
            + "<div class='subsection-title'>申し込みフロー</div>" + flow_html
            + _kv("必須入力", svc.get("required_inputs", ""))
            + _kv("提携業者", svc.get("partners", ""))
            + _kv("査定方法", ", ".join(svc.get("assessment_types", svc.get("methods", []))))
            + _kv("対象車種", svc.get("eligible_vehicles", ""))
            + _kv("対応エリア", svc.get("coverage_area", ""))
            + _kv("最短査定", svc.get("speed", ""))
            + _kv("査定後の流れ", svc.get("post_assessment_flow", ""))
            + _kv("iOS アプリ", (svc.get("app") or {}).get("ios", ""))
            + _kv("Android アプリ", (svc.get("app") or {}).get("android", ""))
        )

        # ── ビジネスモデル ──
        bm_html = (
            _kv("収益タイプ", bm.get("revenue_type", bm.get("money_flow", "")))
            + _kv("ユーザー費用", bm.get("user_cost", ""))
            + _kv("業者費用構造", bm.get("dealer_cost", ""))
            + _kv("業者獲得", bm.get("dealer_acquisition", ""))
            + _kv("情報開示タイミング", bm.get("info_disclosure", bm.get("info_flow", "")))
            + _kv("副収益", bm.get("secondary_revenue", ""))
        )

        # ── 差別化要因 ──
        diff_html = (
            "<div class='subsection-title'>独自機能</div>"
            + _ul(diff.get("unique_features", []))
            + _kv("ターゲット", diff.get("target_users", ""))
            + _kv("ブランドメッセージ", diff.get("brand_message", ""))
            + ("<div class='subsection-title'>権威付け・No.1実績</div>"
               + _ul(diff.get("authority_claims", [])) if diff.get("authority_claims") else "")
        )

        # ── 規模感・実績 ──
        scale_html = (
            _kv("月間利用者数", scale.get("users", ""))
            + _kv("査定件数実績", scale.get("assessments", ""))
            + _kv("提携業者推移", scale.get("partners_trend", ""))
            + _kv("サービス開始", scale.get("launch_year", ""))
        )

        # ── マーケティング ──
        social = mkt.get("social_followers", {})
        social_html = ""
        if social:
            social_html = (
                "<div class='subsection-title'>SNSフォロワー</div>"
                + _kv("X / Twitter", social.get("twitter_x", ""))
                + _kv("YouTube", social.get("youtube", ""))
                + _kv("Instagram", social.get("instagram", ""))
            )
        mkt_html = (
            _kv("TVCM", mkt.get("tv_cm", ""))
            + _kv("SEO順位", mkt.get("seo_rankings", ""))
            + _kv("推定流入", mkt.get("estimated_traffic", ""))
            + _kv("広告訴求テーマ", mkt.get("ad_theme", ""))
            + social_html
            + _kv("チャネル", ", ".join(mkt.get("channels", [])))
        )

        # ── ユーザー評判 ──
        pos = rep.get("positive_themes", [])
        neg = rep.get("negative_themes", [])
        rep_html = ""
        if pos:
            rep_html += "<div class='subsection-title'>👍 好評ポイント</div>" + _ul(pos, "pos-list")
        if neg:
            rep_html += "<div class='subsection-title'>👎 不満ポイント</div>" + _ul(neg, "neg-list")
        if not rep_html:
            rep_html = "<p class='na'>データなし</p>"

        # ── 最新動向 ──
        news_items = d.get("news", [])
        news_html = ""
        for n in news_items:
            if isinstance(n, dict):
                news_html += (
                    f'<div class="news-item">'
                    f'<span class="news-date">{n.get("date","")}</span>'
                    f'<span class="news-title">{n.get("title","")}</span>'
                    f'<span class="news-body">{n.get("summary","")}</span>'
                    f'</div>'
                )
            else:
                news_html += f'<div class="news-item"><span class="news-body">{n}</span></div>'
        if not news_html:
            news_html = "<p class='na'>データなし</p>"

        # ── 採用シグナル ──
        hiring = item.get("details", {}).get("hiring_signals", [])
        hiring_html = _ul(hiring) if hiring else "<p class='na'>データなし</p>"

        # ── データ欠損 ──
        gaps = item.get("data_gaps", [])
        gaps_html = _ul(gaps) if gaps else ""

        # ── カード組み立て ──
        cards += f"""
        <div class="card priority-border-{priority}">
          <div class="card-header">
            <div class="card-title">
              <h2>{name}</h2>
              {f'<a class="company-url" href="{meta["url"]}" target="_blank">{meta["url"]}</a>' if meta.get("url") else ""}
            </div>
            <div class="badges">
              <span class="badge priority-{priority}">優先度: {priority}</span>
            </div>
          </div>
          {score_html}
          <p class="summary">{summary}</p>
          {catchcopy_html}
          <div class="sections">
            {_section("サービス仕様", "⚙️", svc_html, open_=True)}
            {_section("ビジネスモデル", "💰", bm_html)}
            {_section("差別化要因", "⭐", diff_html)}
            {_section("規模感・実績", "📊", scale_html)}
            {_section("マーケティング", "📣", mkt_html)}
            {_section("ユーザー評判", "💬", rep_html)}
            {_section("最新動向", "📰", news_html)}
            {_section("採用シグナル", "🏢", hiring_html)}
          </div>
          <div class="card-footer">
            {('<div class="gaps"><span class="gaps-label">取得できなかった情報: </span>' + ', '.join(gaps) + '</div>') if gaps else ''}
            <span>最終更新: {collected}</span>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>競合リサーチ ダッシュボード</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Hiragino Sans, sans-serif;
            background: #f0f2f5; color: #1a1a1a; font-size: 14px; }}
    header {{ background: #0f172a; color: #fff; padding: 18px 32px; display: flex;
              align-items: baseline; gap: 16px; }}
    header h1 {{ font-size: 1.25rem; font-weight: 700; }}
    header p {{ font-size: 0.8rem; color: #94a3b8; }}
    .container {{ max-width: 1400px; margin: 24px auto; padding: 0 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr)); gap: 20px; }}

    /* ── カード ── */
    .card {{ background: #fff; border-radius: 12px; overflow: hidden;
             box-shadow: 0 1px 4px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.04);
             border-left: 4px solid #e2e8f0; }}
    .priority-border-high  {{ border-left-color: #f59e0b; }}
    .priority-border-medium{{ border-left-color: #3b82f6; }}
    .priority-border-low   {{ border-left-color: #10b981; }}
    .priority-border-self  {{ border-left-color: #8b5cf6; }}

    .card-header {{ padding: 16px 18px 8px; display: flex; justify-content: space-between;
                   align-items: flex-start; gap: 8px; }}
    .card-title h2 {{ font-size: 1rem; font-weight: 700; }}
    .company-url {{ font-size: 0.7rem; color: #94a3b8; text-decoration: none; }}
    .company-url:hover {{ color: #3b82f6; }}
    .badges {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .badge {{ font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; white-space: nowrap; font-weight: 500; }}
    .priority-high   {{ background: #fef3c7; color: #92400e; }}
    .priority-medium {{ background: #dbeafe; color: #1e40af; }}
    .priority-low    {{ background: #d1fae5; color: #065f46; }}
    .priority-self   {{ background: #ede9fe; color: #5b21b6; }}

    /* ── スコア ── */
    .scores {{ padding: 6px 18px 10px; display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }}
    .score-item {{ display: flex; flex-direction: column; gap: 3px; }}
    .score-label {{ font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: .04em; }}
    .score-bar-wrap {{ background: #f1f5f9; border-radius: 4px; height: 6px; overflow: hidden; }}
    .score-bar {{ height: 100%; border-radius: 4px; transition: width .3s; }}
    .score-num {{ font-size: 0.75rem; font-weight: 600; color: #475569; }}
    .score-rationale {{ font-size: 0.72rem; color: #94a3b8; padding: 0 18px 8px; font-style: italic; }}

    /* ── サマリー ── */
    .summary {{ padding: 8px 18px 10px; font-size: 0.88rem; color: #374151; line-height: 1.65; }}
    .catchcopy {{ margin: 0 18px 12px; padding: 8px 12px; background: #f8fafc;
                 border-left: 3px solid #6366f1; font-size: 0.85rem; color: #4338ca;
                 font-style: italic; border-radius: 0 6px 6px 0; }}

    /* ── アコーディオンセクション ── */
    .sections {{ border-top: 1px solid #f1f5f9; }}
    details {{ border-bottom: 1px solid #f1f5f9; }}
    details summary {{
      padding: 9px 18px; cursor: pointer; font-size: 0.82rem; font-weight: 600;
      color: #374151; list-style: none; display: flex; align-items: center; gap: 6px;
      user-select: none; background: #fafafa;
    }}
    details summary::-webkit-details-marker {{ display: none; }}
    details summary::after {{ content: "▸"; margin-left: auto; color: #94a3b8; font-size: 0.7rem; }}
    details[open] summary::after {{ content: "▾"; }}
    details[open] summary {{ background: #f0f9ff; color: #0369a1; }}
    .section-body {{ padding: 10px 18px 14px; background: #fff; }}

    /* ── KV行 ── */
    .kv {{ display: grid; grid-template-columns: 7rem 1fr; gap: 6px 10px;
           padding: 4px 0; border-bottom: 1px dashed #f1f5f9; font-size: 0.82rem; }}
    .kv:last-child {{ border-bottom: none; }}
    .kv-label {{ color: #6b7280; font-weight: 500; white-space: nowrap; padding-top: 1px; }}
    .kv-val {{ color: #1f2937; line-height: 1.5; }}
    .subsection-title {{ font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
                         letter-spacing: .06em; color: #9ca3af; margin: 10px 0 5px; }}
    .section-body ul {{ padding-left: 16px; }}
    .section-body li {{ font-size: 0.82rem; line-height: 1.6; color: #374151; margin-bottom: 2px; }}
    .section-body ol {{ padding-left: 18px; }}
    .section-body ol li {{ font-size: 0.82rem; line-height: 1.6; color: #374151; margin-bottom: 3px; }}
    .pos-list li::marker {{ color: #10b981; }}
    .neg-list li::marker {{ color: #ef4444; }}

    /* ── ニュース ── */
    .news-item {{ display: grid; grid-template-columns: 4.5rem 1fr; gap: 4px 10px;
                 padding: 5px 0; border-bottom: 1px dashed #f1f5f9; }}
    .news-item:last-child {{ border-bottom: none; }}
    .news-date {{ font-size: 0.72rem; color: #94a3b8; font-weight: 500; padding-top: 2px; }}
    .news-title {{ font-size: 0.82rem; font-weight: 600; color: #1f2937; grid-column: 2; }}
    .news-body {{ font-size: 0.78rem; color: #6b7280; grid-column: 2; line-height: 1.5; }}

    /* ── フッター ── */
    .card-footer {{ padding: 10px 18px; background: #fafafa; border-top: 1px solid #f1f5f9;
                   font-size: 0.72rem; color: #9ca3af; display: flex;
                   justify-content: space-between; align-items: flex-start; gap: 8px;
                   flex-wrap: wrap; }}
    .gaps {{ flex: 1; color: #f59e0b; }}
    .gaps-label {{ font-weight: 600; }}
    .na {{ font-size: 0.78rem; color: #9ca3af; font-style: italic; }}
  </style>
</head>
<body>
  <header>
    <h1>競合リサーチ ダッシュボード</h1>
    <p>車買取一括査定サービス｜生成: {today}｜{len(data)}社</p>
  </header>
  <div class="container">
    <div class="grid">
      {cards}
    </div>
  </div>
</body>
</html>"""


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
