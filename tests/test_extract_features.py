import numpy as np
import pandas as pd
import pytest
from PIL import Image

pyspark = pytest.importorskip("pyspark")


@pytest.fixture(scope="module")
def image_dir(tmp_path_factory):
    root = tmp_path_factory.mktemp("images")
    rng = np.random.default_rng(0)
    for label, colour in {"apple": (200, 30, 30), "banana": (230, 220, 40)}.items():
        (root / label).mkdir()
        for i in range(8):
            pixels = np.clip(np.array(colour) + rng.normal(0, 25, (96, 96, 3)), 0, 255).astype("uint8")
            Image.fromarray(pixels).save(root / label / f"{i}.jpg")
    return root


def test_preprocess_returns_model_ready_array(image_dir):
    from extract_features import preprocess

    arr = preprocess((image_dir / "apple" / "0.jpg").read_bytes())
    assert arr.shape == (224, 224, 3)
    assert -1.0 <= arr.min() and arr.max() <= 1.0  # MobileNetV2 scaling


def test_pipeline_end_to_end(image_dir, tmp_path, monkeypatch):
    from pyspark.sql import SparkSession

    import extract_features

    monkeypatch.setattr(extract_features, "WEIGHTS", "none")  # no ImageNet download in CI
    spark = SparkSession.builder.master("local[2]").appName("test").getOrCreate()
    spark.sparkContext.addPyFile(extract_features.__file__)  # make the module importable on workers
    extract_features.main(["--input", str(image_dir), "--output", str(tmp_path), "--pca-k", "3", "--partitions", "2"])

    features = pd.read_parquet(tmp_path / "features")
    pca = pd.read_parquet(tmp_path / "pca")
    assert len(features) == 16 and set(features["label"]) == {"apple", "banana"}
    assert len(features["features"].iloc[0]) == 1280
    assert len(pca["pca_features"].iloc[0]) == 3
