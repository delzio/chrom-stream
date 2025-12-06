import os
import yaml
import argparse
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from google.cloud import storage
from multiprocessing import Process, Queue

from batch_context.batch_context_generator import BatchContextGenerator
from gcp_utils import parquet_to_gcs

def parse_args():
    parser = argparse.ArgumentParser(description="Batch Context Data Generation Simulator")
    parser.add_argument('--config', type=str, default=None, help='Path to YAML configuration file')
    parser.add_argument('--quick_run', action='store_true', help='Run in quick mode for testing')

    return parser.parse_args()

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)
    
def main():

    # load configuration arguments
    args = parse_args()
    if args.quick_run:
        config = {}
        config["number_of_runs"] = 2
        config["holds"] = False
        config["column_ids"] = ["chrom_1", "chrom_2", "chrom_3", "chrom_4"]
        config["batch_delay_sec"] = 0
        config["stream_rate_adjust_factor"] = 1000
        config["local_test"] = True
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")

    # set runtime dependent parameters
    config["execution_time"] = datetime.now(timezone.utc)
    template_path=os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv")
    batch_queue = Queue()
    phase_queue = Queue()

    # build batch context dataset
    build_batch_args = {key: val for key, val in config.items() 
                        if key in ["number_of_runs", "column_ids", "execution_time", "batch_delay_sec"]}
    build_batch_args["template_path"] = template_path
    batch_context, phase_generators = build_batch_context(**build_batch_args)

    # Setup GCS upload processes or local print based on test mode
    if not config["local_test"]:
        gcs_bucket = os.environ["GCS_BATCH_BUCKET"]
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        batch_process = Process(target=send_event_to_gcs, args=(batch_queue, bucket, "batch"))
        phase_process = Process(target=send_event_to_gcs, args=(phase_queue, bucket, "phase"))
    else:
        batch_process = Process(target=print_event, args=(batch_queue, "batch"))
        phase_process = Process(target=print_event, args=(phase_queue, "phase"))

    # Start processes to generate events and send to GCS
    processes = [
        Process(target=generate_batch_context_events, args=(
            batch_queue,
            phase_queue,
            config["number_of_runs"],
            batch_context,
            phase_generators,
            config["stream_rate_adjust_factor"],
            config["batch_delay_sec"]
        )),
        batch_process,
        phase_process
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    return

def build_batch_context(number_of_runs, column_ids, template_path, execution_time, batch_delay_sec, holds=True):
    """ Generate batch context dataset """
    
    batch_context = {}
    phase_generators = {}

    # Collect Batch Data
    batch_id = 0
    for run in range(number_of_runs):
        for col in column_ids:
            batch_id += 1
            if run == 0:
                batch_start_ts = execution_time
                batch_context[col] = []
                phase_generators[col] = []
            else:
                batch_start_ts = batch_context[col][run-1].simulated_batch_data.iloc[-1]["event_ts"] + timedelta(seconds=batch_delay_sec)
            cur_batch_context = BatchContextGenerator(template_path=template_path, recipe_name="affinity_chrom_v1", 
                                                      batch_id=batch_id, chrom_id=col, execution_time=batch_start_ts, holds=holds)
            cur_phase_generator = BatchContextGenerator.get_event_generator(cur_batch_context.simulated_phase_data)
            batch_context[col].append(cur_batch_context)
            phase_generators[col].append(cur_phase_generator)

    return batch_context, phase_generators

def generate_batch_context_events(batch_queue, phase_queue, number_of_runs, batch_context, phase_generators, stream_rate_adjust_factor, batch_delay_sec):
    """ Generate batch context events and push to queue """    

    for run in range(number_of_runs):
        active_generators = []
        for col_key, gen_list in phase_generators.items():
            gen = gen_list[run]
            active_generators.append((col_key, gen))
        
        streaming = True
        while streaming:
            streaming = False

            for col_key, gen in active_generators:
                try:
                    phase_event = next(gen)
                    batch_data = batch_context[col_key][run].simulated_batch_data
                    batch_event = batch_data[batch_data["event_ts"] == phase_event["event_ts"]].reset_index(drop=True)
                    if not batch_event.empty:
                        batch_queue.put(batch_event)
                        
                    phase_event["batch_id"] = batch_data["batch_id"][0]
                    phase_queue.put(pd.DataFrame([phase_event]))

                    phase_data = batch_context[col_key][run].simulated_phase_data
                    cur_phase_idx = phase_data.index[
                        phase_data["event_ts"] == phase_event["event_ts"]
                    ]
                    streaming = True
                except StopIteration:
                    continue
            
            try:
                time_delay = phase_data["event_ts"].iloc[cur_phase_idx[0] + 1] - phase_data["event_ts"].iloc[cur_phase_idx[0]]
                time.sleep(time_delay.total_seconds() / stream_rate_adjust_factor)
            except IndexError:
                break

        time.sleep(batch_delay_sec)

    # signal completion to queues
    batch_queue.put("EOF")
    phase_queue.put("EOF")

def send_event_to_gcs(event_queue, bucket, event_type):
    """ Submit batch or phase context event to GCS """

    while True:
        event = event_queue.get()
        if event == "EOF":
            break
        phase_str = f"phase_{event['phase'][0]}_" if event_type == "phase" else ""
        ts = event["event_ts"][0].strftime("%Y-%m-%dT%H-%M-%S")
        gcs_file_path = f"raw/{event_type}/batch_{event['batch_id'][0]}_{phase_str}context_{ts}.parquet"
        parquet_to_gcs(data=event, gcs_file_path=gcs_file_path, bucket=bucket)

def print_event(event_queue, event_type):
    """ Print batch or phase context event from queue """

    while True:
        event = event_queue.get()
        if isinstance(event, str) and event == "EOF":
            break
        print(f"{event_type} event: {event}")

if __name__ == "__main__":
    main()