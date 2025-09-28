"""Enhanced CLI for repository discovery with progress tracking and rich output."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live

from science_card_improvement.config.settings import get_settings
from science_card_improvement.discovery.repository import RepositoryDiscovery
from science_card_improvement.utils.logger import setup_logging
from science_card_improvement.validators.input import DiscoveryRequestValidator


console = Console()
logger = setup_logging()


@click.command()
@click.option(
    "--type",
    "repo_type",
    type=click.Choice(["dataset", "model", "both"]),
    default="both",
    help="Type of repositories to search for",
)
@click.option(
    "--limit",
    type=click.IntRange(1, 1000),
    default=200,
    help="Maximum number of repositories to return",
)
@click.option(
    "--keywords",
    multiple=True,
    help="Keywords to search for (can be specified multiple times)",
)
@click.option(
    "--sort-by",
    type=click.Choice(["downloads", "likes", "updated", "priority", "readme_quality"]),
    default="priority",
    help="Sort criteria for results",
)
@click.option(
    "--min-downloads",
    type=int,
    help="Minimum number of downloads",
)
@click.option(
    "--min-likes",
    type=int,
    help="Minimum number of likes",
)
@click.option(
    "--needs-improvement",
    is_flag=True,
    help="Only show repositories that need improvement",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for results",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "excel", "table"]),
    default="table",
    help="Output format",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--token",
    envvar="HF_TOKEN",
    help="Hugging Face API token",
)
def main(
    repo_type: str,
    limit: int,
    keywords: tuple,
    sort_by: str,
    min_downloads: Optional[int],
    min_likes: Optional[int],
    needs_improvement: bool,
    output: Optional[str],
    output_format: str,
    no_cache: bool,
    verbose: bool,
    token: Optional[str],
):
    """Discover science repositories on Hugging Face that need better documentation.

    This tool searches for datasets and models related to scientific domains,
    analyzes their documentation quality, and identifies opportunities for improvement.

    Examples:

        # Discover high-priority datasets that need improvement
        sci-discover --type dataset --needs-improvement --sort-by priority

        # Search for genomics repositories with low documentation
        sci-discover --keywords genomics --min-downloads 100 --output results.json

        # Export all science repositories to Excel
        sci-discover --limit 500 --format excel --output science_repos.xlsx
    """
    # Setup
    settings = get_settings()
    if verbose:
        settings.log_level = "DEBUG"
        setup_logging(log_level="DEBUG")

    # Show welcome message
    console.print(
        Panel.fit(
            f"[bold blue]Science Card Improvement - Repository Discovery[/bold blue]\n"
            f"Searching for {repo_type} repositories...",
            border_style="blue",
        )
    )

    # Validate input
    try:
        filters = {}
        if min_downloads is not None:
            filters["min_downloads"] = min_downloads
        if min_likes is not None:
            filters["min_likes"] = min_likes
        if needs_improvement:
            filters["needs_improvement"] = True

        validator = DiscoveryRequestValidator(
            repo_type=repo_type,
            limit=limit,
            keywords=list(keywords) if keywords else None,
            sort_by=sort_by,
            filters=filters if filters else None,
        )
    except Exception as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        raise click.Abort()

    # Check token
    if not token and not settings.hf_token:
        console.print(
            "[yellow]Warning: No Hugging Face token provided. "
            "Some features may be limited.[/yellow]"
        )
        console.print("Set your token with: export HF_TOKEN='your_token_here'")

    # Run discovery
    try:
        asyncio.run(
            discover_and_display(
                repo_type=repo_type,
                limit=limit,
                keywords=list(keywords) if keywords else None,
                sort_by=sort_by,
                filters=filters,
                output=output,
                output_format=output_format,
                cache_enabled=not no_cache,
                token=token,
                verbose=verbose,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Discovery cancelled by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error during discovery: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Exit(1)


async def discover_and_display(
    repo_type: str,
    limit: int,
    keywords: Optional[list],
    sort_by: str,
    filters: dict,
    output: Optional[str],
    output_format: str,
    cache_enabled: bool,
    token: Optional[str],
    verbose: bool,
):
    """Run discovery and display results."""
    # Initialize discovery client
    discovery = RepositoryDiscovery(
        token=token,
        cache_enabled=cache_enabled,
    )

    # Run discovery with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Discovering repositories...", total=None)

        repositories = await discovery.discover_repositories(
            repo_type=repo_type,
            limit=limit,
            keywords=keywords,
            filters=filters,
            sort_by=sort_by,
        )

        progress.update(task, description="Processing results...")

    # Display statistics
    stats = discovery.get_statistics()
    display_statistics(stats, verbose)

    # Handle output
    if output:
        output_path = Path(output)
        await discovery.export_results(repositories, output_path, format=output_format)
        console.print(f"[green]Results exported to {output_path}[/green]")

    # Display results
    if output_format == "table" or not output:
        display_results_table(repositories)
        display_summary(repositories)
    else:
        console.print(f"[green]Found {len(repositories)} repositories[/green]")


def display_results_table(repositories):
    """Display results in a rich table."""
    if not repositories:
        console.print("[yellow]No repositories found matching criteria[/yellow]")
        return

    # Create table
    table = Table(
        title="Discovery Results",
        show_lines=True,
        header_style="bold cyan",
    )

    # Add columns
    table.add_column("Repository", style="blue", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Downloads", justify="right", style="green")
    table.add_column("Likes", justify="right", style="yellow")
    table.add_column("README", style="cyan")
    table.add_column("Quality", justify="right")
    table.add_column("Priority", justify="right", style="red")
    table.add_column("Issues", style="dim")

    # Add rows (limit display to 20 for readability)
    for repo in repositories[:20]:
        readme_status = "YES" if repo.has_readme else "NO"
        if repo.has_readme:
            readme_status += f" ({repo.readme_length} chars)"

        quality_score = f"{repo.readme_quality_score:.0%}" if repo.has_readme else "N/A"
        priority_score = f"{repo.priority_score:.0f}"

        issues_str = ", ".join(repo.issues[:2]) if repo.issues else "None"
        if len(repo.issues) > 2:
            issues_str += f" (+{len(repo.issues) - 2} more)"

        table.add_row(
            repo.repo_id,
            repo.repo_type,
            str(repo.downloads),
            str(repo.likes),
            readme_status,
            quality_score,
            priority_score,
            issues_str,
        )

    console.print(table)

    if len(repositories) > 20:
        console.print(
            f"[dim]Showing first 20 of {len(repositories)} results. "
            f"Use --output to export all.[/dim]"
        )


def display_summary(repositories):
    """Display summary statistics."""
    if not repositories:
        return

    # Calculate statistics
    total = len(repositories)
    datasets = sum(1 for r in repositories if r.repo_type == "dataset")
    models = sum(1 for r in repositories if r.repo_type == "model")
    no_readme = sum(1 for r in repositories if not r.has_readme)
    short_readme = sum(1 for r in repositories if r.has_readme and r.readme_length < 300)
    need_improvement = sum(1 for r in repositories if r.priority_score > 50)

    # Average metrics
    avg_downloads = sum(r.downloads for r in repositories) / total if total else 0
    avg_likes = sum(r.likes for r in repositories) / total if total else 0
    avg_priority = sum(r.priority_score for r in repositories) / total if total else 0

    # Create summary panel
    summary = f"""
[bold]Repository Summary[/bold]
- Total: {total}
- Datasets: {datasets}
- Models: {models}
- Need Improvement: {need_improvement} ({need_improvement/total:.0%})

[bold]Documentation Status[/bold]
- Missing README: {no_readme} ({no_readme/total:.0%})
- Short README: {short_readme} ({short_readme/total:.0%})
- Average Priority: {avg_priority:.1f}/100

[bold]Popularity Metrics[/bold]
- Average Downloads: {avg_downloads:.0f}
- Average Likes: {avg_likes:.0f}
    """

    console.print(Panel(summary.strip(), title="Summary", border_style="green"))


def display_statistics(stats: dict, verbose: bool):
    """Display discovery statistics."""
    if not verbose:
        return

    stats_text = f"""
[bold]Discovery Statistics[/bold]
- Total Discovered: {stats.get('total_discovered', 0)}
- Total Processed: {stats.get('total_processed', 0)}
- API Calls: {stats.get('api_calls', 0)}
- Cache Hits: {stats.get('cache_hits', 0)}
- Errors: {stats.get('errors', 0)}
    """

    console.print(Panel(stats_text.strip(), title="Performance", border_style="dim"))


if __name__ == "__main__":
    main()