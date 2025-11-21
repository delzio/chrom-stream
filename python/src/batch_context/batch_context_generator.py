import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class BatchContextGenerator:
    """
    Data generation functions for simulating batch context data streaming

    Params:
        template_path (str): Path to the template CSV file for generating data
    """

    def __init__(self, template_path, holds=True):
        self.template_data = pd.read_csv(template_path)
        if holds is False:
            self.template_data = self.template_data[self.template_data["flow_setpoint_L_min"] > 0]
            # reset time_min to 0.5 minute increments without holds
            self.template_data["time_min"] = np.arange(0, len(self.template_data) * 0.5, 0.5)
        self.phase_data = self._generate_dataset()

    def _generate_dataset(self):
        """
        Creates pre-defined simulated batch context data templated from template_data.
        """

        grouped_phases = self.template_data.groupby("phase").agg(
            phase_start_min=("time_min", "min"),
            phase_end_min=("time_min", "max")
        ).reset_index()

        grouped_phases["phase_start_sec"] = grouped_phases["phase_start_min"] * 60
        grouped_phases["phase_end_sec"] = grouped_phases["phase_end_min"] * 60

        return grouped_phases.sort_values("phase_start_sec")