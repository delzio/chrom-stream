import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import random
from multiprocessing import Process

from time_series_trends.main import generate_stream
from batch_context.main import generate_batch_context
from sample_results.main import generate_samples

def main():
    # Define trend requirements:
    trend_resolution_hz = 1
    stream_rate_hz = 1
    holds = True
    number_of_runs = 10
    number_of_columns = 4
    anomaly_rate = 0.3
    noise_scale = 1.0
    time_between_batches_sec = 60
    noise_def = {
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

    # runtime dependent parameters:
    start_time = datetime.now(timezone.utc)
    batch_quality = {}
    col_ids = []
    for col in range(number_of_columns):
        cur_col_id = f"chrom_{col}"
        col_ids.append(cur_col_id)
        batch_quality[cur_col_id] = []
        for run in range(number_of_runs):
            if random.random() < anomaly_rate:
                batch_quality[cur_col_id].append("bad")
            else:
                batch_quality[cur_col_id].append("good")


    processes = [
        Process(target=generate_stream(
            trend_resolution_hz=trend_resolution_hz,
            stream_rate_hz=stream_rate_hz,
            holds=holds,
            number_of_trends=number_of_runs,
            column_ids=col_ids,
            batch_quality=batch_quality,
            noise_scale=noise_scale,
            column_util_gap=time_between_batches_sec,
            noise_def=noise_def["trend_noise"],
            streaming_start_ts=start_time
        )),
        Process(target=generate_batch_context(
            number_of_runs=number_of_runs,
            column_ids=col_ids,
            batch_delay_sec=time_between_batches_sec,
            execution_time=start_time,
            holds=holds,
        )),
        Process(target=generate_samples(
            number_of_runs=number_of_runs,
            column_ids=col_ids,
            sampling_ts_buffer_sec=10,
            noise_def=noise_def["sample_noise"],
            noise_scale=noise_scale,
            batch_quality=batch_quality,
            retest_delay_sec=10,
            batch_duration_sec=10180,
            batch_delay_sec=time_between_batches_sec,
            execution_time=start_time
        ))
    ]

    for process in processes:
        process.start()

    for process in processes:
        process.join()

if __name__ == "__main__":
    main()