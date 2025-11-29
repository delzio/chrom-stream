import os
import pandas as pd
import yaml
import argparse
from datetime import datetime, timedelta, timezone
import random
from multiprocessing import Process

from time_series_trends.main import generate_stream
from batch_context.main import build_batch_context, generate_batch_context_events
from sample_results.main import build_sample_dataset, generate_sample_result_events

def parse_args():
    arg_parser = argparse.ArgumentParser(description="Chromatography Data Generation")
    arg_parser.add_argument("--config", type=str, default=None, help='Path to YAML configuration file')
    arg_parser.add_argument("--quick_run", action='store_true', help='Run in quick mode for testing')
    
    return arg_parser.parse_args()

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)

def main():
    # Template Dataset Path
    batch_template_path = os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv")
    sample_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json")

    args = parse_args()
    if args.quick_run:
        config = {}

        # Quick run trend requirements:
        config["trend_resolution_hz"] = 0.1
        config["stream_rate_adjust_factor"] = 1000
        config["holds"] = True
        config["number_of_runs"] = 4
        config["number_of_columns"] = 4
        config["anomaly_rate"] = 0.3
        config["noise_scale"] = 1.0
        config["time_between_batches_sec"] = 60
        config["noise_def"] = {
            "trend_noise": {
                "uv_mau": (0, 2.0),
                "cond_mScm": (0, 0.15),
                "ph": (0, 0.01),
                "flow_mL_min": (0, 300),
                "pressure_bar": (0, 0.01)
            },
            "sample_noise": {
                "absorbance": (0, 0.16),
                "temperature": (0, 1.0)
            }
        }

        # Quick run sampling requirements:
        config["sampling_ts_buffer_sec"] = 600
        config["retest_delay_sec"] = 300

    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")

    # runtime dependent parameters:
    start_time = datetime.now(timezone.utc)
    batch_quality = {}
    col_ids = []
    for col in range(config["number_of_columns"]):
        cur_col_id = f"chrom_{col}"
        col_ids.append(cur_col_id)
        batch_quality[cur_col_id] = []
        for run in range(config["number_of_runs"]):
            if random.random() < config["anomaly_rate"]:
                batch_quality[cur_col_id].append("bad")
            else:
                batch_quality[cur_col_id].append("good")
    
    # pre-load datasets
    batch_context, phase_generators = build_batch_context(
        number_of_runs=config["number_of_runs"], 
        column_ids=col_ids, 
        template_path=batch_template_path,
        execution_time=start_time, 
        batch_delay_sec=config["time_between_batches_sec"]
    )
    batch_duration_sec = (batch_context[cur_col_id][run].simulated_batch_data.iloc[-1]["event_ts"] - batch_context[cur_col_id][run].simulated_batch_data.iloc[0]["event_ts"]).total_seconds()

    sample_results = build_sample_dataset(
        template_path=sample_template_path, 
        number_of_runs=config["number_of_runs"], 
        column_ids=col_ids, 
        sampling_ts_buffer_sec=config["sampling_ts_buffer_sec"],
        noise_def=config["noise_def"]["sample_noise"], 
        noise_scale=config["noise_scale"], 
        batch_quality=batch_quality, 
        retest_delay_sec=config["retest_delay_sec"],
        batch_duration_sec=batch_duration_sec, 
        batch_delay_sec=config["time_between_batches_sec"], 
        execution_time=start_time
    )

    # configure parallel streaming
    processes = [
        Process(target=generate_stream, args=(
            config["trend_resolution_hz"],
            config["stream_rate_adjust_factor"],
            config["holds"],
            config["number_of_runs"],
            col_ids,
            batch_quality,
            config["noise_scale"],
            config["time_between_batches_sec"],
            config["noise_def"]["trend_noise"],
            start_time
        )),
        Process(target=generate_batch_context_events, args=(
            config["number_of_runs"], 
            batch_context, 
            phase_generators, 
            config["stream_rate_adjust_factor"], 
            config["time_between_batches_sec"]
        )),
        Process(target=generate_sample_result_events, args=(
            sample_results, 
            config["stream_rate_adjust_factor"]
        ))
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

if __name__ == "__main__":
    main()