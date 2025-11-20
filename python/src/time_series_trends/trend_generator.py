import pandas as pd
import numpy as np
import time

class TrendGenerator:
    """
    Data generation functions for simulating real-time chromatography sensor data streaming

    Params:
        template_path (str): Path to the template CSV file for generating data
        noise_def (dict): Dictionary defining noise characteristics for each sensor column
        noise_scale (float): Scaling factor for the noise to be applied
        holds (bool): Whether to include hold periods in the generated data

    Methods:
        generate_dataset: Creates full simulated chromatography trend data
        get_stream_generator: Generator function to stream simulated chromatography trend data
    """
    
    def __init__(self, template_path, noise_def=None, noise_scale=1.0, holds=True):
        self.template_data = pd.read_csv(template_path)
        if holds is False:
            self.template_data = self.template_data[self.template_data["flow_setpoint_L_min"] > 0]
            # reset time_min to 0.5 minute increments without holds
            self.template_data["time_min"] = np.arange(0, len(self.template_data) * 0.5, 0.5)
        self.noise_def = noise_def or {
            "uv_mau": (0, 2.0),
            "cond_mScm": (0, 0.15),
            "ph": (0, 0.01),
            "flow_mL_min": (0, 300),
            "pressure_bar": (0, 0.01)
        }
        self.noise_scale = noise_scale

    def generate_dataset(self, trend_resolution_hz=1.0):
        """
        Creates pre-defined simulated chromatography trend data at specified frequency and noise from class template_data.
        """

        # create new target time axis at specified frequency
        total_time_sec = int(self.template_data["time_min"].iloc[-1] * 60)
        dt = 1.0 / trend_resolution_hz
        time_sec = np.arange(0, total_time_sec + dt, dt)
        df_interp = pd.DataFrame({"time_sec": time_sec})
        df_interp["time_min"] = df_interp["time_sec"] / 60.0

        # interpolate sensor columns from template data
        sensor_cols = list(self.noise_def.keys())
        for col in sensor_cols:
            if col not in self.template_data.columns:
                raise KeyError(f"Column '{col}' not found in template data. Please check that noise_def keys match template columns.")
            df_interp[col] = np.interp(df_interp["time_sec"], 
                                       self.template_data["time_min"] * 60.0, 
                                       self.template_data[col])
            
        # add noise based on defined noise levels
        rng = np.random.default_rng()
        for col, (mean, stddev) in self.noise_def.items():
            df_interp[col] += self.noise_scale * rng.normal(mean, stddev, len(df_interp))
            
        # Adjust random values to within realistic ranges
        df_interp["ph"] = df_interp["ph"].clip(2.0, 12.0)
        df_interp["cond_mScm"] = df_interp["cond_mScm"].clip(0.1, 120.0)

        # store the simulated data in the instance
        return df_interp
    
    @staticmethod
    def get_stream_generator(simulated_data, test_mode=False):
        """
        Generator function to stream simulated chromatography trend data at specified frequency
        """

        # Create generator of values from simulated_data
        for n, row in simulated_data.iterrows():
            yield row.to_dict()
            if test_mode and n >= 5:
                break
