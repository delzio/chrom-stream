from google.cloud import storage
import os
import pandas as pd
import json
import time
import yaml
import argparse
from datetime import datetime, timedelta, timezone
from multiprocessing import Process, Queue

from sample_results.sample_result_generator import SampleResultGenerator
from gcp_utils import json_to_gcs

def parse_args():
    parser = argparse.ArgumentParser(description="Sample Result File Generation Simulator")
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
        config["column_ids"] = ["chrom_1", "chrom_2", "chrom_3", "chrom_4"]
        config["sampling_ts_buffer_sec"] = 0
        config["noise_def"] = {
            "absorbance": (0, 0.16),
            "temperature": (0, 1.0)
        }
        config["noise_scale"] = 1.0
        config["batch_quality"] = {
            "chrom_1": ["good", "good", "good", "good"],
            "chrom_2": ["good", "bad", "good", "good"],
            "chrom_3": ["good", "good", "good", "bad"],
            "chrom_4": ["good", "bad", "good", "good"]
        }
        config["retest_delay_sec"] = 0
        config["batch_duration_sec"] = 10180
        config["batch_delay_sec"] = 0
        config["stream_rate_adjust_factor"] = 1000
        config["local_test"] = True
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")

    # runtime dependent parameters:
    config["template_path"] = os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json")
    config["execution_time"] = datetime.now(timezone.utc)
    sample_queue = Queue()

    # build sample result dataset
    build_sample_dataset_args = {key: value for key, value in config.items() if key not in ["stream_rate_adjust_factor", "local_test"]}
    sample_results = build_sample_dataset(**build_sample_dataset_args)

    # Setup GCS upload process or local print based on test mode
    if not config["local_test"]:
        gcs_bucket = os.environ["GCS_SAMPLE_BUCKET"]
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        sample_process = Process(target=send_sample_to_gcs, args=(sample_queue, bucket))
    else:
        sample_process = Process(target=print_sample, args=(sample_queue,))

    # Start processes to generate events and send to GCS
    processes = [
        Process(target=generate_sample_result_events, args=(
            sample_queue,
            sample_results,
            config["stream_rate_adjust_factor"]
        )),
        sample_process
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    return

def build_sample_dataset(template_path: str, number_of_runs: int, column_ids: list, sampling_ts_buffer_sec: int,
                         noise_def: dict, noise_scale: float, batch_quality: dict, retest_delay_sec: int,
                         batch_duration_sec: int, batch_delay_sec: int, execution_time: datetime):
    """ Generate sample result dataset """

    sample_result_generator = SampleResultGenerator(template_path=template_path, noise_def=noise_def, noise_scale=noise_scale)

    sample_results = []

    batch_id = 0
    sample_id = 0
    test_id = 0
    for run in range(number_of_runs):
        for idx, col in enumerate(column_ids):
            batch_id += 1
            instrument_id = f"solovpe_{idx+1}"
            sample_id += 1
            test_id += 1
            if run == 0:
                pre_sample_ts = execution_time - timedelta(seconds=sampling_ts_buffer_sec)
                post_sample_ts = execution_time + timedelta(seconds=(batch_duration_sec + sampling_ts_buffer_sec))
            else:
                pre_sample_ts = execution_time + timedelta(seconds=(run + 1)*(batch_duration_sec + batch_delay_sec)) - timedelta(seconds=sampling_ts_buffer_sec)
                post_sample_ts = execution_time + timedelta(seconds=(run + 1)*(batch_duration_sec + batch_delay_sec)) + timedelta(seconds=(batch_duration_sec + sampling_ts_buffer_sec))
        
            # Generate pre-chrom sample results
            cur_pre_sample_result = collect_results_by_sample(
                 sample_result_generator=sample_result_generator, test_id=test_id,
                 instrument_id=instrument_id, sample_id=sample_id, sample_type="pre-affinity",
                 batch_id=batch_id, column_id=col, sample_ts=pre_sample_ts, target_titer=1.0,
                 retest_delay_sec=retest_delay_sec
            )
            test_id = cur_post_sample_result[-1]["test_metadata"]["test_id"]
            sample_results.extend(cur_pre_sample_result)

            # Generate post-chrom sample results
            sample_id += 1
            test_id += 1
            bad_run = batch_quality[col][run] == "bad"
            target_titer = 4.5 if bad_run else 5.0
            cur_post_sample_result = collect_results_by_sample(
                 sample_result_generator=sample_result_generator, test_id=test_id,
                 instrument_id=instrument_id, sample_id=sample_id, sample_type="post-affinity",
                 batch_id=batch_id, column_id=col, sample_ts=post_sample_ts, target_titer=target_titer,
                 retest_delay_sec=retest_delay_sec
            )
            test_id = cur_post_sample_result[-1]["test_metadata"]["test_id"]
            sample_results.extend(cur_post_sample_result)

    return sample_results

def generate_sample_result_events(sample_queue, sample_results, stream_rate_adjust_factor):
    """ Generate sample result events """ 

    sorted_sample_results = sorted(sample_results, key=lambda x: datetime.strptime(x["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ"))
    sample_event_generator = SampleResultGenerator.get_event_generator(simulated_data=sorted_sample_results)

    sample_event = next(sample_event_generator)
    streaming = True
    while streaming:
        streaming = False

        try:
            sample_queue.put(sample_event)

            cur_test_ts = datetime.strptime(sample_event["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ")

            sample_event = next(sample_event_generator)
            next_test_ts = datetime.strptime(sample_event["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            time_delay = next_test_ts - cur_test_ts
            time.sleep(time_delay.total_seconds() / stream_rate_adjust_factor)
            streaming = True
        except StopIteration:
            continue

    # signal completion to queue
    sample_queue.put("EOF")


def collect_results_by_sample(sample_result_generator, test_id, instrument_id, sample_id, sample_type, batch_id, column_id, sample_ts, target_titer, retest_delay_sec, bad_run=False):
    """ generate and compile sample results for a given run """

    # generate sample result
    test_results = []
    sample_result = sample_result_generator.generate_sample_result(
        test_id=test_id,
        instrument_id=instrument_id,
        sample_id=sample_id,
        sample_type=sample_type,
        batch_id=batch_id,
        column_id=column_id,
        measurement_ts=sample_ts,
        target_titer=target_titer,
        bad_run=bad_run
    )
    test_results.append(sample_result)
    
    # retest if measurement failed validation until successful measurment
    retest_ts = sample_ts
    test_failed = sample_result["system_status"]["scan_result"] == "fail"
    while test_failed:
        test_id += 1
        retest_ts += timedelta(seconds=retest_delay_sec)
        retest_sample_result = sample_result_generator.generate_sample_result(
            test_id=test_id,
            instrument_id=instrument_id,
            sample_id=sample_id,
            sample_type=sample_type,
            batch_id=batch_id,
            column_id=column_id,
            measurement_ts=retest_ts,
            target_titer=target_titer,
            bad_run=bad_run
        )
        test_results.append(retest_sample_result)
        test_failed = retest_sample_result["system_status"]["scan_result"] == "fail"

    return test_results

def send_sample_to_gcs(sample_queue, bucket):
    """ Submit sample result event to GCS """

    while True:
        sample_event = sample_queue.get()
        if sample_event == "EOF":
            break
        gcs_file_path = f"raw/sample_{sample_event['sample_metadata']['sample_id']}_results_{sample_event['test_metadata']['date']}.json"
        json_to_gcs(data=sample_event, gcs_file_path=gcs_file_path, bucket=bucket)
        
def print_sample(sample_queue):
    """ Print batch or phase context event from queue """

    while True:
        sample_event = sample_queue.get()
        if sample_event == "EOF":
            break
        print(f"sample data: {sample_event["sample_metadata"]}")

if __name__ == "__main__":
    main()