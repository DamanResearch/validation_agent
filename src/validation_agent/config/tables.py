from validation_agent.config.settings import settings

CHANGE_REQUEST_DDL = f"""
CREATE TABLE IF NOT EXISTS {settings.fq}.change_request (
  change_request_id STRING,
  ingestion_batch_id STRING,
  asset_id STRING,
  src_file_name STRING,
  received_at TIMESTAMP,
  asset_functional_name STRING,
  asset_type STRING,
  platform STRING,
  asset_group STRING,
  asset_physical_name STRING,
  bitbucket_location STRING,
  report_group_status STRING,
  asset_refresh_cadence STRING,
  sub_category STRING,
  business_domain STRING,
  date_inventory TIMESTAMP,
  asset_last_modified TIMESTAMP,
  sme STRING,
  asset_ware_status STRING
) USING DELTA
"""

ASSET_REGISTRY_DDL = f"""
CREATE TABLE IF NOT EXISTS {settings.fq}.asset_registry (
  registry_version_id STRING,
  asset_id STRING,
  asset_functional_name STRING,
  asset_type STRING,
  platform STRING,
  asset_group STRING,
  asset_physical_name STRING,
  bitbucket_location STRING,
  report_group_status STRING,
  asset_refresh_cadence STRING,
  sub_category STRING,
  business_domain STRING,
  sme STRING,
  asset_ware_status STRING,
  metadata_hash STRING,
  applied_request_id STRING,
  effective_from TIMESTAMP,
  effective_to TIMESTAMP,
  is_current BOOLEAN,
  is_retired BOOLEAN,
  created_at TIMESTAMP
) USING DELTA
"""

ALL_DDL = [CHANGE_REQUEST_DDL, ASSET_REGISTRY_DDL]
