"""Ava self-host CLI — init, start, upgrade (Phase 5)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Ava self-host CLI")


@app.command()
def init(path: Path = Path(".")):
    """Copy .env.example and print next steps."""
    env_example = Path(__file__).resolve().parents[5] / ".env.example"
    target = path / ".env"
    if not target.exists() and env_example.exists():
        target.write_text(env_example.read_text())
    typer.echo(f"Initialized Ava at {path.resolve()}")
    typer.echo("Run: ava start")


@app.command()
def start(production: bool = False):
    """Start docker-compose stack."""
    root = Path(__file__).resolve().parents[5]
    compose = "docker-compose.prod.yml" if production else "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(root / compose), "up", "-d"]
    subprocess.run(cmd, cwd=root, check=False)
    typer.echo("Ava stack starting — API :8000, Web :3000, Collab :1234")


@app.command()
def upgrade():
    """Pull images and run DB migrate."""
    root = Path(__file__).resolve().parents[5]
    subprocess.run(["docker", "compose", "pull"], cwd=root, check=False)
    subprocess.run(
        ["docker", "compose", "run", "--rm", "api", "python", "-m", "ava_api.db", "migrate"],
        cwd=root,
        check=False,
    )
    typer.echo("Upgrade complete.")
