This is a python project that simulates large scale chromatography data generation
- 

### Description

This project is split into 3 smaller projects which can each run independently for testing purposes.
The intention is to run all 3 projects in parallel to mimic data generation from 3 unique sources.

Batch Context:
- Generates batch context data simulating an automation batch record historian
- Data generated:
    - Automation Recipe Name
    - Batch IDs
    - Equipment IDs
    - Batch Start/End Times
    - Phase Names
    - Phase Start/End Times

Live Trends:
- Generates time-series trend data simulating equipment sensor readings for a chromatography unit
- Trends generated:
    - UV (mAU)
    - Conductivity (mScm)
    - pH
    - Flow Rate (mL/min)
    - Pressure (bar)

Sample Results:
- Generates json files of sample concentration results simulating SoloVPE measurement results for a sample
- Data generated:
    - Sample metadata
    - Instrument metadata
    - Raw absorbance data
    - Sample Concentration (mg/mL)


### How to Run

Test Run (quick, print data to console only):

1. cd into chrom-stream/python_data_generation
2. Test with:
    ```bash
    PYTHONPATH=src python src/main.py --quick_run
    ```
3. Watch as generated data will start to print to console
4. Cancel with CTRL + C


Production Run:

WARNING: this will send data to your GCP project, be cognicent of the amount of data you are sending to GCP and the associated cloud storage costs
1. cd into chrom-stream/python_data_generation
2. adjust argument settings in config.yml
3. Run with:
    ```bash
    PYTHONPATH=src python src/main.py --config src/config.yml
    ```
4. Data will start flowing into GCP
5. Cancel with CTRL + C


Testing Data Generation Modules Individually:

1. cd into chrom-stream/python_data_generation
2. Quick-run test with:
    ```bash
    PYTHONPATH=src python src/<module i.e. batch_context>/main.py --quick_run
    ```
3. Test with writing to GCP with:
    ```bash
    PYTHONPATH=src python src/<module i.e. batch_context>/main.py --config src/<module i.e. batch_context>/config.yml
    ```
4. Cancel with CTRL + C