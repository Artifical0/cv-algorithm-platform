from pathlib import Path

from cv_algorithm_sdk import load_manifest
from cv_algorithm_sdk.server import create_algorithm_app
from yolo_algorithm.algorithm import YoloAlgorithm
from yolo_algorithm.settings import YoloSettings


BASE_DIR = Path(__file__).resolve().parent
manifest = load_manifest(BASE_DIR / "manifest.yaml")
app = create_algorithm_app(YoloAlgorithm(manifest, YoloSettings.from_environment()))
