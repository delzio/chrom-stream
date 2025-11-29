import os
import json
import pandas as pd
from google.cloud import pubsub_v1
from influxdb_client_3 import InfluxDBClient3, Point

from pub_sub_utils import subscribe

# INFLUXDB
TOKEN = os.environ["INFLUXDB_WRITE_TOKEN"]
ORG = "Dev"
HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
DATABASE = os.environ["INFLUXDB_BUCKET"]
client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """ Triggered automatically whenever a Pub/Sub message arrives """
    try:
        data = json.loads(message.data.decode("utf-8"))
        print("Received message:", data)
        
        point = (
            Point("chromatography")
            .tag("instrument", data["chrom_unit"])
            .field("uv_mau", data["uv_mau"])
            .field("cond_mScm", data["cond_mScm"])
            .field("ph", data["ph"])
            .field("flow_mL_min", data["flow_mL_min"])
            .field("pressure_bar", data["pressure_bar"])
            .time(data["time_ns"]) 
        )

        client.write(database=DATABASE, record=point)
        print("data point submitted to influxdb")
        message.ack()
    except Exception as e:
        print(f"Error in submission to influxdb: {e}")
    #except json.decoder.JSONDecodeError:
    #    print(f"Message not formatted correctly, acknowledging and ignoring: {message.data}")
    #    message.ack()

def main():
    subscribe(callback_fn=process_message)


if __name__ == "__main__":
    main()