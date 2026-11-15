-- Post-load checks for the Asset Inventory batch. Replace the batch id if you load a different run.

-- Expect 0 rows: asset keys that appear more than once in this batch
SELECT asset_id, COUNT(*) AS n
FROM metadata_discovery.validation_agent.change_request
WHERE ingestion_batch_id = 'INV-2026-11-15'
GROUP BY asset_id
HAVING COUNT(*) > 1;

-- Expect 0 rows: change requests written more than once
SELECT change_request_id, COUNT(*) AS n
FROM metadata_discovery.validation_agent.change_request
GROUP BY change_request_id
HAVING COUNT(*) > 1;

-- Informational: rows the engine will reject at apply time because a required field is blank in the source
SELECT COUNT(*) AS rows_missing_required_fields
FROM metadata_discovery.validation_agent.change_request
WHERE ingestion_batch_id = 'INV-2026-11-15'
  AND (asset_type IS NULL OR asset_functional_name IS NULL OR platform IS NULL);
