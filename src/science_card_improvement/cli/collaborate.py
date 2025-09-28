"""CLI for collaborative dataset improvement using portal status tracking."""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from science_card_improvement.analysis.baseline import BaselineAnalyzer
from science_card_improvement.portal.status import (
    CollaborativeWorkflow,
    PortalStatusManager,
    WorkStatus,
)
from science_card_improvement.utils.logger import setup_logging


console = Console()
logger = setup_logging()


@click.group()
def cli():
    """Collaborative Dataset Improvement Commands."""
    pass


@cli.command()
@click.option(
    "--user-id",
    required=True,
    help="Your Hugging Face user ID"
)
@click.option(
    "--category",
    type=click.Choice(["minimal", "low_quality", "needs_help"]),
    default="minimal",
    help="Category of datasets to target"
)
@click.option(
    "--domains",
    multiple=True,
    help="Preferred scientific domains (e.g., genomics, medical)"
)
def claim(user_id: str, category: str, domains: tuple):
    """Find and claim an available dataset to work on.

    This command searches for unclaimed datasets in the specified category
    and claims one for you to work on, preventing duplicate efforts.

    Examples:
        # Claim any minimal dataset
        python -m science_card_improvement.cli.collaborate claim --user-id myusername

        # Claim a minimal genomics dataset
        python -m science_card_improvement.cli.collaborate claim --user-id myusername --domains genomics

        # Claim from needs_help category
        python -m science_card_improvement.cli.collaborate claim --user-id myusername --category needs_help
    """
    console.print(
        Panel.fit(
            f"[bold blue]Finding Available Dataset[/bold blue]\n"
            f"User: {user_id}\n"
            f"Category: {category}\n"
            f"Domains: {', '.join(domains) if domains else 'Any'}",
            border_style="blue"
        )
    )

    async def run_claim():
        workflow = CollaborativeWorkflow(user_id)
        return await workflow.find_and_claim_dataset(
            category=category,
            preferred_domains=list(domains) if domains else None
        )

    try:
        result = asyncio.run(run_claim())

        if result:
            dataset_id = result["dataset_id"]
            metadata = result["metadata"]

            console.print(f"\n[green]Successfully claimed dataset![/green]")
            console.print(f"Dataset: [blue]{dataset_id}[/blue]")

            # Display metadata
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("Downloads", str(metadata.get("number_of_downloads", "N/A")))
            table.add_row("Storage Size", metadata.get("storage_size", "N/A"))
            table.add_row("Last Modified", metadata.get("last_modified", "N/A"))
            table.add_row("Doc Score", f"{metadata.get('documentation_score', 0):.1f}/100")
            table.add_row("Category", metadata.get("category", "N/A"))

            console.print(table)

            console.print("\n[bold]Next Steps:[/bold]")
            console.print("1. Analyze the dataset: python -m science_card_improvement.cli.compare analyze --repo-id " + dataset_id)
            console.print("2. Create improvements based on baselines")
            console.print("3. Update status: python -m science_card_improvement.cli.collaborate update --user-id " + user_id + " --dataset-id " + dataset_id)
            console.print("4. Submit PR and mark complete")

        else:
            console.print("[yellow]No available datasets found to claim.[/yellow]")
            console.print("All datasets in this category may already be claimed.")
            console.print("Try a different category or check back later.")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--user-id",
    required=True,
    help="Your Hugging Face user ID"
)
@click.option(
    "--dataset-id",
    required=True,
    help="Dataset you're working on"
)
@click.option(
    "--status",
    type=click.Choice(["in_progress", "reviewing", "needs_help", "blocked", "completed"]),
    required=True,
    help="Current work status"
)
@click.option(
    "--notes",
    help="Optional status notes"
)
@click.option(
    "--pr-url",
    help="PR URL (if completed)"
)
def update(user_id: str, dataset_id: str, status: str, notes: Optional[str], pr_url: Optional[str]):
    """Update your work status on a dataset.

    Examples:
        # Mark as still in progress
        python -m science_card_improvement.cli.collaborate update --user-id myusername --dataset-id org/dataset --status in_progress
        python -m science_card_improvement.cli.collaborate update --user-id myusername --dataset-id org/dataset --status needs_help --notes "Need help with medical terminology"

        # Mark as completed
        python -m science_card_improvement.cli.collaborate update --user-id myusername --dataset-id org/dataset --status completed --pr-url https://github.com/...
    """
    work_status = WorkStatus[status.upper()]

    console.print(f"Updating status for [blue]{dataset_id}[/blue]...")

    async def run_update():
        async with PortalStatusManager(user_id) as manager:
            return await manager.update_status(
                dataset_id=dataset_id,
                status=work_status,
                notes=notes,
                pr_url=pr_url
            )

    try:
        success = asyncio.run(run_update())

        if success:
            console.print(f"[green]Status updated successfully![/green]")
            console.print(f"Dataset: {dataset_id}")
            console.print(f"Status: {status}")
            if notes:
                console.print(f"Notes: {notes}")
            if pr_url:
                console.print(f"PR: {pr_url}")
        else:
            console.print("[red]Failed to update status.[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--dataset-id",
    required=True,
    help="Dataset to check"
)
def check(dataset_id: str):
    """Check if a dataset is available or who's working on it.

    Examples:
        python -m science_card_improvement.cli.collaborate check --dataset-id arcinstitute/opengenome2
    """
    console.print(f"Checking status of [blue]{dataset_id}[/blue]...")

    async def run_check():
        async with PortalStatusManager() as manager:
            status = await manager.check_availability(dataset_id)
            metadata = await manager.get_dataset_metadata(dataset_id)
            return status, metadata

    try:
        status, metadata = asyncio.run(run_check())

        # Display status
        if status.get("available"):
            console.print(f"[green]Dataset is available to claim![/green]")
        else:
            console.print(f"[yellow]Dataset is currently being worked on[/yellow]")
            console.print(f"Worker: {status.get('current_worker', 'Unknown')}")
            console.print(f"Status: {status.get('status', 'Unknown')}")
            console.print(f"Last Updated: {status.get('last_updated', 'Unknown')}")

        # Display metadata
        if metadata:
            console.print("\n[bold]Dataset Metadata:[/bold]")
            table = Table(show_header=False, box=None)
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("Downloads", str(metadata.get("number_of_downloads", "N/A")))
            table.add_row("Storage Size", metadata.get("storage_size", "N/A"))
            table.add_row("Last Modified", metadata.get("last_modified", "N/A"))
            table.add_row("Doc Score", f"{metadata.get('documentation_score', 0):.1f}/100")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--user-id",
    required=True,
    help="Your Hugging Face user ID"
)
def my_work(user_id: str):
    """Show all datasets you're currently working on.

    Examples:
        python -m science_card_improvement.cli.collaborate my-work --user-id myusername
    """
    console.print(f"Fetching work for [blue]{user_id}[/blue]...")

    async def run_my_work():
        async with PortalStatusManager(user_id) as manager:
            return await manager.get_my_datasets()

    try:
        datasets = asyncio.run(run_my_work())

        if not datasets:
            console.print("[yellow]You're not currently working on any datasets.[/yellow]")
            return

        # Display datasets
        table = Table(
            title=f"Datasets for {user_id}",
            show_lines=True,
            header_style="bold cyan"
        )

        table.add_column("Dataset", style="blue", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="green")
        table.add_column("Notes", style="dim")

        for dataset in datasets:
            table.add_row(
                dataset.get("dataset_id", "Unknown"),
                dataset.get("status", "Unknown"),
                dataset.get("started_at", "N/A"),
                dataset.get("notes", "")[:50]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Number of datasets to show"
)
@click.option(
    "--exclude-claimed",
    is_flag=True,
    default=True,
    help="Exclude already claimed datasets"
)
def find_minimal(limit: int, exclude_claimed: bool):
    """Find minimal documentation datasets available to work on.

    Examples:
        # Find 20 unclaimed minimal datasets
        python -m science_card_improvement.cli.collaborate find-minimal
        python -m science_card_improvement.cli.collaborate find-minimal --limit 50 --no-exclude-claimed
        # Find all minimal datasets including claimed ones
        python -m science_card_improvement.cli.collaborate find-minimal --limit 50 --no-exclude-claimed
    """
    console.print(
        Panel.fit(
            "[bold cyan]Finding Minimal Documentation Datasets[/bold cyan]\n"
            f"Searching for datasets with minimal or no documentation",
            border_style="cyan"
        )
    )

    async def run_find():
        async with PortalStatusManager() as manager:
            return await manager.search_minimal_datasets(
                limit=limit,
                exclude_claimed=exclude_claimed
            )

    try:
        datasets = asyncio.run(run_find())

        if not datasets:
            console.print("[yellow]No minimal datasets found.[/yellow]")
            return

        # Display results
        table = Table(
            title="Minimal Documentation Datasets",
            show_lines=True,
            header_style="bold cyan"
        )

        table.add_column("#", style="dim")
        table.add_column("Dataset", style="blue", no_wrap=True)
        table.add_column("Downloads", justify="right", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Status", style="cyan")

        for i, dataset in enumerate(datasets[:limit], 1):
            status = "Available" if dataset.get("available", True) else "Claimed"
            table.add_row(
                str(i),
                dataset.get("id", "Unknown"),
                str(dataset.get("number_of_downloads", 0)),
                dataset.get("storage_size", "N/A"),
                status
            )

        console.print(table)

        console.print(f"\n[bold]Found {len(datasets)} minimal datasets[/bold]")
        if exclude_claimed:
            console.print("All shown datasets are available to claim")
        console.print("\nTo claim a dataset, use:")
        console.print("python -m science_card_improvement.cli.collaborate claim --user-id YOUR_ID")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--user-id",
    required=True,
    help="Your Hugging Face user ID"
)
@click.option(
    "--dataset-id",
    required=True,
    help="Dataset that was improved"
)
@click.option(
    "--pr-url",
    required=True,
    help="Pull request URL with improvements"
)
def complete(user_id: str, dataset_id: str, pr_url: str):
    """Mark a dataset as completed with improvement results.

    This interactive command guides you through marking a dataset complete
    and recording the improvements made.

    Examples:
        python -m science_card_improvement.cli.collaborate complete --user-id myusername --dataset-id org/dataset --pr-url https://...
    """
    console.print(
        Panel.fit(
            f"[bold green]Completing Dataset Improvement[/bold green]\n"
            f"Dataset: {dataset_id}\n"
            f"PR: {pr_url}",
            border_style="green"
        )
    )

    # Analyze the dataset to get before/after scores
    console.print("\nAnalyzing dataset improvement...")
    analyzer = BaselineAnalyzer()

    try:
        current_analysis = analyzer.analyze_card(dataset_id)
        current_score = current_analysis.quality_score

        console.print(f"Current documentation score: [cyan]{current_score:.1f}/100[/cyan]")

        # Get improvement details interactively
        estimated_score = float(Prompt.ask(
            "Estimated score after improvements",
            default=str(min(current_score + 30, 80))
        ))

        console.print("\nWhat improvements were made? (enter each, empty line to finish)")
        improvements = []
        while True:
            improvement = Prompt.ask("Improvement", default="")
            if not improvement:
                break
            improvements.append(improvement)

        if not improvements:
            improvements = ["General documentation improvements"]

        # Confirm before marking complete
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"Dataset: {dataset_id}")
        console.print(f"Score: {current_score:.1f} → {estimated_score:.1f} (+{estimated_score - current_score:.1f})")
        console.print(f"Improvements: {', '.join(improvements)}")
        console.print(f"PR: {pr_url}")

        if not Confirm.ask("\nMark this dataset as completed?"):
            console.print("[yellow]Cancelled[/yellow]")
            return

        # Mark as complete
        async def run_complete():
            async with PortalStatusManager(user_id) as manager:
                return await manager.complete_work(
                    dataset_id=dataset_id,
                    pr_url=pr_url,
                    before_score=current_score,
                    after_score=estimated_score,
                    improvements=improvements
                )

        success = asyncio.run(run_complete())

        if success:
            console.print(f"\n[green]Successfully marked {dataset_id} as completed![/green]")
            console.print(f"Score improvement: +{estimated_score - current_score:.1f} points")
            console.print("\nThank you for your contribution to improving scientific dataset documentation!")
        else:
            console.print("[red]Failed to mark as complete.[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


if __name__ == "__main__":
    cli()