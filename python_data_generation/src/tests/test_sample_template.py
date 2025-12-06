import pytest
import pandas as pd
import numpy as np

def test_template_dataset(sample_result_fixture):
    data = sample_result_fixture.template_data
    
    assert len(data) > 0

    assert "system_status" in data
    assert "messages" in data["system_status"]
    assert "errors" in data["system_status"]

    assert "instrument" in data

    assert "test_metadata" in data
    assert "test_id" in data["test_metadata"]
    assert "temperature_c" in data["test_metadata"]
    assert "pathlength_range_mm" in data["test_metadata"]
    assert "min" in data["test_metadata"]["pathlength_range_mm"]
    assert "max" in data["test_metadata"]["pathlength_range_mm"]

    assert "measurement" in data
    assert "raw_data_points" in data["measurement"]
    assert "concentration" in data["measurement"]
    assert isinstance(data["measurement"]["raw_data_points"], list)
    assert len(data["measurement"]["raw_data_points"]) > 0
    assert all(["pathlength_mm" in item for item in data["measurement"]["raw_data_points"]])
    assert all(["absorbance" in item for item in data["measurement"]["raw_data_points"]])
