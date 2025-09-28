"""CLI for baseline comparison and improvement workflow."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

from science_card_improvement.analysis.baseline import BaselineAnalyzer
from science_card_improvement.config.settings import get_settings
from science_card_improvement.exceptions.custom_exceptions import RepositoryNotFoundError
from science_card_improvement.review.human import HumanReviewSystem
from science_card_improvement.utils.logger import setup_logging


console = Console()
logger = setup_logging()


@click.group()
def cli():
    """Science Card Improvement - Baseline Comparison Tools."""
    pass


@cli.command()
@click.option(
    "--target",
    required=True,
    help="Target repository to analyze (e.g., arcinstitute/opengenome2)",
)
@click.option(
    "--baseline",
    default="tahoebio/Tahoe-100M",
    help="Baseline repository for comparison",
)
@click.option(
    "--repo-type",
    type=click.Choice(["dataset", "model"]),
    default="dataset",
    help="Repository type",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for comparison report",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "console"]),
    default="console",
    help="Output format",
)
@click.option(
    "--show-suggestions",
    is_flag=True,
    default=True,
    help="Show improvement suggestions",
)
def compare(
    target: str,
    baseline: str,
    repo_type: str,
    output: Optional[str],
    output_format: str,
    show_suggestions: bool,
):
    """Compare a repository against baseline examples.

    This command analyzes a target repository and compares it with known good
    (and bad) examples to identify improvements needed.

    Examples:

        # Compare Arc Institute's card with Tahoe Bio's excellent example
        sci-compare --target arcinstitute/opengenome2 --baseline tahoebio/Tahoe-100M

        # Generate a detailed report
        sci-compare --target my-org/my-dataset --output report.md --format markdown

        # Get JSON output for programmatic use
        sci-compare --target my-org/my-dataset --format json
    """
    console.print(
        Panel.fit(
            f"[bold blue]Baseline Comparison Analysis[/bold blue]\n"
            f"Target: {target}\n"
            f"Baseline: {baseline}",
            border_style="blue",
        )
    )

    try:
        # Initialize analyzer
        analyzer = BaselineAnalyzer()

        # Run comparison
        with console.status("[bold green]Analyzing repositories..."):
            comparison = analyzer.compare_with_baselines(target, repo_type)

        # Generate report
        if output_format == "json":
            report = json.dumps(comparison, indent=2)
        else:
            report = analyzer.generate_improvement_report(
                target,
                repo_type,
                output_format="markdown"
            )

        # Handle output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            console.print(f"[green]Report saved to {output_path}[/green]")

        # Display to console
        if output_format == "console" or not output:
            display_comparison_results(comparison, show_suggestions)
        elif output_format == "markdown":
            console.print(Markdown(report))

    except RepositoryNotFoundError as e:
        console.print(f"[red]Error: Repository '{target}' not found[/red]")
        raise click.Exit(1)
    except Exception as e:
        console.print(f"[red]Error during comparison: {e}[/red]")
        logger.error("Comparison failed", exception=e)
        raise click.Exit(1)


@cli.command()
@click.option(
    "--repo-id",
    required=True,
    help="Repository to analyze",
)
@click.option(
    "--repo-type",
    type=click.Choice(["dataset", "model"]),
    default="dataset",
    help="Repository type",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for analysis",
)
def analyze(repo_id: str, repo_type: str, output: Optional[str]):
    """Analyze a repository's documentation quality.

    Examples:
        sci-analyze --repo-id arcinstitute/opengenome2
        sci-analyze --repo-id bigscience/bloom --repo-type model
    """
    console.print(f"[bold]Analyzing {repo_id}...[/bold]")

    try:
        analyzer = BaselineAnalyzer()
        analysis = analyzer.analyze_card(repo_id, repo_type)

        # Display results
        display_analysis_results(analysis)

        # Save if requested
        if output:
            output_path = Path(output)
            with open(output_path, "w") as f:
                json.dump(analysis.to_dict(), f, indent=2)
            console.print(f"[green]Analysis saved to {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--poor-example",
    default="arcinstitute/opengenome2",
    help="Example of poor documentation",
)
@click.option(
    "--good-example",
    default="tahoebio/Tahoe-100M",
    help="Example of good documentation",
)
def show_examples(poor_example: str, good_example: str):
    """Show the difference between good and bad documentation examples.

    This command displays a side-by-side comparison of documentation quality.
    """
    console.print(
        Panel(
            "[bold]Documentation Quality Examples[/bold]\n\n"
            f"Poor Example: {poor_example}\n"
            f"Good Example: {good_example}",
            border_style="cyan",
        )
    )

    try:
        analyzer = BaselineAnalyzer()

        # Analyze both
        with console.status("Analyzing examples..."):
            poor_analysis = analyzer.analyze_card(poor_example)
            good_analysis = analyzer.analyze_card(good_example)

        # Create comparison table
        table = Table(
            title="Documentation Comparison",
            show_lines=True,
            header_style="bold cyan",
        )

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column(f"{poor_example}", style="red")
        table.add_column(f"{good_example}", style="green")

        # Add metrics
        table.add_row(
            "Quality Score",
            f"{poor_analysis.quality_score:.1f}/100",
            f"{good_analysis.quality_score:.1f}/100",
        )

        table.add_row(
            "Documentation Length",
            f"{poor_analysis.total_length:,} chars",
            f"{good_analysis.total_length:,} chars",
        )

        table.add_row(
            "Number of Sections",
            str(len(poor_analysis.sections)),
            str(len(good_analysis.sections)),
        )

        table.add_row(
            "Has Code Examples",
            "No" if not any(s.has_code_examples for s in poor_analysis.sections) else "Yes",
            "No" if not any(s.has_code_examples for s in good_analysis.sections) else "Yes",
        )

        table.add_row(
            "Has Citations",
            "No" if not any(s.has_citations for s in poor_analysis.sections) else "Yes",
            "No" if not any(s.has_citations for s in good_analysis.sections) else "Yes",
        )

        table.add_row(
            "Key Strengths",
            ", ".join(poor_analysis.strengths[:2]) if poor_analysis.strengths else "None",
            ", ".join(good_analysis.strengths[:2]) if good_analysis.strengths else "Many",
        )

        table.add_row(
            "Main Issues",
            ", ".join(poor_analysis.weaknesses[:2]) if poor_analysis.weaknesses else "None",
            ", ".join(good_analysis.weaknesses[:2]) if good_analysis.weaknesses else "Minor",
        )

        console.print(table)

        # Show key differences
        console.print("\n[bold]Key Differences:[/bold]")
        console.print(f"• Quality gap: {good_analysis.quality_score - poor_analysis.quality_score:.1f} points")
        console.print(f"• Length difference: {good_analysis.total_length - poor_analysis.total_length:,} characters")
        console.print(f"• The good example has {len(good_analysis.sections) - len(poor_analysis.sections)} more sections")

        # Show what makes the good example good
        console.print("\n[bold green]What makes {good_example} excellent:[/bold green]")
        for strength in good_analysis.strengths[:5]:
            console.print(f"  {strength}")

        # Show what's wrong with the poor example
        console.print(f"\n[bold red]What {poor_example} is missing:[/bold red]")
        for issue in poor_analysis.missing_elements[:5]:
            console.print(f"  {issue}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Exit(1)


@cli.command()
@click.option(
    "--list-only",
    is_flag=True,
    help="Just list the baseline repositories",
)
def baselines(list_only: bool):
    """Show or update baseline repositories.

    This command displays the current baseline repositories used for comparison.
    """
    analyzer = BaselineAnalyzer()

    if list_only:
        console.print("[bold]Gold Standard Repositories:[/bold]")
        for repo in analyzer.GOLD_STANDARD_REPOS:
            console.print(f"  {repo}")

        console.print("\n[bold]Poor Example Repositories:[/bold]")
        for repo in analyzer.POOR_EXAMPLE_REPOS:
            console.print(f"  {repo}")
    else:
        # Show detailed analysis of baselines
        console.print("[bold]Analyzing baseline repositories...[/bold]\n")

        for repo_id, analysis in analyzer.gold_standards.items():
            console.print(f"[bold green]{repo_id}[/bold green]")
            console.print(f"   Score: {analysis.quality_score:.1f}/100")
            console.print(f"   Sections: {len(analysis.sections)}")
            console.print(f"   Strengths: {', '.join(analysis.strengths[:3])}")
            console.print()

        for repo_id, analysis in analyzer.poor_examples.items():
            console.print(f"[bold red]{repo_id}[/bold red]")
            console.print(f"   Score: {analysis.quality_score:.1f}/100")
            console.print(f"   Issues: {', '.join(analysis.weaknesses[:3])}")
            console.print()


def display_comparison_results(comparison: dict, show_suggestions: bool):
    """Display comparison results in a formatted way."""
    target = comparison["target_analysis"]

    # Header
    console.print(
        Panel(
            f"[bold]Analysis Results[/bold]\n"
            f"Repository: {target['repo_id']}\n"
            f"Quality Score: {target['quality_score']:.1f}/100",
            border_style="cyan",
        )
    )

    # Strengths and weaknesses
    if target["strengths"]:
        console.print("\n[bold green]Strengths:[/bold green]")
        for strength in target["strengths"]:
            console.print(f"  {strength}")

    if target["weaknesses"]:
        console.print("\n[bold red]Weaknesses:[/bold red]")
        for weakness in target["weaknesses"]:
            console.print(f"  {weakness}")

    # Recommendations
    if show_suggestions and comparison["recommendations"]:
        console.print("\n[bold yellow]Priority Improvements:[/bold yellow]")
        for rec in comparison["recommendations"]:
            emoji = "HIGH" if rec["priority"] == "HIGH" else "MEDIUM"
            console.print(f"  {emoji} {rec['action']}")
            console.print(f"      Reference: {rec['reference']}")

    # Impact estimate
    impact = comparison["estimated_improvement_impact"]
    console.print(
        Panel(
            f"[bold]Estimated Impact[/bold]\n"
            f"Current Score: {impact['current_score']:.1f}\n"
            f"Potential Score: {impact['potential_score']:.1f}\n"
            f"Improvement: {impact['estimated_improvement']}\n"
            f"{impact['percentile_change']}",
            border_style="green",
        )
    )


def display_analysis_results(analysis):
    """Display analysis results in a formatted way."""
    # Create summary table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Quality Score", f"{analysis.quality_score:.1f}/100")
    table.add_row("Documentation Length", f"{analysis.total_length:,} characters")
    table.add_row("Number of Sections", str(len(analysis.sections)))

    console.print(table)

    # Show sections
    console.print("\n[bold]Sections Found:[/bold]")
    for section in analysis.sections[:10]:
        quality = "Good" if section.quality_score > 0.5 else "Needs Work"
        console.print(f"  {quality} {section.name} ({section.word_count} words)")

    # Show issues
    if analysis.missing_elements:
        console.print("\n[bold yellow]Missing Elements:[/bold yellow]")
        for element in analysis.missing_elements:
            console.print(f"  {element}")

    # Show suggestions
    if analysis.improvement_suggestions:
        console.print("\n[bold]Improvement Suggestions:[/bold]")
        for i, suggestion in enumerate(analysis.improvement_suggestions[:5], 1):
            console.print(f"  {i}. {suggestion}")


@cli.command()
@click.pass_context
def interactive(ctx):
    """Interactive baseline comparison workflow.

    This guides you through the entire process step by step.
    """
    console.print(
        Panel(
            "[bold cyan]Interactive Baseline Comparison Workflow[/bold cyan]\n\n"
            "This wizard will guide you through:\n"
            "1. Selecting a repository to improve\n"
            "2. Comparing with baselines\n"
            "3. Reviewing suggestions\n"
            "4. Creating improvement proposals",
            border_style="cyan",
        )
    )

    # Step 1: Get target repository
    target = click.prompt("Enter repository to analyze (e.g., arcinstitute/opengenome2)")

    # Step 2: Choose baseline
    console.print("\n[bold]Available baseline examples:[/bold]")
    console.print("1. tahoebio/Tahoe-100M (Excellent dataset card)")
    console.print("2. bigscience/bloom (Excellent model card)")
    console.print("3. Custom (enter your own)")

    baseline_choice = click.prompt("Choose baseline", type=int, default=1)
    if baseline_choice == 1:
        baseline = "tahoebio/Tahoe-100M"
    elif baseline_choice == 2:
        baseline = "bigscience/bloom"
    else:
        baseline = click.prompt("Enter custom baseline repository")

    # Step 3: Run comparison
    console.print(f"\n[bold]Comparing {target} with {baseline}...[/bold]")
    ctx.invoke(compare, target=target, baseline=baseline, show_suggestions=True)

    # Step 4: Ask if user wants to generate improvements
    if click.confirm("\nWould you like to generate improvement proposals?"):
        console.print("[yellow]Note: All proposals require human review before submission[/yellow]")
        # This would call the generate command
        console.print("[green]Use 'sci-generate' to create improvement proposals[/green]")


if __name__ == "__main__":
    cli()