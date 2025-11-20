import os
import random
import time
import pandas as pd

from trend_generator import TrendGenerator

def main(quick_run_mode, 
         trend_resolution_hz=1, 
         stream_rate_hz=1, 
         holds=True, 
         number_of_trends=8, 
         number_of_columns=4, 
         anomaly_rate=0.2,
         noise_def=None,
         noise_scale=1.0,
         column_util_gap=1000):

    if quick_run_mode:
        # Settings for quick run mode
        # This will generate a total of 16 trends across 4 columns in under 5 minutes
        trend_resolution_hz = .1
        stream_rate_hz = 10
        holds = False 
        number_of_trends = 4
        number_of_columns = 4
        anomaly_rate = 0.3
        column_util_gap = 5  # seconds between columns

    good_trend_path = os.path.join(os.getcwd(),"data","good_trend_template.csv")
    good_trend_gen = TrendGenerator(good_trend_path, noise_def=noise_def, noise_scale=noise_scale, holds=holds)

    bad_trend_path = os.path.join(os.getcwd(),"data","bad_trend_template.csv")
    bad_trend_gen = TrendGenerator(bad_trend_path, noise_def=noise_def, noise_scale=noise_scale, holds=holds)

    trend_gen_dict = {}
    for i in range(number_of_columns):
        key = f"column_{i+1}"
        trend_gen_dict[key] = []
        for j in range(number_of_trends):
            # Decide whether to use good or bad trend template based on anomaly rate
            if random.random() < anomaly_rate:
                bad_trend_gen.generate_dataset(trend_resolution_hz=trend_resolution_hz)
                trend_gen = bad_trend_gen.get_stream_generator()
            else:
                good_trend_gen.generate_dataset(trend_resolution_hz=trend_resolution_hz)
                trend_gen = good_trend_gen.get_stream_generator()
            trend_gen_dict[key].append(trend_gen)

    #start_ts = time.time()
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
                    print(f"{col_key}: {data_point}")
                    streaming = True
                except StopIteration:
                    continue
            time.sleep(1.0 / stream_rate_hz)
        time.sleep(column_util_gap)
    #end_ts = time.time()
    #total_time_min = (end_ts - start_ts) / 60.0
    #print(f"Stream time: {total_time_min:.2f} minutes.")

if __name__ == "__main__":
    main(quick_run_mode=True)