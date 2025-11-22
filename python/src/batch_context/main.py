import os
import pandas as pd
from datetime import datetime, timedelta, timezone

from batch_context.batch_context_generator import BatchContextGenerator

def main():

    execution_time = datetime.now(timezone.utc)
    batch_context = BatchContextGenerator(template_path=os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv"),
                                          recipe_name="affinity_chrom", batch_id="1", chrom_id="chrom_1", execution_time=execution_time)
    print(batch_context.phase_ts)

    return


if __name__ == "__main__":
    main()