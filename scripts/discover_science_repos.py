#!/usr/bin/env python3
"""
Science Repository Discovery Script

This script discovers science-related datasets and models on Hugging Face
that may need improved documentation cards.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import click
from rich.console import Console
from huggingface_hub import HfApi, DatasetInfo, ModelInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

@dataclass
class ScienceRepo:
    """Represents a science-related repository on Hugging Face."""
    id: str
    type: str  # 'dataset' or 'model'
    title: str
    description: str
    tags: List[str]
    downloads: int
    likes: int
    has_readme: bool
    readme_length: int

class ScienceRepoDiscovery:
    """Discovers and analyzes science repositories on Hugging Face."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the discovery client."""
        self.api = HfApi(token=token or os.getenv("HF_TOKEN"))
        self.science_keywords = [
            "science", "biology", "genomics", "chemistry", "physics", 
            "astronomy", "medicine", "medical", "clinical", "healthcare"
        ]
    
    def search_science_repos(self, repo_type: str, limit: int = 100) -> List[ScienceRepo]:
        """Search for science-related repositories."""
        repos = []
        
        if repo_type in ['dataset', 'both']:
            repos.extend(self._search_datasets(limit // 2 if repo_type == 'both' else limit))
        
        if repo_type in ['model', 'both']:
            repos.extend(self._search_models(limit // 2 if repo_type == 'both' else limit))
        
        return repos
    
    def _search_datasets(self, limit: int) -> List[ScienceRepo]:
        """Search for science datasets."""
        datasets = []
        seen_ids = set()
        
        for keyword in self.science_keywords[:5]:  # Limit for demo
            try:
                search_results = self.api.list_datasets(
                    search=keyword,
                    limit=min(10, limit // len(self.science_keywords[:5])),
                    full=True
                )
                
                for dataset_info in search_results:
                    if dataset_info.id in seen_ids:
                        continue
                    seen_ids.add(dataset_info.id)
                    
                    repo = self._convert_dataset_to_repo(dataset_info)
                    if repo:
                        datasets.append(repo)
                        
                    if len(datasets) >= limit:
                        break
                        
            except Exception as e:
                console.print(f"[red]Error searching for '{keyword}': {e}[/red]")
                continue
            
            if len(datasets) >= limit:
                break
        
        return datasets[:limit]
    
    def _search_models(self, limit: int) -> List[ScienceRepo]:
        """Search for science models."""
        models = []
        seen_ids = set()
        
        for keyword in self.science_keywords[:5]:  # Limit for demo
            try:
                search_results = self.api.list_models(
                    search=keyword,
                    limit=min(10, limit // len(self.science_keywords[:5])),
                    full=True
                )
                
                for model_info in search_results:
                    if model_info.id in seen_ids:
                        continue
                    seen_ids.add(model_info.id)
                    
                    repo = self._convert_model_to_repo(model_info)
                    if repo:
                        models.append(repo)
                        
                    if len(models) >= limit:
                        break
                        
            except Exception as e:
                console.print(f"[red]Error searching for '{keyword}': {e}[/red]")
                continue
            
            if len(models) >= limit:
                break
        
        return models[:limit]
    
    def _convert_dataset_to_repo(self, dataset_info: DatasetInfo) -> Optional[ScienceRepo]:
        """Convert DatasetInfo to ScienceRepo."""
        try:
            # Check if README exists and get length
            has_readme = False
            readme_length = 0
            
            try:
                readme_path = self.api.hf_hub_download(
                    repo_id=dataset_info.id,
                    filename="README.md",
                    repo_type="dataset"
                )
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    has_readme = True
                    readme_length = len(readme_content)
            except:
                pass
            
            return ScienceRepo(
                id=dataset_info.id,
                type="dataset",
                title=getattr(dataset_info, 'title', dataset_info.id),
                description=getattr(dataset_info, 'description', ''),
                tags=getattr(dataset_info, 'tags', []),
                downloads=getattr(dataset_info, 'downloads', 0),
                likes=getattr(dataset_info, 'likes', 0),
                has_readme=has_readme,
                readme_length=readme_length
            )
        except Exception as e:
            console.print(f"[red]Error converting dataset {dataset_info.id}: {e}[/red]")
            return None
    
    def _convert_model_to_repo(self, model_info: ModelInfo) -> Optional[ScienceRepo]:
        """Convert ModelInfo to ScienceRepo."""
        try:
            # Check if README exists and get length
            has_readme = False
            readme_length = 0
            
            try:
                readme_path = self.api.hf_hub_download(
                    repo_id=model_info.id,
                    filename="README.md",
                    repo_type="model"
                )
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    has_readme = True
                    readme_length = len(readme_content)
            except:
                pass
            
            return ScienceRepo(
                id=model_info.id,
                type="model",
                title=getattr(model_info, 'title', model_info.id),
                description=getattr(model_info, 'description', ''),
                tags=getattr(model_info, 'tags', []),
                downloads=getattr(model_info, 'downloads', 0),
                likes=getattr(model_info, 'likes', 0),
                has_readme=has_readme,
                readme_length=readme_length
            )
        except Exception as e:
            console.print(f"[red]Error converting model {model_info.id}: {e}[/red]")
            return None
    
    def save_results(self, repos: List[ScienceRepo], filename: str = "discovery_results.json"):
        """Save discovery results to a JSON file."""
        results = []
        for repo in repos:
            results.append({
                "id": repo.id,
                "type": repo.type,
                "title": repo.title,
                "description": repo.description,
                "tags": repo.tags,
                "downloads": repo.downloads,
                "likes": repo.likes,
                "has_readme": repo.has_readme,
                "readme_length": repo.readme_length
            })
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        console.print(f"[green]Results saved to {filename}[/green]")

@click.command()
@click.option('--type', 'repo_type', 
              type=click.Choice(['dataset', 'model', 'both']), 
              default='both',
              help='Type of repositories to search for')
@click.option('--limit', default=100, help='Maximum number of repositories to return')
@click.option('--output', default='discovery_results.json', help='Output file for results')
def main(repo_type: str, limit: int, output: str):
    """Discover science repositories on Hugging Face."""
    
    # Check for HF token
    if not os.getenv("HF_TOKEN"):
        console.print("[red]Error: HF_TOKEN environment variable not set[/red]")
        console.print("Please set your Hugging Face token:")
        console.print("export HF_TOKEN='your_token_here'")
        return
    
    console.print(f"[bold blue]Discovering {repo_type} repositories...[/bold blue]")
    
    # Initialize discovery client
    discovery = ScienceRepoDiscovery()
    
    # Search for repositories
    repos = discovery.search_science_repos(repo_type, limit)
    
    console.print(f"[green]Found {len(repos)} science repositories[/green]")
    
    # Save results
    discovery.save_results(repos, output)
    
    # Show summary
    dataset_count = sum(1 for repo in repos if repo.type == 'dataset')
    model_count = sum(1 for repo in repos if repo.type == 'model')
    no_readme_count = sum(1 for repo in repos if not repo.has_readme)
    short_readme_count = sum(1 for repo in repos if repo.has_readme and repo.readme_length < 300)
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Datasets: {dataset_count}")
    console.print(f"  Models: {model_count}")
    console.print(f"  No README: {no_readme_count}")
    console.print(f"  Short README (<300 chars): {short_readme_count}")
    console.print(f"  Total needing improvement: {no_readme_count + short_readme_count}")

if __name__ == "__main__":
    main()
