class Detector:
    def __init__(self, model_name: str = "efficient-lite"):
        self.model_name = model_name

    def predict(self, image_path: str) -> dict:
        # Placeholder inference: in real lib, load model and run
        return {
            "image": image_path,
            "model": self.model_name,
            "detections": [
                {"label": "person", "confidence": 0.91, "bbox": [10, 20, 200, 300]},
                {"label": "bottle", "confidence": 0.78, "bbox": [300, 120, 360, 210]}
            ]
        }
