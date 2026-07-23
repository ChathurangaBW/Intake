from pathlib import Path

import typer

from intake.evidence import make_evidence_record

app = typer.Typer(help="Intake security automation framework")


@app.command()
def hash_artifact(path: Path, media_type: str = "application/octet-stream") -> None:
    """Create a local evidence record for a file."""
    if not path.exists() or not path.is_file():
        raise typer.BadParameter(f"Not a file: {path}")

    record = make_evidence_record(path, media_type=media_type, source_tool="intake.hash_artifact")
    typer.echo(record.model_dump_json(indent=2))


@app.command()
def doctor() -> None:
    """Check that the CLI is installed."""
    typer.echo("Intake CLI is installed.")
