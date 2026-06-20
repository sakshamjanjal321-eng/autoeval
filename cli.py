import os
import asyncio
from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel

from autoeval.loader import load_suite
from autoeval.runner import TestSuiteRunner
from autoeval.reporters.rich_cli import RichCLIReporter
from autoeval.reporters.json_reporter import JSONReporter
from autoeval.reporters.html_reporter import HTMLReporter

app = typer.Typer(help="AutoEval: A modern, asynchronous LLM Benchmark Suite CLI")
console = Console()

def run_async(coro):
    """Helper to run async coroutines in sync Typer commands."""
    return asyncio.run(coro)

@app.command()
def run(
    suite: str = typer.Argument(..., help="Path to the test suite YAML file"),
    model: Optional[List[str]] = typer.Option(None, "--model", "-m", help="Models to evaluate. Overrides YAML defaults if provided."),
    output_dir: str = typer.Option("reports", "--output-dir", "-o", help="Directory to save the reports"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max number of concurrent API requests")
):
    """Runs a benchmark suite against specified models."""
    if not os.path.exists(suite):
        console.print(f"[bold red]Error:[/] Suite file '{suite}' not found.", err=True)
        raise typer.Exit(code=1)
        
    try:
        test_suite = load_suite(suite)
    except Exception as e:
        console.print(f"[bold red]Schema Error:[/] Failed to parse suite YAML: {e}", err=True)
        raise typer.Exit(code=1)
        
    models_to_run = model if model else test_suite.models
    if not models_to_run:
        console.print("[bold yellow]Warning:[/] No models specified in CLI or YAML. Defaulting to mock model.", style="yellow")
        models_to_run = ["mock/good"]
        
    # Setup reporters
    cli_reporter = RichCLIReporter()
    runner = TestSuiteRunner(
        suite=test_suite,
        models=models_to_run,
        concurrency=concurrency,
        reporters=[cli_reporter]
    )
    
    # Run tests
    results = run_async(runner.run())
    
    # Generate reports
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename friendly timestamp
    safe_time = results.timestamp.replace(":", "-").replace(" ", "_")
    json_path = os.path.join(output_dir, f"report_{safe_time}.json")
    html_path = os.path.join(output_dir, f"report_{safe_time}.html")
    
    # JSON reporter
    json_reporter = JSONReporter()
    json_reporter.write(results, json_path)
    
    # HTML reporter
    html_reporter = HTMLReporter()
    html_reporter.write(results, html_path)
    
    console.print(Panel(
        f"[green][OK] Evaluation complete![/]\n\n"
        f"[bold white]JSON Trace:[/] {json_path}\n"
        f"[bold white]HTML Dashboard:[/] {html_path}",
        title="Reports Generated",
        border_style="green"
    ))

@app.command()
def validate(
    suite: str = typer.Argument(..., help="Path to the test suite YAML file")
):
    """Validates the syntax and structure of a test suite YAML file."""
    if not os.path.exists(suite):
        console.print(f"[bold red]Error:[/] Suite file '{suite}' not found.", err=True)
        raise typer.Exit(code=1)
        
    try:
        test_suite = load_suite(suite)
        console.print(Panel(
            f"[green][OK] YAML syntax is valid![/]\n\n"
            f"[bold white]Suite Name:[/] {test_suite.name}\n"
            f"[bold white]Description:[/] {test_suite.description or 'N/A'}\n"
            f"[bold white]Models:[/] {', '.join(test_suite.models) if test_suite.models else 'None default'}\n"
            f"[bold white]Test Cases:[/] {len(test_suite.tests)} tests found.",
            title="Validation Succeeded",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[bold red]Validation Failed:[/] {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
