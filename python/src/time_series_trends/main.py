import os
import argparse
import yaml
import random
import time
from datetime import datetime, timedelta, timezone
import pandas as pd

from time_series_trends.trend_generator import TrendGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="Chrom Sensor Data Stream Simulator")
    parser.add_argument('--config', type=str, default=None, help='Path to YAML configuration file')
    parser.add_argument('--quick_run', action='store_true', help='Run in quick mode for testing')

    return parser.parse_args()

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)

def main():

    args = parse_args()
    if args.quick_run:
        # quick run settings: generates generates 16 trends across 4 columns within 5 minutes
        config = {}
        config["trend_resolution_hz"] = .1
        config["stream_rate_hz"] = 10
        config["holds"] = False 
        config["number_of_trends"] = 4
        config["number_of_columns"] = 4
        config["anomaly_rate"] = 0.3
        config["noise_scale"] = 1.0
        config["column_util_gap"] = 5
        config["noise_def"] = {
            "uv_mau": (0, 2.0),
            "cond_mScm": (0, 0.15),
            "ph": (0, 0.01),
            "flow_mL_min": (0, 300),
            "pressure_bar": (0, 0.01)
        }
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")
    
    config["streaming_start_ts"] = datetime.now(timezone.utc)

    generate_stream(**config)

def generate_stream(trend_resolution_hz, stream_rate_hz, holds,
                   number_of_trends, column_ids, batch_quality, 
                   noise_scale, column_util_gap, noise_def, streaming_start_ts):
    """ Generate Time Series Trend Dataset """

    good_trend_path = os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv")
    good_trend_gen = TrendGenerator(good_trend_path, noise_def=noise_def, noise_scale=noise_scale, holds=holds)

    bad_trend_path = os.path.join(os.getenv("PYTHONPATH"),"data","bad_trend_template.csv")
    bad_trend_gen = TrendGenerator(bad_trend_path, noise_def=noise_def, noise_scale=noise_scale, holds=holds)

    trend_gen_dict = {}
    for col in column_ids:
        trend_gen_dict[col] = []
        for j in range(number_of_trends):
            # Decide whether to use good or bad trend template based on anomaly rate
            if batch_quality[col][j] == "bad":
                simulated_data = bad_trend_gen.generate_dataset(trend_resolution_hz=trend_resolution_hz)
                trend_gen = TrendGenerator.get_stream_generator(simulated_data)
            else:
                simulated_data = good_trend_gen.generate_dataset(trend_resolution_hz=trend_resolution_hz)
                trend_gen = TrendGenerator.get_stream_generator(simulated_data)
            trend_gen_dict[col].append(trend_gen)

    for trend_no in range(number_of_trends):
        active_generators = []
        for col_key, gen_list in trend_gen_dict.items():
            gen = gen_list[trend_no]
            active_generators.append((col_key, gen))
        
        streaming = True
        while streaming:
            streaming = False
            for col_key, gen in active_generators:
                try:
                    data_point = next(gen)
                    data_point["time_sec"] = streaming_start_ts + timedelta(seconds=data_point["time_sec"])
                    print(f"{col_key}: {data_point}")
                    streaming = True
                except StopIteration:
                    continue
            time.sleep(1.0 / stream_rate_hz)
        time.sleep(column_util_gap)

if __name__ == "__main__":
    main()