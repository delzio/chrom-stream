"""
Batch Data:
 - Recipe Name
 - Batch ID (1 lot per trend)
 - Batch Start Time
 - Batch End Time
 - Phase ID
 - Phase Name
 - Phase Start Time
 - Phase End Time
 - Chrom Unit ID

"""

import os
import pandas as pd
from datetime import datetime, timedelta

from batch_context.batch_context_generator import BatchContextGenerator

def main():
    batch_context = BatchContextGenerator(template_path=os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv"))
    print(batch_context.phase_data)

    return


if __name__ == "__main__":
    main()