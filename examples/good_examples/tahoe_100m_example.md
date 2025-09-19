# Tahoe-100M: A Large-Scale Dataset for Computer Vision Research

**Short description:** Tahoe-100M is a comprehensive dataset containing 100 million images with detailed annotations for computer vision research, including object detection, classification, and segmentation tasks.

## Motivation

This dataset was created to address the need for large-scale, diverse image data for training modern computer vision models. Existing datasets often lack the scale and diversity needed for robust model training, particularly for underrepresented regions and scenarios.

## Data Sources and Collection

### Original Sources
- Images collected from publicly available sources
- Diverse geographic and cultural representation
- Multiple image types and resolutions

### Collection Process
- Automated collection using web scraping
- Manual verification and quality control
- Ethical review and approval process

## Dataset Structure

### Overview
- **Total Size**: 100 million images
- **Number of Classes**: 10,000 object categories
- **Splits**: Train (80M), Validation (10M), Test (10M)
- **Average Resolution**: 512x512 pixels

### Data Format
- Images in JPEG format
- Annotations in COCO format
- Metadata in JSON format

## Usage

### Loading the Dataset
```python
from datasets import load_dataset

# Load the full dataset
dataset = load_dataset("tahoebio/Tahoe-100M")

# Load specific splits
train_data = load_dataset("tahoebio/Tahoe-100M", split="train")
test_data = load_dataset("tahoebio/Tahoe-100M", split="test")
```

## License

This dataset is released under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{tahoe100m,
  title={Tahoe-100M: A Large-Scale Dataset for Computer Vision Research},
  author={Tahoe Research Team},
  year={2024},
  url={https://huggingface.co/datasets/tahoebio/Tahoe-100M}
}
```

## Limitations and Ethical Considerations

### Known Limitations
- Some images may contain copyrighted material
- Geographic distribution may not be perfectly balanced
- Image quality varies across different sources

### Ethical Considerations
- Images were collected from publicly available sources
- Privacy considerations were addressed during collection
- Bias mitigation strategies were implemented

## Contact

- **Maintainer**: Tahoe Research Team
- **Email**: contact@tahoebio.com
- **Institution**: Tahoe Bio Research Institute
