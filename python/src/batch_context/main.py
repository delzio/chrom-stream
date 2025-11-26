import os
import yaml
import argparse
import time
from datetime import datetime, timedelta, timezone

from batch_context.batch_context_generator import BatchContextGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="Batch Context Data Generation Simulator")
    parser.add_argument('--config', type=str, default=None, help='Path to YAML configuration file')
    parser.add_argument('--quick_run', action='store_true', help='Run in quick mode for testing')

    return parser.parse_args()

def load_config(config_path):
    with open(config_path) as file:
        return yaml.safe_load(file)
    
def main():

    args = parse_args()
    if args.quick_run:
        config = {}
        config["number_of_runs"] = 4
        config["column_ids"] = ["chrom_1", "chrom_2", "chrom_3", "chrom_4"]
        config["batch_delay_sec"] = 60
        config["stream_rate_adjust_factor"] = 1000
    elif args.config:
        config = load_config(args.config)
    else:
        raise ValueError("Either --config must be provided or --quick_run must be set.")

    config["execution_time"] = datetime.now(timezone.utc)
    template_path=os.path.join(os.getenv("PYTHONPATH"),"data","good_trend_template.csv")

    build_batch_args = {key: val for key, val in config.items() 
                        if key in ["number_of_runs", "column_ids", "execution_time", "batch_delay_sec"]}
    build_batch_args["template_path"] = template_path
    batch_context, phase_generators = build_batch_context(**build_batch_args)

    generate_events_args = {key: val for key, val in config.items() 
                            if key in ["number_of_runs", "stream_rate_adjust_factor", "batch_delay_sec"]}
    generate_events_args["batch_context"] = batch_context
    generate_events_args["phase_generators"] = phase_generators
    generate_batch_context_events(**generate_events_args)

    return

def build_batch_context(number_of_runs, column_ids, template_path, execution_time, batch_delay_sec):
    """ Generate batch context dataset """
    
    batch_context = {}
    phase_generators = {}

    # Collect Batch Data
    batch_id = 0
    for run in range(number_of_runs):
        for col in column_ids:
            batch_id += 1
            if run == 0:
                batch_start_ts = execution_time
                batch_context[col] = []
                phase_generators[col] = []
            else:
                batch_start_ts = batch_context[col][run-1].simulated_batch_data.iloc[-1]["event_ts"] + timedelta(seconds=batch_delay_sec)
            cur_batch_context = BatchContextGenerator(template_path=template_path, recipe_name="affinity_chrom_v1", 
                                                      batch_id=batch_id, chrom_id=col, execution_time=batch_start_ts)
            cur_phase_generator = BatchContextGenerator.get_event_generator(cur_batch_context.simulated_phase_data)
            batch_context[col].append(cur_batch_context)
            phase_generators[col].append(cur_phase_generator)

    return batch_context, phase_generators

def generate_batch_context_events(number_of_runs, batch_context, phase_generators, stream_rate_adjust_factor, batch_delay_sec):
    for run in range(number_of_runs):
        active_generators = []
        for col_key, gen_list in phase_generators.items():
            gen = gen_list[run]
            active_generators.append((col_key, gen))
        
        streaming = True
        while streaming:
            streaming = False

            for col_key, gen in active_generators:
                try:
                    phase_event = next(gen)
                    batch_data = batch_context[col_key][run].simulated_batch_data
                    batch_event = batch_data[batch_data["event_ts"] == phase_event["event_ts"]]
                    if not batch_event.empty:
                        print(f"batch data for {col_key}: {batch_event}")
                    print(f"phase data for {col_key}: {phase_event}")

                    phase_data = batch_context[col_key][run].simulated_phase_data
                    cur_phase_idx = phase_data.index[
                        phase_data["event_ts"] == phase_event["event_ts"]
                    ]
                    streaming = True
                except StopIteration:
                    continue
            
            try:
                time_delay = phase_data["event_ts"].iloc[cur_phase_idx[0] + 1] - phase_data["event_ts"].iloc[cur_phase_idx[0]]
                time.sleep(time_delay.total_seconds() / stream_rate_adjust_factor)
            except IndexError:
                break

        time.sleep(batch_delay_sec)

if __name__ == "__main__":
    main()