# Discovery System Configuration Guide

## Overview

The Science Card Improvement Project uses an advanced discovery system with 192 comprehensive science keywords to find datasets and models across all scientific domains on Hugging Face.

## Configuration Files

### `config/science_keywords.json`

Contains 192 carefully curated science keywords organized by domain:

```json
[
  "science", "scientific", "research", "experiment", "analysis", "laboratory", "lab",
  "biology", "biological", "bio", "life science", "genomics", "genome", "genetics",
  "gene", "dna", "rna", "protein", "proteomics", "proteome",
  "molecular", "biochemistry", "biophysics", "bioengineering", "biotechnology",
  "biotech", "biomedical", "biomedicine",
  ...
]
```

**Keyword Categories:**
- **Core Scientific Terms**: science, research, experiment, analysis
- **Life Sciences**: biology, genomics, genetics, proteomics, molecular biology
- **Medical Sciences**: clinical, pathology, oncology, immunology, pharmacology
- **Physical Sciences**: physics, chemistry, materials science, nanotechnology
- **Earth Sciences**: geology, climate, oceanography, environmental science
- **Specialized Fields**: neuroscience, bioinformatics, forensic science

### Discovery Logic Configuration

Located in `src/core/discovery.py`:

```python
# Intelligent keyword handling
per_keyword_limit = max(10, min(100, limit // max(1, len(keywords))))
```

**Adaptive Limits:**
- **Minimum**: 10 results per keyword (ensures good coverage)
- **Maximum**: 100 results per keyword (prevents API overload)
- **Calculation**: `max(10, min(100, total_limit ÷ keyword_count))`

## Performance Optimization

### Parallel Processing
- **ThreadPoolExecutor**: Concurrent API calls for all keywords
- **Worker Threads**: Configurable via `discovery_max_workers` setting
- **Timeout Handling**: 30-second timeout per keyword search

### Deduplication
- **Repository ID tracking**: Prevents duplicate entries across keyword searches
- **Memory efficient**: Uses sets for O(1) lookup performance
- **Cross-keyword filtering**: Ensures unique results regardless of keyword overlap

### Error Handling
- **Graceful degradation**: Continues discovery even if some keywords fail
- **Comprehensive logging**: Tracks API calls, errors, and performance metrics
- **Rate limiting**: Respects Hugging Face API limits

## CLI Configuration

### Default Parameters (Updated)

**Discovery CLI** (`src/cli/discover.py`):
```python
@click.option("--limit", default=200)  # Increased from 100
```

**Find Datasets Script** (`find_datasets.py`):
```python
limit=200  # Comprehensive search limit
keywords=None  # Uses all 192 science keywords
```

### Usage Examples

```bash
# Use all 192 keywords with default limit (200)
python -m src.cli.discover

# Increase limit for maximum coverage
python -m src.cli.discover --limit 500

# Focus on specific domain (overrides keyword list)
python -m src.cli.discover --keywords genomics biology medical

# Verbose output with performance metrics
python -m src.cli.discover --limit 200 --verbose
```

## Configuration Tuning

### For Large-Scale Discovery
```python
# Increase limits for comprehensive coverage
total_limit = 1000
per_keyword_limit = max(10, min(50, total_limit // len(keywords)))
```

### For Fast Discovery
```python
# Reduce limits for quick results
total_limit = 50
per_keyword_limit = max(5, min(20, total_limit // len(keywords)))
```

### Custom Keyword Sets

To use custom keywords, modify `config/science_keywords.json`:

```json
[
  "your_custom_keyword1",
  "your_custom_keyword2",
  "domain_specific_term"
]
```

## Monitoring and Metrics

### Performance Tracking
- **Total discovered**: Number of unique repositories found
- **API calls**: Total Hugging Face API requests made
- **Cache hits**: Number of cached results used
- **Errors**: Failed keyword searches
- **Duration**: Total discovery time

### Quality Metrics
- **Documentation scores**: 0-100 scale quality assessment
- **Improvement candidates**: Repositories needing better documentation
- **Success rate**: Percentage of high-quality discoveries

## Best Practices

### Keyword Management
1. **Domain Coverage**: Ensure all relevant scientific domains are represented
2. **Specificity Balance**: Mix broad terms (biology) with specific ones (genomics)
3. **Avoid Duplicates**: Remove redundant or overly similar keywords
4. **Regular Updates**: Add emerging scientific terms and domains

### Performance Optimization
1. **Limit Tuning**: Balance comprehensiveness with speed
2. **Parallel Workers**: Adjust based on system capabilities
3. **Cache Usage**: Enable caching for repeated searches
4. **Error Monitoring**: Track and address frequent failures

### Quality Assurance
1. **Baseline Validation**: Regular checks against known good/bad examples
2. **Score Calibration**: Ensure scoring system reflects actual quality
3. **Human Review**: Always require human approval for improvements
4. **Continuous Learning**: Update criteria based on community feedback

## Troubleshooting

### Common Issues

**Low Discovery Count:**
- Check keyword relevance and specificity
- Verify API token and rate limits
- Increase per-keyword limits

**High Error Rate:**
- Monitor API response codes
- Check network connectivity
- Validate keyword formatting

**Poor Quality Results:**
- Review scoring criteria
- Update baseline examples
- Refine keyword selection

**Performance Issues:**
- Reduce parallel workers
- Lower per-keyword limits
- Enable caching