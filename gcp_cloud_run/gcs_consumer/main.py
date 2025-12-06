import os
import json
import pandas as pd
from typing import Callable
from google.cloud import pubsub_v1, storage
from google.cloud.storage.bucket import Bucket

# GCP CONFIG
CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
SUBSCRIPTION_ID = os.environ["PUBSUB_SUBSCRIPTION_ID"]
OUTPUT_DIR = os.environ["PYTHON_OUTPUT_DIR"]
GCS_BUCKET = os.environ["GCS_TREND_BUCKET"]
gcs_client = storage.Client()
BUCKET = gcs_client.bucket(GCS_BUCKET)

# INITIALIZE GLOBALS
BUFFER_TIME_LIMIT = 900 # 15 minutes
BUFFER_SIZE_LIMIT = 1000 # records
BUFFER = {}
last_timestamp_ns = {}
last_flow_rate = {}
totalized_volume_ml = {}

def main():

    # Start Pub/Sub subscription to receive events
    subscribe(callback_fn=process_message)

    return

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

def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """ Triggered automatically whenever a Pub/Sub message arrives """
    try:
        data = json.loads(message.data.decode("utf-8"))
        chrom_unit = data["chrom_unit"]

        # handle only new data for streaming
        if last_timestamp_ns.get(chrom_unit, 0) < int(data["time_ns"]):
            event = handle_event(data)

            if chrom_unit not in BUFFER:
                BUFFER[chrom_unit] = []
            BUFFER[chrom_unit].append(event)

            if len(BUFFER[chrom_unit]) >= BUFFER_SIZE_LIMIT:
                parquet_to_gcs(
                    data=pd.DataFrame(BUFFER[chrom_unit]),
                    gcs_file_path=f"raw/{chrom_unit}/{chrom_unit}_trends_{event['time_iso'].replace(':', '-')}.parquet",
                    bucket=BUCKET
                ) 
                BUFFER[chrom_unit] = []
        
        message.ack()
    except Exception as e:
        print(f"Error collecting data from pub/sub: {e}")

def handle_event(event: dict) -> None:
    """ Process individual event from Pub/Sub """
    global last_timestamp_ns, last_flow_rate, totalized_volume_ml

    # Calculate totalized volume
    chrom_unit = event["chrom_unit"]
    cur_ts = int(event["time_ns"])
    cur_flow = event["flow_mL_min"]

    last_ts = last_timestamp_ns.get(chrom_unit, None)
    last_flow = last_flow_rate.get(chrom_unit, 0)
    if chrom_unit not in totalized_volume_ml:
        totalized_volume_ml[chrom_unit] = 0.0

    if last_ts is not None and cur_ts < last_ts:
        print(f"Skipping out of order event for {chrom_unit}. Current TS: {cur_ts}, Last TS: {last_ts}")
        return

    if last_ts is not None:
        # Calculate time difference in minutes
        delta_min = (cur_ts - last_ts) / 1e9 / 60.0
        # Average flow rate between last and current
        avg_flow = (last_flow + cur_flow) / 2.0
        # Calculate volume added since last event
        delta_vol = avg_flow * delta_min
        totalized_volume_ml[chrom_unit] += delta_vol

    # Calculate totalized column volumes (assuming 226 L column volume)
    tot_col_vol = totalized_volume_ml[chrom_unit] / 1000.0 / 226 

    last_timestamp_ns[chrom_unit] = cur_ts
    last_flow_rate[chrom_unit] = cur_flow

    # Add calculations to event
    event["totalized_volume_ml"] = totalized_volume_ml[chrom_unit]
    event["totalized_column_volumes"] = tot_col_vol

    return event

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

if __name__ == "__main__":
    main()