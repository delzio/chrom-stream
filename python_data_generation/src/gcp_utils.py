from google.cloud import pubsub_v1
from google.cloud.storage.bucket import Bucket
from typing import Callable
import json
import os
import pandas as pd
import io

# GCP
CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
TOPIC_ID = "chrom-sensor-readings"   # name of topic
SUBSCRIPTION_ID = os.environ["PUBSUB_STREAMING_SUB_ID"]
publisher = pubsub_v1.PublisherClient(
    publisher_options=pubsub_v1.types.PublisherOptions(enable_message_ordering=True)
)

def publish(message: dict) -> None:
    """ Publish message formatted as dictionary to GCP Pub/Sub """

    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    ordering_key = message.get("chrom_unit", "default")

    future = publisher.publish(
        topic_path,
        json.dumps(message).encode("utf-8"),
        source="python_time_series_trend_generator",
        ordering_key=ordering_key
    )

    print(f"publishing data to pubsub: {message}")

def subscribe(callback_fn: Callable) -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"Listening for messages from: {subscription_path}")
    subscriber.subscribe(subscription_path, callback=callback_fn)

    # Keep process running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped")

def parquet_to_gcs(data: pd.DataFrame, gcs_file_path: str, bucket: Bucket, verbose: bool = True) -> None:
    """ Upload local parquet file to GCS bucket """
    
    # Create an in-memory bytes buffer
    buffer = io.BytesIO()
    data.to_parquet(buffer, index=False)

    # Reset buffer pointer before upload
    buffer.seek(0)

    # Upload to GCS bucket
    blob = bucket.blob(gcs_file_path)
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    if verbose:
        print(f"Uploaded {len(data)} rows to GCS at path: {gcs_file_path}")


def json_to_gcs(data: dict, gcs_file_path: str, bucket: Bucket, verbose: bool = True) -> None:
    """ Upload local json file to GCS bucket """

    json_str = json.dumps(data, indent=2)

    # Write JSON string to an in-memory binary buffer
    buffer = io.BytesIO(json_str.encode("utf-8"))

    # Reset buffer pointer before upload
    buffer.seek(0)

    # Upload to GCS bucket
    blob = bucket.blob(gcs_file_path)
    blob.upload_from_file(buffer, content_type="application/json")

    if verbose:
        print(f"Uploaded sample result json to GCS bucket: {data["sample_metadata"]}")


