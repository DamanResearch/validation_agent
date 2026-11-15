-- Asset registry: SCD Type 2 history of approved asset metadata.
-- Exactly one current row per asset_id (is_current = true) once changes are applied.
CREATE TABLE IF NOT EXISTS metadata_discovery.validation_agent.asset_registry (
  registry_version_id    STRING    COMMENT '<asset_id>:<change_request_id>',
  asset_id               STRING,
  asset_functional_name  STRING,
  asset_type             STRING,
  platform               STRING,
  asset_group            STRING,
  asset_physical_name    STRING,
  bitbucket_location     STRING,
  report_group_status    STRING,
  asset_refresh_cadence  STRING,
  sub_category           STRING,
  business_domain        STRING,
  sme                    STRING,
  asset_ware_status      STRING,
  metadata_hash          STRING    COMMENT 'SHA-256 over TRACKED_FIELDS',
  applied_request_id     STRING,
  effective_from         TIMESTAMP,
  effective_to           TIMESTAMP,
  is_current             BOOLEAN,
  is_retired             BOOLEAN,
  created_at             TIMESTAMP
)
USING DELTA
COMMENT 'SCD2 asset registry maintained by validation_agent';
