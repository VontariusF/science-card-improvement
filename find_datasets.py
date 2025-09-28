#!/usr/bin/env python3
"""
Quick script to find datasets on Hugging Face that need improvement.
"""

import asyncio

from science_card_improvement.analysis.baseline import BaselineAnalyzer
from science_card_improvement.discovery.repository import RepositoryDiscovery

async def find_datasets_needing_improvement():
    """Find and display datasets that need documentation improvement."""

    print("SEARCHING FOR DATASETS NEEDING IMPROVEMENT")
    print("=" * 50)

    # Initialize discovery and analysis
    discovery = RepositoryDiscovery(cache_enabled=False)
    analyzer = BaselineAnalyzer(cache_enabled=False)

    # Search for science datasets with all science keywords
    print("Searching for science datasets...")
    repos = await discovery.discover_repositories(
        repo_type='dataset',
        limit=200,  # Increased limit for comprehensive search
        # keywords=None means it will use all science keywords from config
    )

    print(f"Found {len(repos)} datasets. Analyzing documentation quality...\n")

    # Analyze each repository
    datasets_needing_help = []

    for i, repo in enumerate(repos, 1):
        try:
            print(f"[{i}/{len(repos)}] Analyzing {repo.repo_id}...")

            # Analyze the card
            analysis = analyzer.analyze_card(repo.repo_id, repo.repo_type)

            # Determine if needs improvement
            needs_improvement = (
                analysis.quality_score < 50 or
                analysis.total_length < 1000 or
                len(analysis.sections) < 5
            )

            status = "NEEDS HELP" if needs_improvement else "OK"

            print(f"  Score: {analysis.quality_score:.1f}/100")
            print(f"  Length: {analysis.total_length:,} characters")
            print(f"  Sections: {len(analysis.sections)}")
            print(f"  Status: {status}")

            if needs_improvement:
                datasets_needing_help.append({
                    'repo_id': repo.repo_id,
                    'score': analysis.quality_score,
                    'length': analysis.total_length,
                    'sections': len(analysis.sections),
                    'weaknesses': analysis.weaknesses[:3],  # Top 3 issues
                })

            print()

        except Exception as e:
            print(f"  ERROR analyzing: {str(e)[:80]}...")
            print()

    # Display summary
    print("SUMMARY")
    print("=" * 50)
    print(f"Total datasets analyzed: {len(repos)}")
    print(f"Datasets needing improvement: {len(datasets_needing_help)}")
    print(f"Success rate: {((len(repos) - len(datasets_needing_help)) / len(repos) * 100):.1f}%")

    if datasets_needing_help:
        print("\nTOP CANDIDATES FOR IMPROVEMENT:")
        print("-" * 50)

        # Sort by score (worst first)
        for i, item in enumerate(sorted(datasets_needing_help, key=lambda x: x['score'])[:5], 1):
            print(f"{i}. {item['repo_id']}")
            print(f"   Score: {item['score']:.1f}/100")
            print(f"   Length: {item['length']:,} chars")
            print(f"   Sections: {item['sections']}")

            if item['weaknesses']:
                print(f"   Issues: {', '.join(item['weaknesses'][:2])}")

            # Show comparison with examples
            if item['score'] < 5:
                print(f"   Similar to: arcinstitute/opengenome2 (extremely minimal)")
            elif item['score'] < 25:
                print(f"   Much worse than: tahoebio/Tahoe-100M (comprehensive)")

            print()

    print("NEXT STEPS:")
    print("-" * 50)
    print("1. Pick a dataset from the list above")
    print("2. Run: python -c \"from science_card_improvement.analysis.baseline import BaselineAnalyzer; analyzer = BaselineAnalyzer(); comparison = analyzer.compare_with_baselines('REPO_ID'); print('Quality gap:', comparison['comparison_with_gold_standards'])\"")
    print("3. Use the human review system to propose improvements")
    print("4. NEVER auto-submit - always review manually!")

if __name__ == "__main__":
    try:
        asyncio.run(find_datasets_needing_improvement())
    except KeyboardInterrupt:
        print("\nSearch cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")