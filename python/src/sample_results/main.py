import os
import pandas as pd
import json
import time
import yaml
import argparse
from datetime import datetime, timedelta, timezone

from sample_results.sample_result_generator import SampleResultGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="Sample Result File Generation Simulator")
    parser.add_argument('--config', type=str, default=None, help='Path to YAML configuration file')
    parser.add_argument('--quick_run', action='store_true', help='Run in quick mode for testing')

    return parser.parse_args()

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)

def main():
    # run the main script
    args = parse_args()
    if args.quick_run:
        config = {}
        config["number_of_runs"] = 4
        config["column_ids"] = ["chrom_1", "chrom_2", "chrom_3", "chrom_4"]
        config["sampling_ts_buffer_sec"] = 10
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
        config["retest_delay_sec"] = 60
        config["batch_duration_sec"] = 10180
        config["batch_delay_sec"] = 60
        config["stream_rate_adjust_factor"] = 1000
    else:
        config = load_config(args.config)

    config["template_path"] = os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json")
    config["execution_time"] = datetime.now(timezone.utc)

    build_sample_dataset_args = {key: value for key, value in config if key != "stream_rate_adjust_factor"}

    sample_results = build_sample_dataset(**build_sample_dataset_args)

    #with open(os.path.join(os.getenv("PYTHONPATH"),"output_files","sample_results_generated.json"), "w") as file:
    #          json.dump(sample_results, file, indent=2)

    generate_sample_result_events(sample_results=sample_results, stream_rate_adjust_factor=config["stream_rate_adjust_factor"])

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
            sample_results.extend(cur_post_sample_result)

    return sample_results

def generate_sample_result_events(sample_results, stream_rate_adjust_factor):
    """ Generate sample result events """ 

    sorted_sample_results = sorted(sample_results, key=lambda x: datetime.strptime(x["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ"))
    sample_event_generator = SampleResultGenerator.get_event_generator(simulated_data=sorted_sample_results)

    sample_event = next(sample_event_generator)
    streaming = True
    while streaming:
        streaming = False

        try:
            print(f"Sending sample data for {sample_event["sample_metadata"]}")
            cur_test_ts = datetime.strptime(sample_event["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ")

            sample_event = next(sample_event_generator)
            next_test_ts = datetime.strptime(sample_event["test_metadata"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            time_delay = next_test_ts - cur_test_ts
            time.sleep(time_delay.total_seconds() / stream_rate_adjust_factor)
            streaming = True
        except StopIteration:
            continue


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

if __name__ == "__main__":
    main()