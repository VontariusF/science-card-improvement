# {{ title }}

**Short description (TL;DR):** {{ short_description }}

## Motivation

{{ motivation }}

This dataset was created to {{ purpose }}. It addresses the need for {{ problem_statement }} in the {{ domain }} field.

## Data Sources and Collection

### Original Sources
{{ data_sources }}

### Collection Process
{{ collection_process }}

### Data Preprocessing
{{ preprocessing_steps }}

## Dataset Structure

### Overview
- **Total Size**: {{ total_size }}
- **Number of Samples**: {{ num_samples }}
- **Number of Features**: {{ num_features }}
- **Splits**: {{ splits }}

### Data Format
{{ data_format }}

### Sample Data
{{ sample_data }}

## Usage

### Loading the Dataset
```python
from datasets import load_dataset

# Load the full dataset
dataset = load_dataset("{{ repo_id }}")

# Load specific splits
train_data = load_dataset("{{ repo_id }}", split="train")
test_data = load_dataset("{{ repo_id }}", split="test")
```

### Basic Usage Example
```python
# Example usage code
{{ usage_example }}
```

## License

{{ license_info }}

**License Type**: {{ license_type }}

## Citation

If you use this dataset, please cite:

```bibtex
{{ citation_bibtex }}
```

**DOI**: {{ doi }}
**Publication**: {{ publication }}

## Limitations and Ethical Considerations

### Known Limitations
{{ limitations }}

### Potential Biases
{{ biases }}

### Ethical Considerations
{{ ethical_considerations }}

### Recommended Use Cases
{{ recommended_use_cases }}

### Use Cases to Avoid
{{ avoid_use_cases }}

## Contact and Maintainers

- **Maintainer**: {{ maintainer_name }}
- **Email**: {{ maintainer_email }}
- **Institution**: {{ institution }}

### Contributing
{{ contributing_info }}

### Issues and Support
{{ support_info }}
