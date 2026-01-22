import os
import argparse
import yaml
import time
from datetime import datetime, timedelta, timezone
from multiprocessing import Process, Queue

from time_series_trends.trend_generator import TrendGenerator
from gcp_utils import publish

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Chrom Sensor Data Stream Simulator")
    parser.add_argument('--config', type=str, default=None, help='Path to YAML configuration file')
    parser.add_argument('--quick_run', action='store_true', help='Run in quick mode for testing')

    return parser.parse_args(argv)

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)

def main(argv=None):

    # load configuration arguments
    args = parse_args(argv)
    if args.quick_run:
        # quick run settings: generates generates 16 trends across 4 columns within 5 minutes
        config = {}
        config["trend_resolution_hz"] = .1
        config["stream_rate_adjust_factor"] = 1000
        config["holds"] = False 
        config["number_of_trends"] = 2
        config["column_ids"] = ["chrom_1", "chrom_2", "chrom_3", "chrom_4"]
        config["batch_quality"] = {
            "chrom_1": ["good", "good", "good", "good"],
            "chrom_2": ["good", "bad", "good", "good"],
            "chrom_3": ["good", "good", "good", "bad"],
            "chrom_4": ["good", "bad", "good", "good"]
        }
        config["noise_scale"] = 1.0
        config["column_util_gap"] = 0
        config["noise_def"] = {
            "uv_mau": (0, 2.0),
            "cond_mScm": (0, 0.15),
            "ph": (0, 0.01),
            "flow_mL_min": (0, 300),
            "pressure_bar": (0, 0.01)
        }
        config["local_test"] = True
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")
    
    # runtime dependent parameters:
    config["streaming_start_ts"] = datetime.now(timezone.utc)
    trend_queue = Queue()

    # Setup Pub/Sub publish process or local print based on test mode
    if not config["local_test"]:
        publish_process = Process(target=publish_trend_to_pubsub, args=(trend_queue,))
    else:
        publish_process = Process(target=print_trend, args=(trend_queue,))

    # Start processes to generate events and publish to Pub/Sub
    processes = [
        Process(target=generate_stream, args=(
            trend_queue,
            config["trend_resolution_hz"],
            config["stream_rate_adjust_factor"],
            config["holds"],
            config["number_of_trends"],
            config["column_ids"],
            config["batch_quality"],
            config["noise_scale"],
            config["column_util_gap"],
            config["noise_def"],
            config["streaming_start_ts"]
        )),
        publish_process
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()

    return


def generate_stream(trend_queue, trend_resolution_hz, stream_rate_adjust_factor, holds,
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

        batch_start_ts = streaming_start_ts + trend_no * (timedelta(seconds=max(simulated_data["time_sec"])) + timedelta(seconds=column_util_gap))
        
        streaming = True
        while streaming:
            streaming = False
            for col_key, gen in active_generators:
                try:
                    data_point = next(gen)
                    timestamp = batch_start_ts + timedelta(seconds=data_point["time_sec"])
                    data_point["time_iso"] = timestamp.isoformat()
                    data_point["time_ns"] = int(timestamp.timestamp() * 1e9)
                    data_point["chrom_unit"] = col_key
                    
                    trend_queue.put(data_point)

                    streaming = True
                except StopIteration:
                    continue
            time.sleep(1 / trend_resolution_hz / stream_rate_adjust_factor)
        time.sleep(column_util_gap / stream_rate_adjust_factor)

    # end stream
    trend_queue.put("EOF")

def publish_trend_to_pubsub(trend_queue) -> None:
    """ Publish message to Pub/Sub topic """

    while True:
        data_point = trend_queue.get()
        if data_point == "EOF":
            break
        publish(message=data_point)

def print_trend(trend_queue) -> None:
    """ Print trend data points from queue """

    while True:
        data_point = trend_queue.get()
        if data_point == "EOF":
            break
        print(f"trend data point: {data_point}")

if __name__ == "__main__":
    main()