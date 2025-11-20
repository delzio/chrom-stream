import os
import pytest
import pandas as pd

from trend_generator import TrendGenerator

good_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "good_trend_template.csv")
bad_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "bad_trend_template.csv")

@pytest.fixture
def noise_def_fixture():
    return {
        "uv_mau": (0, 2.0),
        "cond_mScm": (0, 0.15),
        "ph": (0, 0.01),
        "flow_mL_min": (0, 300),
        "pressure_bar": (0, 0.01)
    }

@pytest.fixture
def good_trend_no_holds_fixture(noise_def_fixture):
    return TrendGenerator(good_template_path, noise_def=noise_def_fixture, holds=False)

@pytest.fixture
def bad_trend_no_holds_fixture(noise_def_fixture):
    return TrendGenerator(bad_template_path, noise_def=noise_def_fixture, holds=False)

@pytest.fixture
def good_trend_with_holds_fixture(noise_def_fixture):
    return TrendGenerator(good_template_path, noise_def=noise_def_fixture, holds=True)

@pytest.fixture
def bad_trend_with_holds_fixture(noise_def_fixture):
    return TrendGenerator(bad_template_path, noise_def=noise_def_fixture, holds=True)