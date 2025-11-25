import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from batch_context.batch_context_generator import BatchContextGenerator

def main():

    execution_time = datetime.now(timezone.utc)
    batch_context_dict = generate_batch_context(number_of_runs=3,
                                                column_ids=["chrom_1", "chrom_2", "chrom3", "chrom4"],
                                                batch_delay_sec=60, execution_time=execution_time)

    return

def generate_batch_context(number_of_runs: int, column_ids: list,
                           batch_delay_sec: int, execution_time: datetime, holds: bool = True):
    """ Generate batch context dataset """
    
    template_path=os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv")
    batch_context = {}

    batch_id = 0
    for run in range(number_of_runs):
        for col in column_ids:
            batch_id += 1
            if run == 0:
                batch_start_ts = execution_time
                batch_context[col] = []
            else:
                batch_start_ts = batch_context[col][run-1].batch_ts["end_ts"] + timedelta(seconds=batch_delay_sec)
            cur_batch_context = BatchContextGenerator(template_path=template_path, recipe_name="affinity_chrom_v1", 
                                                      batch_id=batch_id, chrom_id=col, execution_time=batch_start_ts)
            batch_context[col].append(cur_batch_context)
    
    return batch_context



if __name__ == "__main__":
    main()