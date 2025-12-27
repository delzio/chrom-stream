Enable GCP APIs:
Storage API
Eventarc API
Cloudbuild API
CloudComposer API
SecretManager API

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

 -> openssl genrsa -out snowflake_dbt_key.pem 2048
 -> openssl rsa -in snowflake_dbt_key.pem -pubout -out snowflake_dbt_key.pub
 -> base64 -w 0 snowflake_dbt_key.pem > snowflake_dbt_key.b64

Add contents of snowflake_dbt_key.b64 to SecretManager
Grant Cloud Compute Service Account Secret Manager Secret Accessor
