import os
import json
import base64
import io
import pandas as pd
from flask import Flask, request
from google.cloud import storage
from google.cloud.storage.bucket import Bucket

# GCP CONFIG
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GCS_BUCKET = os.environ["GCP_TREND_BUCKET"]
gcs_client = storage.Client()
BUCKET = gcs_client.bucket(GCS_BUCKET)

# INITIALIZE GLOBALS
BUFFER_TIME_LIMIT = 900 # 15 minutes
BUFFER_SIZE_LIMIT = 1000 # records
BUFFER = {}
last_timestamp_ns = {}
last_flow_rate = {}
totalized_volume_ml = {}

app = Flask(__name__)

# Cloud Run HTTP entry point
@app.route("/", methods=["POST"])
def receive_pubsub_message():
    """ Triggered automatically whenever a Pub/Sub message arrives via HTTP """
    envelope = request.get_json()
    if not envelope:
        msg = "No Pub/Sub message received"
        print(f"error: {msg}")
        return f"Bad Request: {msg}", 400
    
    msg = envelope["message"]

    try:
        data = base64.b64decode(msg["data"]).decode("utf-8")
        event = json.loads(data)

        # handle only new data for streaming
        process_data(event)
        return "", 200
    
    except Exception as e:
        print(f"Error processing data from pub/sub: {e}")
        return f"Interal error: {e}", 500


def process_data(data: dict) -> None:
    """ Triggered automatically whenever a Pub/Sub message arrives """
    
    chrom_unit = data["chrom_unit"]
    cur_ts = int(data["time_ns"])

    # handle only new data for streaming
    if last_timestamp_ns.get(chrom_unit, 0) >= cur_ts:
        print(f"Skipping old event for {chrom_unit}")
        return
    
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)