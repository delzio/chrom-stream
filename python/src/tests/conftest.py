import os
import pytest
import pandas as pd
from datetime import datetime, timezone

from time_series_trends.trend_generator import TrendGenerator
from batch_context.batch_context_generator import BatchContextGenerator
from sample_results.sample_result_generator import SampleResultGenerator

good_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "good_trend_template.csv")
bad_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "bad_trend_template.csv")
sample_template_path = os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json")

execution_time = datetime.now(timezone.utc)

# Trend Generator Fixtures
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

# Batch Context Generator Fixtures
@pytest.fixture
def good_batch_context_with_holds():
    return BatchContextGenerator(good_template_path, recipe_name="affinity_chrom", batch_id="1", chrom_id="chrom_1", execution_time=execution_time, holds=True)

@pytest.fixture
def bad_batch_context_with_holds():
    return BatchContextGenerator(bad_template_path, recipe_name="affinity_chrom", batch_id="1", chrom_id="chrom_1", execution_time=execution_time, holds=True)

@pytest.fixture
def good_batch_context_no_holds():
    return BatchContextGenerator(good_template_path, recipe_name="affinity_chrom", batch_id="1", chrom_id="chrom_1", execution_time=execution_time, holds=False)

@pytest.fixture
def bad_batch_context_no_holds():
    return BatchContextGenerator(bad_template_path, recipe_name="affinity_chrom", batch_id="1", chrom_id="chrom_1", execution_time=execution_time, holds=False)

# Sample Result Generator Fixture
@pytest.fixture
def sample_result_fixture():
    return SampleResultGenerator(template_path=sample_template_path)