import os
import json
import pandas as pd
from google.cloud import pubsub_v1, storage
from influxdb_client_3 import InfluxDBClient3, Point
from multiprocessing import Process, Queue

from gcp_utils import subscribe, parquet_to_gcs

# INFLUXDB CONFIG
TOKEN = os.environ["INFLUXDB_WRITE_TOKEN"]
ORG = "Dev"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATABASE = os.environ["INFLUXDB_BUCKET"]
influx_client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

# GCS CONFIG
OUTPUT_DIR = os.environ["PYTHON_OUTPUT_DIR"]
GCS_BUCKET = os.environ["GCS_TREND_BUCKET"]
gcs_client = storage.Client()
BUCKET = gcs_client.bucket(GCS_BUCKET)

# INITIALIZE GLOBALS
local_test = True
stream_trend_queue = Queue()
batch_trend_queue = Queue()
buffer_limit = 1000
buffer = {}
last_timestamp_ns = {}
last_flow_rate = {}
totalized_volume_ml = {}

def main():

    # Start Pub/Sub subscription to receive events
    subscribe(callback_fn=process_message)

    # Start processes to handle streaming and batched trend data
    if local_test:
        processes = [
            Process(target=print_trend_event, args=(stream_trend_queue, "stream")),
            Process(target=print_trend_event, args=(batch_trend_queue, "batch"))
        ]
    else:
        processes = [
            Process(target=send_points_to_influxdb, args=(stream_trend_queue,)),
            Process(target=send_batched_trend_to_gcs, args=(batch_trend_queue, BUCKET))
        ]
    
    for process in processes:
        process.start() 
    for process in processes:
        process.join()

    return

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

    point = (
        Point("chromatography")
        .tag("instrument", event["chrom_unit"])
        .field("uv_mau", event["uv_mau"])
        .field("cond_mScm", event["cond_mScm"])
        .field("ph", event["ph"])
        .field("flow_mL_min", event["flow_mL_min"])
        .field("pressure_bar", event["pressure_bar"])
        .field("totalized_volume_ml", totalized_volume_ml[chrom_unit])
        .field("totalized_column_volumes", tot_col_vol)
        .time(cur_ts) 
    )

    stream_trend_queue.put(point)

    # handle buffered data for raw storage
    event_with_tot_calcs = event.copy()
    event_with_tot_calcs["totalized_volume_ml"] = totalized_volume_ml[chrom_unit]
    event_with_tot_calcs["totalized_column_volumes"] = tot_col_vol

    if chrom_unit not in buffer:
        buffer[chrom_unit] = []
    buffer[chrom_unit].append(event_with_tot_calcs)

    if len(buffer[chrom_unit]) >= buffer_limit:
        batch_trend_queue.put(buffer[chrom_unit])
        buffer[chrom_unit] = []


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """ Triggered automatically whenever a Pub/Sub message arrives """
    try:
        data = json.loads(message.data.decode("utf-8"))
        chrom_unit = data["chrom_unit"]

        # handle only new data for streaming
        if last_timestamp_ns.get(chrom_unit, 0) < int(data["time_ns"]):
            handle_event(data)
        
        message.ack()
    except Exception as e:
        print(f"Error collecting data from pub/sub: {e}")

def send_points_to_influxdb(stream_trend_queue):
    """ Send streaming trend data points to InfluxDB """

    while True:
        data_point = stream_trend_queue.get()
        influx_client.write(database=DATABASE, record=data_point)
        print("data point submitted to influxdb")

def send_batched_trend_to_gcs(batch_trend_queue, bucket):
    """ Send batched trend data to GCS """

    while True:
        batched_data = batch_trend_queue.get()
        chrom_unit = list(batched_data.keys())[0]
        df = pd.DataFrame(batched_data[chrom_unit])
        ts = df["time_iso"].replace(":", "-")
        gcs_file_path = f"raw/{chrom_unit}/{chrom_unit}_trends_{ts}.parquet"
        parquet_to_gcs(data=df, gcs_file_path=gcs_file_path, bucket=bucket)

def print_trend_event(trend_queue, event_type):
    """ Print stream or batched trend event from queue """

    while True:
        trend_event = trend_queue.get()
        if event_type == "stream":
            print(f"streaming data point: {trend_event}")
        else:
            print(f"batched trend data: {trend_event.head()}")


if __name__ == "__main__":
    main()