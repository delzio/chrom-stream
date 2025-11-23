import os
import numpy as np
import pandas as pd
from datetime import datetime, timezone
import json
import copy

class SampleResultGenerator:
    """
    Generate simluated SoloVPE Protein Concentration results
    """

    def __init__(self, template_path: str, noise_def: dict = None, noise_scale: float = 1.0):
        self.template_data = self._read_json(template_path=template_path)
        self.noise_def = noise_def or {
            # key: (sd mean, sd as ratio of abs value)
            "absorbance": (0, 0.05),
            "temperature": (0, 1.0)
        }
        self.noise_scale = noise_scale

    
    def _read_json(self, template_path):
        """ read json template """
        with open(template_path) as file:
            template_data = json.load(file)
            
        return template_data
    
    def _calculate_trend_params(self, raw_data):
        """ calculate raw data slope, intercept, and r-square """
        
        # slope
        n = len(raw_data)
        sum_pathlength = 0
        sum_absorbance = 0
        sum_pathlength_squared = 0
        sum_pathlength_absorbace = 0
        for data_point in raw_data:
            sum_pathlength += data_point["pathlength_mm"]
            sum_absorbance += data_point["absorbance"]
            sum_pathlength_squared += data_point["pathlength_mm"]**2
            sum_pathlength_absorbace += (data_point["pathlength_mm"] * data_point["absorbance"])
        
        numerator = (n * sum_pathlength_absorbace - sum_pathlength * sum_absorbance)
        denominator = (n * sum_pathlength_squared - sum_pathlength**2)
        if denominator == 0:
            raise ValueError("Error in slope calculation: denominator cannot equate to 0.")
        slope = numerator / denominator

        # intercept
        mean_absorbance = sum_absorbance / n
        mean_pathlength = sum_pathlength / n
        intercept = mean_absorbance - slope * mean_pathlength

        # r-square
        ss_res = 0
        ss_tot = 0
        for data_point in raw_data:
            predicted_absorbance = data_point["pathlength_mm"] * slope + intercept
            ss_res += (data_point["absorbance"] - predicted_absorbance)**2
            ss_tot += (data_point["absorbance"] - mean_absorbance)**2
        if ss_tot == 0:
            raise ValueError("Error in r-square calculation: denominator cannot equate to 0.")
        r_square = 1 - ss_res / ss_tot

        trend_params = {
            "n": n,
            "slope": slope,
            "intercept": intercept,
            "r_square": r_square
        }

        return trend_params

    
    def generate_result(self, instrument_id: str, sample_id: str, sample_type: str, batch_id: str, measurement_ts: datetime, target_titer: float, bad_run: bool = False):
        rng = np.random.default_rng()

        # initialize scan_result data
        simulated_data = copy.deepcopy(self.template_data)
        simulated_data["system_status"]["scan_result"] = "fail"
        
        # generate simulated metadata
        simulated_data["instrument"]["id"] = instrument_id
        simulated_data["sample_metadata"] = {
            "sample_id": sample_id,
            "sample_type": sample_type,
            "batch_id": batch_id
        }
        simulated_data["run_metadata"]["date"] = datetime.strftime(measurement_ts, "%Y-%m-%dT%H:%M:%SZ")
        simulated_data["run_metadata"]["temperature_c"] = simulated_data["run_metadata"]["temperature_c"] + rng.normal(self.noise_def["temperature"][0], self.template_data["run_metadata"]["temperature_c"] * (1 + self.noise_def["temperature"][1]))

        # correct pathlength and absorbance readings for target titer
        if target_titer != 1:
            simulated_data["run_metadata"]["pathlength_range_mm"]["min"] = simulated_data["run_metadata"]["pathlength_range_mm"]["min"] / target_titer
            simulated_data["run_metadata"]["pathlength_range_mm"]["max"] = simulated_data["run_metadata"]["pathlength_range_mm"]["max"] / target_titer
                
        # generate simulated raw data 
        for data_point in simulated_data["measurement"]["raw_data_points"]:
            if target_titer != 1:
                data_point["pathlength_mm"]  = data_point["pathlength_mm"] / target_titer
            data_point["absorbance"] = data_point["absorbance"] + rng.normal(self.noise_def["absorbance"][0], data_point["absorbance"] * (1 + self.noise_def["absorbance"][1]))

        # generate calculated results
        try:
            trend_params = self._calculate_trend_params(raw_data=simulated_data["measurement"]["raw_data_points"])

            simulated_data["measurement"]["linear_regression"] = {
                "slope_abs_per_mm": trend_params["slope"],
                "intercept": trend_params["intercept"],
                "r_squared": trend_params["r_square"],
                "num_points_used": trend_params["n"]
            }

            simulated_data["measurement"]["concentration"]["protein_concentration_mg_mL"] = trend_params["slope"] / 1.45

            simulated_data["system_status"]["scan_result"] = "success"
        except ValueError as e:
            simulated_data["system_status"]["errors"].append(str(e))

        return simulated_data