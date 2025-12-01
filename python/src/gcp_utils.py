from google.cloud import pubsub_v1
from google.cloud.storage.bucket import Bucket
from typing import Callable
import json
import os
import pandas as pd

# GCP
CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
TOPIC_ID = "chrom-sensor-readings"   # name of topic
SUBSCRIPTION_ID = os.environ["PUBSUB_SUBSCRIPTION_ID"]
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

def parquet_to_gcs(data: pd.DataFrame, temp_file_path: str, gcs_file_path: str, bucket: Bucket, verbose: bool = True) -> None:
    """ Upload local parquet file to GCS bucket """

    data.to_parquet(temp_file_path, index=False)
    # upload to GCS batch bucket
    blob = bucket.blob(os.path.join(gcs_file_path, os.path.basename(temp_file_path)))
    blob.upload_from_filename(temp_file_path)
    if verbose:
        print(f"Uploaded data: {data} to GCS bucket")

def json_to_gcs(data: dict, temp_file_path: str, gcs_file_path: str, bucket: Bucket, verbose: bool = True) -> None:
    """ Upload local json file to GCS bucket """

    with open(temp_file_path, "w") as file:
        json.dump(data, file, indent=2)
    # upload to GCS batch bucket
    blob = bucket.blob(os.path.join(gcs_file_path, os.path.basename(temp_file_path)))
    blob.upload_from_filename(temp_file_path)
    if verbose:
        print(f"Uploaded json data (keys: {data.keys()}) to GCS bucket")


