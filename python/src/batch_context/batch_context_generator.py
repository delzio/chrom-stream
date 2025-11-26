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
        self.simulated_batch_data = self._generate_batch_data(recipe_name=recipe_name, batch_id=batch_id, chrom_id=chrom_id, execution_time=execution_time)
        self.simulated_phase_data = self._generate_phase_data(execution_time=execution_time)
    
    def _generate_batch_data(self, recipe_name, batch_id, chrom_id, execution_time):
        """ Creates pre-defined simulated batch context data template from template_data """

        batch_data = []
        for event in ["batch_start", "batch_end"]:
            if event == "batch_start":
                event_ts = execution_time + timedelta(seconds=min(self.template_data["time_min"]) * 60)
            else:
                event_ts = execution_time + timedelta(seconds=max(self.template_data["time_min"]) * 60)
            batch_data.append({
                "recipe_name": recipe_name,
                "batch_id": batch_id,
                "chrom_id": chrom_id,
                "event": event,
                "event_ts": event_ts
            })

        return pd.DataFrame(batch_data)

    def _generate_phase_data(self, execution_time):
        """Creates simulated phase context data templated from template_data."""
        
        agg = self.template_data.groupby("phase")["time_min"].agg(["min", "max"]).reset_index()

        records = []
        for event, col in [("phase_start", "min"), ("phase_end", "max")]:
            event_times = agg[col].values * 60  # seconds
            event_ts = [execution_time + timedelta(seconds=t) for t in event_times]

            records.append(
                pd.DataFrame({
                    "phase": agg["phase"],
                    "event": event,
                    "event_ts": event_ts
                })
            )

        phase_data = pd.concat(records, ignore_index=True)
        phase_data = phase_data.sort_values("event_ts").reset_index(drop=True)

        return phase_data

    @staticmethod
    def get_event_generator(simulated_phase_data, test_mode=False):
        """ Generator function to trace simulated batch context at specified frequency """

        # Create generator of values from simulated_data
        for n, row in simulated_phase_data.iterrows():
            yield row.to_dict()
            if test_mode and n >= 5:
                break