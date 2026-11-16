import uuid
from datetime import datetime

from delta.tables import DeltaTable
from pyspark.sql import SparkSession

from validation_agent.config.settings import settings
from validation_agent.engine import plan_batch
from validation_agent.models import ChangeRequest, Outcome, RegistryRow


def load_requests(spark: SparkSession) -> list[ChangeRequest]:
    rows = spark.table(f"{settings.fq}.change_request").orderBy("received_at").collect()
    return [ChangeRequest(**row.asDict()) for row in rows]


def apply_requests(
    spark: SparkSession,
    requests: list[ChangeRequest],
    applied_at: datetime,
) -> list[Outcome]:
    registry = spark.table(f"{settings.fq}.asset_registry")
    rows = registry.collect()
    current = {row.asset_id: RegistryRow(**row.asDict()) for row in rows if row.is_current}
    applied_ids = {row.applied_request_id for row in rows}

    changes, outcomes = plan_batch(requests, current, applied_ids, applied_at)

    if changes:
        staged = spark.createDataFrame(
            [row.model_dump() for row in changes.values()], schema=registry.schema
        )
        (
            DeltaTable.forName(spark, f"{settings.fq}.asset_registry")
            .alias("t")
            .merge(staged.alias("s"), "t.registry_version_id = s.registry_version_id")
            .whenMatchedUpdate(set={"effective_to": "s.effective_to", "is_current": "s.is_current"})
            .whenNotMatchedInsertAll()
            .execute()
        )

    if outcomes:
        audit = spark.table(f"{settings.fq}.audit_event")
        audit_rows = [
            {
                "event_id": str(uuid.uuid4()),
                "change_request_id": outcome.change_request_id,
                "event_type": outcome.decision.value,
                "classification": outcome.classification.value,
                "decision": outcome.decision.value,
                "occurred_at": applied_at,
            }
            for outcome in outcomes
        ]
        spark.createDataFrame(audit_rows, schema=audit.schema).write.insertInto(
            f"{settings.fq}.audit_event"
        )
    return outcomes
