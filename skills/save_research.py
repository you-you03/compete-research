"""
Usage:
  python skills/save_research.py --company mota --data '{"summary": "...", ...}'

Saves Claude's research result (JSON string) to cache and updates history.
"""

import json
import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).parent.parent))

from compete_research.agents.research_agent import get_company, save_research

app = typer.Typer(add_completion=False)


@app.command()
def main(
    company: str = typer.Option(..., "--company", "-c", help="Company ID"),
    data: str = typer.Option(..., "--data", "-d", help="JSON string of research result"),
) -> None:
    c = get_company(company)
    if not c:
        typer.echo(f"Error: '{company}' が companies.json に見つかりません", err=True)
        raise typer.Exit(1)

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: JSON parse failed: {e}", err=True)
        raise typer.Exit(1)

    path = save_research(company, parsed)
    typer.echo(f"保存完了: {path}", err=True)
    print(str(path))


if __name__ == "__main__":
    app()
