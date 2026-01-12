# Awesome Vision Lib

A lightweight edge-focused computer vision library for real-time object detection on constrained devices.

## Purpose
- Provide an easy API for capture → preprocess → inference → postprocess.
- Optimize for low-latency and low-power scenarios.

## Installation
```bash
pip install -r requirements.txt
```

## Quick Start
```python
from awesome_vision import Detector

model = Detector(model_name="efficient-lite")
result = model.predict("samples/frame.jpg")
print(result)
```

## API Surface
- `Detector(model_name: str)`
- `predict(image_path: str) -> dict`
- `load_weights(path: str)`

## Limitations
- English-only class labels
- Max image size 640x640

## License
MIT
