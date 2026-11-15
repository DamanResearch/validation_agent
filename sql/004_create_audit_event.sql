-- Audit log: one row per decided change request (written by validation_agent.writer).
CREATE TABLE IF NOT EXISTS metadata_discovery.validation_agent.audit_event (
  event_id           STRING,
  change_request_id  STRING,
  event_type         STRING,
  classification     STRING,
  decision           STRING,
  occurred_at        TIMESTAMP
)
USING DELTA
COMMENT 'One audit row per decided change request';
