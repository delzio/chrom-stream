import pytest

def test_simulated_dataset_shape(noise_def_fixture, good_trend_with_holds_fixture):
    trend_resolution = 0.1

    template_df = good_trend_with_holds_fixture.template_data
    simulated_df = good_trend_with_holds_fixture.generate_dataset(trend_resolution_hz=trend_resolution)
    required_cols = ["time_sec", "time_min"]
    required_cols.extend(list(noise_def_fixture.keys()))

    assert template_df["time_min"][0]*60 == simulated_df["time_sec"][0]
    assert template_df["time_min"].iloc[-1]*60 == simulated_df["time_sec"].iloc[-1]
    assert (simulated_df["time_sec"].iloc[-1] - simulated_df["time_sec"][0])/(len(simulated_df) - 1) == 1/trend_resolution
    assert simulated_df.shape[1] == (len(noise_def_fixture.keys()) + 2)
    assert all(col in required_cols for col in simulated_df.columns)

def test_unique_dataset_generation(noise_def_fixture, bad_trend_with_holds_fixture):
    trend_resolution = 0.1

    simulated_df_1 = bad_trend_with_holds_fixture.generate_dataset(trend_resolution_hz=trend_resolution)
    simulated_df_2 = bad_trend_with_holds_fixture.generate_dataset(trend_resolution_hz=trend_resolution)

    assert not simulated_df_1.equals(simulated_df_2)