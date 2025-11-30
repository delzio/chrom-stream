import os
import json
import pandas as pd
from google.cloud import pubsub_v1
from influxdb_client_3 import InfluxDBClient3, Point

from pub_sub_utils import subscribe

# INFLUXDB CONFIG
TOKEN = os.environ["INFLUXDB_WRITE_TOKEN"]
ORG = "Dev"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATABASE = os.environ["INFLUXDB_BUCKET"]
client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

# INITIALIZE GLOBALS
buffer = {}
last_timestamp_ns = {}
last_flow_rate = {}
totalized_volume_ml = {}

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
    client.write(database=DATABASE, record=point)
    print("data point submitted to influxdb")


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """ Triggered automatically whenever a Pub/Sub message arrives """
    try:
        data = json.loads(message.data.decode("utf-8"))
        chrom_unit = data["chrom_unit"]

        # buffer data by chrom unit
        if chrom_unit not in buffer:
            buffer[chrom_unit] = []
        else:
            buffer[chrom_unit].append(data)
        
        # sort buffer by timestamp
        buffer[chrom_unit] = sorted(buffer[chrom_unit], key=lambda x: int(x["time_ns"]))

        # ensure buffered events are handled in order
        for event in buffer[chrom_unit]:
            if last_timestamp_ns.get(chrom_unit, 0) < int(event["time_ns"]):
                handle_event(event)
        
        message.ack()
    except Exception as e:
        print(f"Error collecting data from pub/sub: {e}")


def main():
    subscribe(callback_fn=process_message)


if __name__ == "__main__":
    main()