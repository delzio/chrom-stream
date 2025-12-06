import pytest

from time_series_trends.trend_generator import TrendGenerator

def test_stream_generator_items(good_trend_no_holds_fixture):
    simulated_df = good_trend_no_holds_fixture.generate_dataset(trend_resolution_hz=0.1)
    stream_generator = TrendGenerator.get_stream_generator(simulated_data=simulated_df)

    first_record = next(stream_generator)
    assert isinstance(first_record, dict)

def test_stream_generator_test_mode(bad_trend_no_holds_fixture):
    simulated_df = bad_trend_no_holds_fixture.generate_dataset(trend_resolution_hz=0.1)
    stream_generator = TrendGenerator.get_stream_generator(simulated_data=simulated_df, test_mode=True)

    records = list(stream_generator) 
    assert len(records) == 6
