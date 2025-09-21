"""CLI for discovering datasets using Hugging Science Portal insights."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.portal_integration import HuggingSciencePortal, EnhancedDiscoveryWithPortal
from src.utils.logger import setup_logging


console = Console()
logger = setup_logging()


@click.group()
def cli():
    """Hugging Science Portal Integration Commands."""
    pass


@cli.command()
@click.option(
    "--category",
    type=click.Choice([
        "genomics", "proteomics", "medical_imaging", "clinical_data",
        "drug_discovery", "neuroscience", "chemistry", "biology",
        "physics", "earth_science", "environmental", "materials_science"
    ]),
    help="Scientific category to focus on"
)
@click.option(
    "--max-score",
    type=click.IntRange(0, 100),
    default=30,
    help="Maximum quality score (to find those needing improvement)"
)
@click.option(
    "--limit",
    type=click.IntRange(1, 500),
    default=100,
    help="Maximum datasets to discover"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for results"
)
@click.option(
    "--show-recommendations",
    is_flag=True,
    default=True,
    help="Show improvement recommendations"
)
def portal_search(
    category: Optional[str],
    max_score: int,
    limit: int,
    output: Optional[str],
    show_recommendations: bool
):
    """Search for datasets using Hugging Science Portal insights.

    This command connects to the Hugging Science Dataset Insight Portal
    to find high-priority science datasets that need documentation improvement.

    Examples:
        # Find genomics datasets needing improvement
        python -m src.cli.portal_discover portal-search --category genomics

        # Find all science datasets with poor documentation
        python -m src.cli.portal_discover portal-search --max-score 20

        # Export results with recommendations
        python -m src.cli.portal_discover portal-search --output results.json
    """
    console.print(
        Panel.fit(
            f"[bold blue]Hugging Science Portal Search[/bold blue]\n"
            f"Category: {category or 'All'}\n"
            f"Max Quality Score: {max_score}/100",
            border_style="blue"
        )
    )

    async def run_search():
        async with HuggingSciencePortal() as portal:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Searching portal...", total=None)

                # Search for datasets
                insights = await portal.search_science_datasets(
                    category=category,
                    max_quality_score=max_score,
                    limit=limit,
                    sort_by="improvement_priority"
                )

                progress.update(task, description="Fetching recommendations...")

                # Get recommendations for top candidates
                if show_recommendations and insights:
                    for insight in insights[:10]:  # Top 10
                        recs = await portal.get_improvement_recommendations(
                            insight.repo_id
                        )
                        insight.recommendations = recs

                return insights

    try:
        insights = asyncio.run(run_search())

        if not insights:
            console.print("[yellow]No datasets found matching criteria[/yellow]")
            return

        # Display results
        display_portal_results(insights, show_recommendations)

        # Save if requested
        if output:
            save_portal_results(insights, output)
            console.print(f"[green]Results saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--timeframe",
    type=click.Choice(["day", "week", "month"]),
    default="week",
    help="Time period for trending datasets"
)
@click.option(
    "--category",
    type=click.Choice([
        "genomics", "proteomics", "medical_imaging", "clinical_data",
        "drug_discovery", "neuroscience", "chemistry", "biology",
        "physics", "earth_science", "environmental", "materials_science"
    ]),
    help="Filter by scientific category"
)
def trending(timeframe: str, category: Optional[str]):
    """Show trending science datasets from the portal.

    Displays datasets gaining traction in the scientific community
    that may benefit from documentation improvements.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Trending Science Datasets[/bold cyan]\n"
            f"Timeframe: {timeframe}\n"
            f"Category: {category or 'All'}",
            border_style="cyan"
        )
    )

    async def get_trending():
        async with HuggingSciencePortal() as portal:
            return await portal.get_trending_science_datasets(
                timeframe=timeframe,
                category=category
            )

    try:
        trending_datasets = asyncio.run(get_trending())

        if not trending_datasets:
            console.print("[yellow]No trending datasets found[/yellow]")
            return

        # Display trending datasets
        table = Table(
            title="Trending Science Datasets",
            show_lines=True,
            header_style="bold cyan"
        )

        table.add_column("Repository", style="blue", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Downloads", justify="right", style="green")
        table.add_column("Quality", justify="right")
        table.add_column("Trend", style="yellow")

        for dataset in trending_datasets[:20]:
            table.add_row(
                dataset.get("id", "Unknown"),
                dataset.get("category", "N/A"),
                str(dataset.get("downloads", 0)),
                f"{dataset.get('quality_score', 0):.0f}/100",
                dataset.get("trend", "↑")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--limit",
    type=click.IntRange(1, 500),
    default=200,
    help="Maximum datasets to discover"
)
@click.option(
    "--categories",
    multiple=True,
    help="Scientific categories (can specify multiple)"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for results"
)
def enhanced_discovery(limit: int, categories: tuple, output: Optional[str]):
    """Run enhanced discovery combining our system with portal insights.

    This combines traditional keyword-based discovery with portal insights
    to provide the most comprehensive view of datasets needing improvement.

    Examples:
        # Full enhanced discovery
        python -m src.cli.portal_discover enhanced-discovery --limit 300

        # Focus on specific categories
        python -m src.cli.portal_discover enhanced-discovery --categories genomics --categories proteomics
    """
    console.print(
        Panel.fit(
            "[bold green]Enhanced Discovery with Portal Insights[/bold green]\n"
            f"Combining traditional search with portal intelligence\n"
            f"Target: {limit} datasets",
            border_style="green"
        )
    )

    async def run_enhanced():
        enhancer = EnhancedDiscoveryWithPortal()
        return await enhancer.discover_with_insights(
            limit=limit,
            categories=list(categories) if categories else None
        )

    try:
        with console.status("[bold green]Running enhanced discovery..."):
            results = asyncio.run(run_enhanced())

        if not results:
            console.print("[yellow]No datasets discovered[/yellow]")
            return

        # Display combined results
        display_enhanced_results(results)

        # Show statistics
        portal_count = sum(1 for r in results if r.get("source") == "portal")
        traditional_count = sum(1 for r in results if r.get("source") == "traditional")
        trending_count = sum(1 for r in results if r.get("is_trending"))

        console.print(
            Panel(
                f"[bold]Discovery Statistics[/bold]\n"
                f"Total Discovered: {len(results)}\n"
                f"From Portal: {portal_count}\n"
                f"From Traditional: {traditional_count}\n"
                f"Trending: {trending_count}",
                title="Summary",
                border_style="green"
            )
        )

        # Save if requested
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(f"[green]Results saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


def display_portal_results(insights, show_recommendations):
    """Display portal search results."""
    table = Table(
        title="Portal Dataset Insights",
        show_lines=True,
        header_style="bold cyan"
    )

    table.add_column("Repository", style="blue", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Quality", justify="right")
    table.add_column("Priority", justify="right", style="red")
    table.add_column("Missing", style="yellow")

    for insight in insights[:20]:
        missing = ", ".join(insight.missing_components[:2])
        if len(insight.missing_components) > 2:
            missing += f" (+{len(insight.missing_components) - 2})"

        table.add_row(
            insight.repo_id,
            insight.category,
            f"{insight.documentation_score:.0f}/100",
            f"{insight.improvement_priority:.0f}",
            missing or "None"
        )

    console.print(table)

    # Show recommendations for top candidates
    if show_recommendations and hasattr(insights[0], 'recommendations'):
        console.print("\n[bold]Top Improvement Recommendations:[/bold]")
        for i, insight in enumerate(insights[:5], 1):
            if hasattr(insight, 'recommendations'):
                console.print(f"\n{i}. [blue]{insight.repo_id}[/blue]")
                recs = insight.recommendations.get("recommendations", [])
                for rec in recs[:3]:
                    console.print(f"   - {rec}")


def display_enhanced_results(results):
    """Display enhanced discovery results."""
    table = Table(
        title="Enhanced Discovery Results",
        show_lines=True,
        header_style="bold green"
    )

    table.add_column("Repository", style="blue", no_wrap=True)
    table.add_column("Source", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Priority", justify="right", style="red")
    table.add_column("Status", style="yellow")

    for result in results[:30]:
        status = ""
        if result.get("is_trending"):
            status = "TRENDING"
        elif result.get("source") == "portal":
            status = "PORTAL"
        else:
            status = "DISCOVERED"

        table.add_row(
            result.get("repo_id", "Unknown"),
            result.get("source", "N/A"),
            f"{result.get('documentation_score', 0):.0f}/100",
            f"{result.get('improvement_priority', 0):.0f}",
            status
        )

    console.print(table)


def save_portal_results(insights, output_path):
    """Save portal results to file."""
    data = []
    for insight in insights:
        data.append({
            "repo_id": insight.repo_id,
            "category": insight.category,
            "documentation_score": insight.documentation_score,
            "improvement_priority": insight.improvement_priority,
            "missing_components": insight.missing_components,
            "recommended_tags": insight.recommended_tags,
            "usage_stats": insight.usage_stats,
            "community_engagement": insight.community_engagement,
            "recommendations": getattr(insight, 'recommendations', {})
        })

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    cli()