import pytest
from datetime import datetime, timedelta

from time_series_trends.main import generate_stream

def test_generate_stream_superfast(noise_def_fixture):
    """
    this is a simple end-to-end integration test for the time_series_trends project
    without holds, the each trend completes in about 75 minutes = 4500 seconds
    at a trend resolution of 0.01 Hz, we have 45 records with 100s intervals
    at a stream rate of 10 Hz, we stream 10 records per second, streaming a full trend in 4.5 seconds
    with 2 trends per column and 4 columns running in parallel, streaming all trends should take ~ 9 seconds
    if no errors and the function completes in a time consistent with the stream rate, test passes
    """
    
    start_ts = datetime.now()
    generate_stream(trend_resolution_hz=0.01, stream_rate_hz=10, holds=False, 
                    number_of_trends=2, column_ids=["chrom_1", "chrom_2", "chrom_3", "chrom_4"], 
                    batch_quality={
                        "chrom_1": ["good", "good", "good", "good"],
                        "chrom_2": ["good", "bad", "good", "good"],
                        "chrom_3": ["good", "good", "good", "bad"],
                        "chrom_4": ["good", "bad", "good", "good"]
                    }, 
                    noise_scale=1, column_util_gap=0, noise_def=noise_def_fixture,
                    streaming_start_ts=start_ts)
    assert (datetime.now() - start_ts).total_seconds() < 10
