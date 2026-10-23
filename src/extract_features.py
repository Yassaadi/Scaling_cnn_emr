"""Distributed image feature extraction with PySpark and MobileNetV2.

Reads JPEG images (one sub-folder per class), extracts 1,280-dimensional embeddings
with a pre-trained MobileNetV2 inside a pandas UDF, then standardises them and
reduces them with PCA. Runs unchanged on a laptop or on an AWS EMR cluster:

    # local, using every core as a worker
    spark-submit --master "local[*]" src/extract_features.py --input data/sample --output output

    # EMR (see emr/run_on_emr.sh)
    spark-submit src/extract_features.py --input s3://my-bucket/images --output s3://my-bucket/results
"""

from __future__ import annotations

import argparse
import io
import os
from collections.abc import Iterator

import numpy as np
import pandas as pd
from PIL import Image
from pyspark.ml.feature import PCA, StandardScaler
from pyspark.ml.functions import array_to_vector, vector_to_array
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType

IMAGE_SIZE = (224, 224)
# Set to "none" to use random weights (smoke tests without downloading ImageNet weights).
WEIGHTS = os.environ.get("MOBILENET_WEIGHTS", "imagenet")


def build_model(weights: str | None = None):
    """MobileNetV2 without its classification head: outputs a 1,280-d embedding."""
    from tensorflow.keras import Model
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2

    weights = weights or WEIGHTS
    base = MobileNetV2(weights=None if weights == "none" else weights, include_top=True, input_shape=(224, 224, 3))
    base.trainable = False
    return Model(inputs=base.input, outputs=base.layers[-2].output)


def preprocess(content: bytes) -> np.ndarray:
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img = Image.open(io.BytesIO(content)).convert("RGB").resize(IMAGE_SIZE)
    return preprocess_input(np.asarray(img, dtype=np.float32))


def make_featurizer(spark: SparkSession):
    """pandas UDF that loads the model once per executor task and embeds images in batches."""
    weights = spark.sparkContext.broadcast(build_model().get_weights())

    @F.pandas_udf(ArrayType(FloatType()))
    def featurize(batches: Iterator[pd.Series]) -> Iterator[pd.Series]:
        model = build_model(weights="none")
        model.set_weights(weights.value)
        for content in batches:
            embeddings = model.predict(np.stack(content.map(preprocess)), verbose=0)
            yield pd.Series(list(embeddings.astype(np.float32)))

    return featurize


def load_images(spark: SparkSession, path: str) -> DataFrame:
    images = (
        spark.read.format("binaryFile")
        .option("pathGlobFilter", "*.jpg")
        .option("recursiveFileLookup", "true")
        .load(path)
    )
    return images.withColumn("label", F.element_at(F.split("path", "/"), -2))


def reduce_dimensions(features: DataFrame, k: int) -> tuple[DataFrame, list[float]]:
    """Standardise embeddings and project them on the first k principal components."""
    vectors = features.withColumn("vector", array_to_vector("features"))
    scaled = StandardScaler(inputCol="vector", outputCol="scaled", withMean=True, withStd=True).fit(vectors)
    vectors = scaled.transform(vectors)
    pca = PCA(k=k, inputCol="scaled", outputCol="pca").fit(vectors)
    reduced = pca.transform(vectors).select("path", "label", vector_to_array("pca").alias("pca_features"))
    return reduced, pca.explainedVariance.toArray().tolist()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="folder of images, one sub-folder per class (local or s3://)")
    parser.add_argument("--output", required=True, help="output folder (local or s3://)")
    parser.add_argument("--pca-k", type=int, default=20, help="number of principal components")
    parser.add_argument("--partitions", type=int, default=24, help="parallelism for feature extraction")
    args = parser.parse_args(argv)

    spark = SparkSession.builder.appName("fruit-image-features").getOrCreate()
    spark.conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "64")

    images = load_images(spark, args.input)
    featurize = make_featurizer(spark)
    features = images.repartition(args.partitions).select("path", "label", featurize("content").alias("features"))
    features.write.mode("overwrite").parquet(f"{args.output}/features")

    features = spark.read.parquet(f"{args.output}/features")
    reduced, variance = reduce_dimensions(features, args.pca_k)
    reduced.write.mode("overwrite").parquet(f"{args.output}/pca")

    n = features.count()
    print(f"Images processed: {n}")
    print(f"Explained variance, first {args.pca_k} components: {sum(variance):.1%}")
    spark.stop()


if __name__ == "__main__":
    main()
