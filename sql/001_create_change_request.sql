-- Delta change request table: one row per change request ingested from the
-- Asset Inventory extract (Asset_Inventory.xlsx). Feeds validation_agent.writer.
CREATE TABLE IF NOT EXISTS metadata_discovery.validation_agent.change_request (
  change_request_id      STRING    COMMENT 'Unique change request id (CR-<batch>-<hash>)',
  ingestion_batch_id     STRING    COMMENT 'Ingestion run that produced the row',
  asset_id               STRING    COMMENT 'Asset key: platform|physical_name|sub_category|asset_group',
  src_file_name          STRING    COMMENT 'Source file name, e.g. Asset_Inventory.xlsx',
  received_at            TIMESTAMP COMMENT 'When the change request was received',
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
  date_inventory         TIMESTAMP,
  asset_last_modified    TIMESTAMP,
  sme                    STRING,
  asset_ware_status      STRING
)
USING DELTA
COMMENT 'Delta change requests built from the Asset Inventory source file';
