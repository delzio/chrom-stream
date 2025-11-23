import os
import pandas as pd
from datetime import datetime, timezone

from sample_results.sample_result_generator import SampleResultGenerator

def main():
    # run the main script
    test = SampleResultGenerator(template_path=os.path.join(os.getenv("PYTHONPATH"), "data", "sample_result.json"))

    print (test.generate_result(instrument_id="1", sample_id="1", sample_type="pre_affinity", batch_id=1, measurement_ts=datetime.now(), target_titer=5))
    return

if __name__ == "__main__":
    main()