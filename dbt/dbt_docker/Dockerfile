FROM python:3.11-slim

# Prevents Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Forces logs to be flushed immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /dbt

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dbt
RUN pip install --no-cache-dir \
    dbt-core==1.11.0-rc3 \
    dbt-snowflake==1.10.4

# Copy dbt project
COPY chrom_stream/ /dbt/

# Create runtime profiles directory
RUN mkdir -p /root/.dbt

# Copy template (will be rendered at runtime)
COPY profiles.yml.template /root/.dbt/profiles.yml

ENTRYPOINT ["dbt"]
