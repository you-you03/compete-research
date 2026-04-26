"""
Usage (Claude Code skill entry point):
  python skills/research.py --company mota
  python skills/research.py --all
  python skills/research.py --list

Prints research prompt to stdout for Claude to execute with WebSearch/WebFetch.
If cached data exists within TTL, prints the cache instead.
"""

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from compete_research.agents.research_agent import (
    build_research_prompt,
    get_company,
    load_all_latest_research,
    load_cached_research,
    load_companies,
)

app = typer.Typer(add_completion=False)


@app.command()
def main(
    company: str = typer.Option("", "--company", "-c", help="Company ID to research"),
    all_companies: bool = typer.Option(False, "--all", "-a", help="Research all companies"),
    list_companies: bool = typer.Option(False, "--list", "-l", help="List available companies"),
    force: bool = typer.Option(False, "--force", "-f", help="Ignore cache and re-research"),
    industry: str = typer.Option("", "--industry", help="Filter by industry tag"),
) -> None:
    if list_companies:
        companies = load_companies(industry or None)
        print(json.dumps(companies, ensure_ascii=False, indent=2))
        return

    if all_companies:
        companies = load_companies(industry or None)
        for c in companies:
            _print_research_for(c["id"], force)
        return

    if company:
        _print_research_for(company, force)
        return

    typer.echo("Error: --company, --all, or --list が必要です", err=True)
    raise typer.Exit(1)


def _print_research_for(company_id: str, force: bool) -> None:
    company = get_company(company_id)
    if not company:
        typer.echo(f"Error: '{company_id}' が companies.json に見つかりません", err=True)
        raise typer.Exit(1)

    if not force:
        cached = load_cached_research(company_id)
        if cached:
            typer.echo(f"\n[キャッシュあり] {company['name']} (TTL内)", err=True)
            print(json.dumps(cached, ensure_ascii=False, indent=2))
            return

    typer.echo(f"\n[調査開始] {company['name']}", err=True)
    print(build_research_prompt(company))


if __name__ == "__main__":
    app()
