import pytest
import pandas as pd
import numpy as np

def test_good_template_dataset(noise_def_fixture, good_trend_with_holds_fixture):
    df = good_trend_with_holds_fixture.template_data
    
    assert len(df) > 0
    assert "time_min" in df.columns
    assert "flow_setpoint_L_min" in df.columns
    assert any(df["flow_setpoint_L_min"] > 0)
    assert all(col in df.columns for col in noise_def_fixture.keys())
    assert all(df["time_min"] == np.arange(0, len(df) * 0.5, 0.5).tolist())

def test_bad_template_dataset(noise_def_fixture, bad_trend_with_holds_fixture):
    df = bad_trend_with_holds_fixture.template_data
    
    assert len(df) > 0
    assert "flow_setpoint_L_min" in df.columns
    assert any(df["flow_setpoint_L_min"] > 0)
    assert all(col in df.columns for col in noise_def_fixture.keys())
    assert all(df["time_min"] == np.arange(0, len(df) * 0.5, 0.5).tolist())

def test_good_template_dataset_no_holds(good_trend_no_holds_fixture):
    df = good_trend_no_holds_fixture.template_data

    assert len(df) > 0
    assert all(df["flow_setpoint_L_min"] > 0)

def test_bad_template_dataset_no_holds(bad_trend_no_holds_fixture):
    df = bad_trend_no_holds_fixture.template_data

    assert len(df) > 0
    assert all(df["flow_setpoint_L_min"] > 0)  
