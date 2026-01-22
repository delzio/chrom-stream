import os
import json
import base64
from flask import Flask, request
from influxdb_client_3 import InfluxDBClient3, Point

# GCP CONFIG
PROJECT_ID = os.environ["GCP_PROJECT_ID"]

# INFLUXDB CONFIG
TOKEN = os.environ["INFLUXDB_WRITE_TOKEN"]
ORG = "Dev"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATABASE = os.environ["INFLUXDB_BUCKET"]
influx_client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

# INITIALIZE GLOBALS
last_timestamp_ns = {}
last_flow_rate = {}
totalized_volume_ml = {}


# Cloud Run HTTP entry point
app = Flask(__name__)

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

    point = (
        Point("chromatography")
        .tag("instrument", data["chrom_unit"])
        .field("time_sec", data["time_sec"])
        .field("uv_mau", data["uv_mau"])
        .field("cond_mScm", data["cond_mScm"])
        .field("ph", data["ph"])
        .field("flow_mL_min", data["flow_mL_min"])
        .field("pressure_bar", data["pressure_bar"])
        .time(int(data["time_ns"])) 
    )

    influx_client.write(database=DATABASE, record=point)
    print("data point submitted to influxdb")
        
# deprecated: totalized volume calculations done downstream of streaming
def handle_event(event: dict) -> None:
    """ Process individual event from Pub/Sub and calculate totalized volumes """
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)