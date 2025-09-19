"""Human review and confirmation system for all changes before pushing."""

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from src.config.settings import get_settings
from src.utils.logger import LoggerMixin


@dataclass
class ChangeProposal:
    """Represents a proposed change to a repository."""

    repo_id: str
    repo_type: str
    change_type: str  # "create", "update", "append"
    file_path: str
    original_content: Optional[str]
    proposed_content: str
    summary: str
    improvements: List[str]
    risks: List[str]
    confidence_score: float
    created_at: datetime
    reviewed: bool = False
    approved: bool = False
    reviewer_notes: str = ""


class HumanReviewSystem(LoggerMixin):
    """System for managing human review of all proposed changes."""

    def __init__(self, auto_save: bool = True):
        """Initialize the human review system.

        Args:
            auto_save: Automatically save proposals to disk
        """
        self.settings = get_settings()
        self.console = Console()
        self.auto_save = auto_save
        self.proposals_dir = self.settings.output_dir / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

        # Track current session
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.pending_proposals: List[ChangeProposal] = []
        self.reviewed_proposals: List[ChangeProposal] = []

    def create_proposal(
        self,
        repo_id: str,
        repo_type: str,
        file_path: str,
        proposed_content: str,
        original_content: Optional[str] = None,
        summary: str = "",
        improvements: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        confidence_score: float = 0.0,
    ) -> ChangeProposal:
        """Create a new change proposal for review.

        Args:
            repo_id: Repository ID
            repo_type: Repository type (dataset/model)
            file_path: File to be changed (usually README.md)
            proposed_content: The new content
            original_content: Original content if updating
            summary: Summary of changes
            improvements: List of improvements made
            risks: Potential risks or concerns
            confidence_score: AI confidence in the changes (0-1)

        Returns:
            Created proposal
        """
        change_type = "create" if original_content is None else "update"

        proposal = ChangeProposal(
            repo_id=repo_id,
            repo_type=repo_type,
            change_type=change_type,
            file_path=file_path,
            original_content=original_content,
            proposed_content=proposed_content,
            summary=summary or "Card improvement proposal",
            improvements=improvements or [],
            risks=risks or [],
            confidence_score=confidence_score,
            created_at=datetime.utcnow(),
        )

        self.pending_proposals.append(proposal)

        if self.auto_save:
            self._save_proposal(proposal)

        self.log_info(f"Created proposal for {repo_id}", proposal_id=id(proposal))
        return proposal

    def review_proposal(
        self,
        proposal: ChangeProposal,
        interactive: bool = True,
        show_diff: bool = True,
    ) -> bool:
        """Review a proposal interactively or programmatically.

        Args:
            proposal: Proposal to review
            interactive: Use interactive CLI review
            show_diff: Show diff between original and proposed

        Returns:
            Whether the proposal was approved
        """
        if interactive:
            return self._interactive_review(proposal, show_diff)
        else:
            return self._programmatic_review(proposal)

    def _interactive_review(self, proposal: ChangeProposal, show_diff: bool) -> bool:
        """Interactive CLI review of a proposal."""
        self.console.clear()

        # Show header
        self.console.print(
            Panel.fit(
                f"[bold blue]Review Proposal for {proposal.repo_id}[/bold blue]",
                border_style="blue",
            )
        )

        # Show summary table
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Repository", proposal.repo_id)
        table.add_row("Type", proposal.repo_type)
        table.add_row("Change Type", proposal.change_type)
        table.add_row("File", proposal.file_path)
        table.add_row("Confidence", f"{proposal.confidence_score:.0%}")
        table.add_row("Created", proposal.created_at.strftime("%Y-%m-%d %H:%M"))

        self.console.print(table)
        self.console.print()

        # Show improvements
        if proposal.improvements:
            self.console.print("[bold green]Improvements:[/bold green]")
            for imp in proposal.improvements:
                self.console.print(f"  ✅ {imp}")
            self.console.print()

        # Show risks
        if proposal.risks:
            self.console.print("[bold yellow]Potential Risks:[/bold yellow]")
            for risk in proposal.risks:
                self.console.print(f"  ⚠️ {risk}")
            self.console.print()

        # Show content or diff
        if show_diff and proposal.original_content:
            self._show_diff(proposal.original_content, proposal.proposed_content)
        else:
            self._show_proposed_content(proposal.proposed_content)

        # Get user decision
        self.console.print("\n[bold]Review Options:[/bold]")
        self.console.print("  [green]A[/green] - Approve this change")
        self.console.print("  [yellow]E[/yellow] - Edit the proposed content")
        self.console.print("  [red]R[/red] - Reject this change")
        self.console.print("  [blue]S[/blue] - Skip for now")
        self.console.print("  [cyan]V[/cyan] - View full content")
        self.console.print("  [magenta]D[/magenta] - Download proposal for external review")

        while True:
            choice = Prompt.ask(
                "\nYour choice",
                choices=["a", "e", "r", "s", "v", "d"],
                default="s",
            ).lower()

            if choice == "a":
                # Approve
                proposal.reviewed = True
                proposal.approved = True
                notes = Prompt.ask("Add review notes (optional)", default="")
                proposal.reviewer_notes = notes
                self.reviewed_proposals.append(proposal)
                self.console.print("[green]✅ Proposal approved![/green]")
                return True

            elif choice == "e":
                # Edit
                edited_content = self._edit_content(proposal.proposed_content)
                if edited_content != proposal.proposed_content:
                    proposal.proposed_content = edited_content
                    self.console.print("[yellow]Content updated. Reviewing again...[/yellow]")
                    return self._interactive_review(proposal, show_diff)

            elif choice == "r":
                # Reject
                proposal.reviewed = True
                proposal.approved = False
                reason = Prompt.ask("Reason for rejection")
                proposal.reviewer_notes = f"Rejected: {reason}"
                self.reviewed_proposals.append(proposal)
                self.console.print("[red]❌ Proposal rejected.[/red]")
                return False

            elif choice == "s":
                # Skip
                self.console.print("[yellow]Skipped for now.[/yellow]")
                return False

            elif choice == "v":
                # View full content
                self._show_proposed_content(proposal.proposed_content, full=True)

            elif choice == "d":
                # Download
                file_path = self._export_proposal(proposal)
                self.console.print(f"[cyan]Proposal exported to: {file_path}[/cyan]")

    def _show_diff(self, original: str, proposed: str) -> None:
        """Show diff between original and proposed content."""
        import difflib

        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile="original",
            tofile="proposed",
            n=3,
        )

        diff_text = "".join(diff)

        if len(diff_text) > 5000:
            # For large diffs, show summary
            self.console.print("[yellow]Large diff detected. Showing summary:[/yellow]")
            lines_added = diff_text.count("\n+")
            lines_removed = diff_text.count("\n-")
            self.console.print(f"  Lines added: {lines_added}")
            self.console.print(f"  Lines removed: {lines_removed}")

            if Confirm.ask("Show full diff?", default=False):
                self.console.print(Syntax(diff_text, "diff", theme="monokai"))
        else:
            self.console.print(Syntax(diff_text, "diff", theme="monokai"))

    def _show_proposed_content(self, content: str, full: bool = False) -> None:
        """Show proposed content."""
        if not full and len(content) > 2000:
            # Show truncated version
            truncated = content[:2000] + "\n\n[... truncated ...]"
            self.console.print(Panel(Markdown(truncated), title="Proposed Content (Preview)"))
        else:
            self.console.print(Panel(Markdown(content), title="Proposed Content"))

    def _edit_content(self, content: str) -> str:
        """Open content in editor for manual editing."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            delete=False,
            encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Open in default editor
        click.edit(filename=tmp_path)

        # Read back edited content
        with open(tmp_path, "r", encoding="utf-8") as f:
            edited = f.read()

        Path(tmp_path).unlink()  # Clean up temp file
        return edited

    def _programmatic_review(self, proposal: ChangeProposal) -> bool:
        """Programmatic review based on rules and thresholds."""
        # Never auto-approve by default
        self.log_warning(
            "Programmatic review requested but auto-approval is disabled",
            repo_id=proposal.repo_id
        )
        return False

    def review_all_pending(self) -> Tuple[int, int]:
        """Review all pending proposals interactively.

        Returns:
            Tuple of (approved_count, rejected_count)
        """
        approved = 0
        rejected = 0

        total = len(self.pending_proposals)

        for i, proposal in enumerate(self.pending_proposals[:], 1):
            self.console.print(f"\n[bold]Reviewing proposal {i}/{total}[/bold]")

            if self.review_proposal(proposal):
                approved += 1
                self.pending_proposals.remove(proposal)
            else:
                rejected += 1

            if i < total:
                if not Confirm.ask("Continue to next proposal?", default=True):
                    break

        return approved, rejected

    def create_pr_draft(self, proposal: ChangeProposal) -> Dict[str, Any]:
        """Create a PR draft from an approved proposal.

        This creates a draft but DOES NOT submit it automatically.

        Args:
            proposal: Approved proposal

        Returns:
            PR draft information
        """
        if not proposal.approved:
            raise ValueError("Cannot create PR from unapproved proposal")

        pr_draft = {
            "repo_id": proposal.repo_id,
            "repo_type": proposal.repo_type,
            "title": f"Improve {proposal.repo_type} card documentation",
            "description": self._generate_pr_description(proposal),
            "branch": f"improve-card-{proposal.repo_id.replace('/', '-')}-{self.session_id}",
            "changes": [
                {
                    "path": proposal.file_path,
                    "content": proposal.proposed_content,
                    "action": proposal.change_type,
                }
            ],
            "created_at": datetime.utcnow().isoformat(),
            "auto_submit": False,  # NEVER auto-submit
            "requires_confirmation": True,
        }

        # Save draft for manual submission
        draft_path = self.proposals_dir / f"pr_draft_{proposal.repo_id.replace('/', '_')}_{self.session_id}.json"
        with open(draft_path, "w") as f:
            json.dump(pr_draft, f, indent=2)

        self.console.print(
            Panel(
                f"[green]PR draft created and saved to:[/green]\n{draft_path}\n\n"
                "[yellow]⚠️ This draft has NOT been submitted.[/yellow]\n"
                "To submit, use: sci-submit --draft-file <path>",
                title="PR Draft Created",
                border_style="green",
            )
        )

        return pr_draft

    def _generate_pr_description(self, proposal: ChangeProposal) -> str:
        """Generate PR description from proposal."""
        description = f"""## Summary

This PR improves the {proposal.repo_type} card documentation based on automated analysis and comparison with exemplary repositories.

## Changes Made

{proposal.summary}

## Improvements

"""
        for imp in proposal.improvements:
            description += f"- ✅ {imp}\n"

        if proposal.reviewer_notes:
            description += f"\n## Review Notes\n\n{proposal.reviewer_notes}\n"

        description += """
## Review Process

This change was:
1. Generated by the Science Card Improvement toolkit
2. Reviewed and approved by a human maintainer
3. Validated against best practices from repositories like tahoebio/Tahoe-100M

## References

- Poor example (before): [arcinstitute/opengenome2](https://huggingface.co/datasets/arcinstitute/opengenome2)
- Good example (target): [tahoebio/Tahoe-100M](https://huggingface.co/datasets/tahoebio/Tahoe-100M)

---
*Generated with Science Card Improvement Toolkit - All changes human-reviewed*
"""
        return description

    def _save_proposal(self, proposal: ChangeProposal) -> Path:
        """Save proposal to disk."""
        filename = f"proposal_{proposal.repo_id.replace('/', '_')}_{self.session_id}.json"
        filepath = self.proposals_dir / filename

        data = {
            "repo_id": proposal.repo_id,
            "repo_type": proposal.repo_type,
            "change_type": proposal.change_type,
            "file_path": proposal.file_path,
            "summary": proposal.summary,
            "improvements": proposal.improvements,
            "risks": proposal.risks,
            "confidence_score": proposal.confidence_score,
            "created_at": proposal.created_at.isoformat(),
            "reviewed": proposal.reviewed,
            "approved": proposal.approved,
            "reviewer_notes": proposal.reviewer_notes,
            "content_hash": hash(proposal.proposed_content),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        # Save content separately (can be large)
        content_file = filepath.with_suffix(".md")
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(proposal.proposed_content)

        return filepath

    def _export_proposal(self, proposal: ChangeProposal) -> Path:
        """Export proposal for external review."""
        export_dir = self.settings.output_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"proposal_export_{proposal.repo_id.replace('/', '_')}_{timestamp}.md"
        filepath = export_dir / filename

        export_content = f"""# Proposal for {proposal.repo_id}

**Generated**: {proposal.created_at}
**Type**: {proposal.change_type}
**Confidence**: {proposal.confidence_score:.0%}

## Summary

{proposal.summary}

## Improvements

"""
        for imp in proposal.improvements:
            export_content += f"- {imp}\n"

        export_content += f"""

## Proposed Content

```markdown
{proposal.proposed_content}
```

## Review Instructions

1. Review the proposed changes above
2. Check against the gold standard: https://huggingface.co/datasets/tahoebio/Tahoe-100M
3. Ensure factual accuracy and completeness
4. Approve or suggest modifications

---
*Science Card Improvement Toolkit*
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(export_content)

        return filepath

    def get_statistics(self) -> Dict[str, Any]:
        """Get review statistics for the current session."""
        return {
            "session_id": self.session_id,
            "pending_proposals": len(self.pending_proposals),
            "reviewed_proposals": len(self.reviewed_proposals),
            "approved": sum(1 for p in self.reviewed_proposals if p.approved),
            "rejected": sum(1 for p in self.reviewed_proposals if not p.approved),
            "approval_rate": (
                sum(1 for p in self.reviewed_proposals if p.approved) / len(self.reviewed_proposals)
                if self.reviewed_proposals else 0
            ),
        }