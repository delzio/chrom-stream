import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class BatchContextGenerator:
    """
    Data generation functions for simulating batch context data streaming

    Params:
        template_path (str): Path to the template CSV file for generating data
    """

    def __init__(self, template_path: str, recipe_name: str, batch_id: str, chrom_id: str, execution_time: datetime, holds: bool=True):
        self.template_data = pd.read_csv(template_path)
        if holds is False:
            self.template_data = self.template_data[self.template_data["flow_setpoint_L_min"] > 0]
            # reset time_min to 0.5 minute increments without holds
            self.template_data["time_min"] = np.arange(0, len(self.template_data) * 0.5, 0.5)
        self.recipe_name = recipe_name
        self.batch_id = batch_id
        self.chrom_id = chrom_id
        self.batch_ts = {
            "batch_id": self.batch_id,
            "start_ts": execution_time + timedelta(seconds=min(self.template_data["time_min"]) * 60),
            "end_ts": execution_time + timedelta(seconds=max(self.template_data["time_min"]) * 60)
        }
        self.phase_ts = self._generate_phase_data(execution_time=execution_time)
    
    def _generate_phase_data(self, execution_time):
        """
        Creates pre-defined simulated phase context data templated from template_data.
        """

        grouped_phases = self.template_data.groupby("phase").agg(
            phase_start_min=("time_min", "min"),
            phase_end_min=("time_min", "max")
        ).reset_index()

        grouped_phases["start_ts"] = [execution_time + timedelta(seconds=start_min * 60) for start_min in grouped_phases["phase_start_min"]]
        grouped_phases["end_ts"] = [execution_time + timedelta(seconds=end_min * 60) for end_min in grouped_phases["phase_end_min"]]
        grouped_phases = grouped_phases[["phase", "start_ts", "end_ts"]]

        return grouped_phases.sort_values("start_ts").reset_index(drop=True)