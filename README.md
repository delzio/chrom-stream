Enable GCP APIs:
Storage API
Eventarc API
Cloudbuild API
CloudComposer API
SecretManager API

Cannot create service accounts from terraform so must create it for dbt_srvc_account and tf_srvc_account in snowflake manually

Create
.google/credentials/gcp.json
.snowflake/credentials/
 -> openssl genrsa -out snowflake_tf_key.pem 2048
 -> openssl rsa -in snowflake_tf_key.pem -pubout -out snowflake_tf_key.pub
 -> openssl pkcs8 -topk8 -inform PEM -outform DER \
    -in snowflake_tf_key.pem \
    -out snowflake_tf_key.der \
    -nocrypt
 -> base64 -w 0 snowflake_tf_key.der > snowflake_tf_key.b64

 -> openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out snowflake_dbt_key.p8
 -> openssl rsa -in snowflake_dbt_key.p8 -pubout -out snowflake_dbt_key.pub

Add contents of snowflake_dbt_key.b64 to SecretManager
Grant Cloud Compute Service Account Secret Manager Secret Accessor

OR just use airflow's connection manager
