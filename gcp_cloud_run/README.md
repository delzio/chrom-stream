GCP Cloud Run services to consume pub/sub trend messages and write to InfluxDB and GCS
- 

### Description

This project is split into gcs_consumer and influx_consumer components each with python scripts, requirements, and Dockerfiles for Cloud Run setup.

### GCS Consumer

This consumes the messages generated from the time_series_trends python data generator, batches the data every 15 minutes, and submits the batched data as parquet files to a GCS bucket

### Influx Consumer

This consumes the messages generated from the time_series_trends python data generator and writes each data point into InfluxDB for real time streaming