import pytest
from datetime import datetime, timedelta
from multiprocessing import Queue

from time_series_trends.main import main

def test_generate_stream_superfast(noise_def_fixture):
    """
    this is a simple end-to-end integration test for the time_series_trends project
    without holds, the each trend completes in about 75 minutes = 4500 seconds
    at a stream rate adjust factor of 1000, we stream at a rate of 4500 / 1000 seconds or 4.5 seconds
    with 2 trends per column and 4 columns running in parallel, streaming all trends should take ~ 9 seconds
    if no errors and the function completes in a time consistent with the stream rate, test passes
    """
    
    start_ts = datetime.now()
    main(["--quick_run"])
    assert (datetime.now() - start_ts).total_seconds() < 11
