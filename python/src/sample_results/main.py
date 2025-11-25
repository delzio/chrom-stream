import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from sample_results.sample_result_generator import SampleResultGenerator

def main():
    # run the main script
    execution_time = datetime.now(timezone.utc)
    sample_results = generate_samples(number_of_runs=3, column_ids=["chrom_1", "chrom_2", "chrom_3", "chrom_4"],
                                      sampling_ts_buffer_sec=10, noise_def={
                                          "absorbance": (0, 0.16),
                                          "temperature": (0, 1.0)
                                      },
                                      noise_scale=1.0, batch_quality={
                                          "chrom_1": ["good", "good", "bad"],
                                          "chrom_2": ["good", "good", "good"],
                                          "chrom_3": ["good", "bad", "good"],
                                          "chrom_4": ["good", "good", "bad"],
                                      }, retest_delay_sec=5, batch_duration_sec=10180,
                                      batch_delay_sec=60, execution_time=execution_time)

    print (sample_results)
    return

def generate_samples(number_of_runs: int, column_ids: list, sampling_ts_buffer_sec: int,
                     noise_def: dict, noise_scale: float, batch_quality: dict, retest_delay_sec: int,
                     batch_duration_sec: int, batch_delay_sec: int, execution_time: datetime):
    """ Generate sample result dataset """

    template_path=os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json")
    sample_result_generator = SampleResultGenerator(template_path=template_path, noise_def=noise_def, noise_scale=noise_scale)

    sample_results = {}

    batch_id = 0
    sample_id = 0
    for run in range(number_of_runs):
        for idx, col in enumerate(column_ids):
            batch_id += 1
            instrument_id = f"solovpe_{idx}"
            sample_id += 1
            if run == 0:
                pre_sample_ts = execution_time - timedelta(seconds=sampling_ts_buffer_sec)
                post_sample_ts = execution_time + timedelta(seconds=(batch_duration_sec + sampling_ts_buffer_sec))
                sample_results[col] = []
            else:
                pre_sample_ts = execution_time + timedelta(seconds=(run + 1)*(batch_duration_sec + batch_delay_sec)) - timedelta(seconds=sampling_ts_buffer_sec)
                post_sample_ts = execution_time + timedelta(seconds=(run + 1)*(batch_duration_sec + batch_delay_sec)) + timedelta(seconds=(batch_duration_sec + sampling_ts_buffer_sec))
            
            # Generate pre-chrom sample results
            cur_pre_sample_result = sample_result_generator.generate_sample_result(
                instrument_id=instrument_id,
                sample_id=sample_id,
                sample_type="pre-affinity",
                batch_id=batch_id,
                measurement_ts=pre_sample_ts,
                target_titer=1.0,
                bad_run=(batch_quality[col][run] == "bad")
            )
            sample_results[col].append(cur_pre_sample_result)
            retest_ts = pre_sample_ts
            test_failed = cur_pre_sample_result["system_status"]["scan_result"] == "fail"
            while test_failed:
                sample_id += 1
                retest_ts += timedelta(seconds=retest_delay_sec)
                retest_pre_sample_result = sample_result_generator.generate_sample_result(
                    instrument_id=instrument_id,
                    sample_id=sample_id,
                    sample_type="pre-affinity",
                    batch_id=batch_id,
                    measurement_ts=retest_ts,
                    target_titer=1.0,
                    bad_run=(batch_quality[col][run] == "bad")
                )
                sample_results[col].append(retest_pre_sample_result)
                test_failed = retest_pre_sample_result["system_status"]["scan_result"] == "fail"

            # Generate post-chrom sample results
            sample_id += 1
            cur_post_sample_result = sample_result_generator.generate_sample_result(
                instrument_id=instrument_id,
                sample_id=sample_id,
                sample_type="post-affinity",
                batch_id=batch_id,
                measurement_ts=post_sample_ts,
                target_titer=5.0,
                bad_run=(batch_quality[col][run] == "bad")
            )
            sample_results[col].append(cur_post_sample_result)
            retest_ts = post_sample_ts
            test_failed = cur_post_sample_result["system_status"]["scan_result"] == "fail"
            while test_failed:
                sample_id += 1
                retest_ts += timedelta(seconds=retest_delay_sec)
                retest_post_sample_result = sample_result_generator.generate_sample_result(
                    instrument_id=instrument_id,
                    sample_id=sample_id,
                    sample_type="post-affinity",
                    batch_id=batch_id,
                    measurement_ts=retest_ts,
                    target_titer=5.0,
                    bad_run=(batch_quality[col][run] == "bad")
                )
                sample_results[col].append(retest_post_sample_result)
                test_failed = retest_post_sample_result["system_status"]["scan_result"] == "fail"

    return sample_results

if __name__ == "__main__":
    main()