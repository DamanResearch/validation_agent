from dataclasses import dataclass
from datetime import datetime

from delta.tables import DeltaTable
from pyspark.sql import SparkSession

from validation_agent.config.settings import settings
from validation_agent.engine import decide, plan_scd2, validate
from validation_agent.models import ChangeRequest, Decision, RegistryRow


@dataclass(frozen=True)
class Outcome:
    change_request_id: str
    classification: str
    decision: str


def load_requests(spark: SparkSession) -> list[ChangeRequest]:
    rows = spark.table(f"{settings.fq}.change_request").orderBy("received_at").collect()
    return [ChangeRequest(**row.asDict()) for row in rows]


def apply_requests(
    spark: SparkSession,
    requests: list[ChangeRequest],
    applied_at: datetime,
) -> list[Outcome]:
    registry = spark.table(f"{settings.fq}.asset_registry")
    current = {
        row.asset_id: RegistryRow(**row.asDict())
        for row in registry.where("is_current").collect()
    }
    applied_ids = {row.applied_request_id for row in registry.select("applied_request_id").collect()}

    changes: dict[str, RegistryRow] = {}
    outcomes: list[Outcome] = []
    for request in requests:
        if request.change_request_id in applied_ids:
            continue
        result = validate(request, current.get(request.asset_id))
        decision = decide(result)
        closed, new_row = plan_scd2(request, result, current.get(request.asset_id), applied_at)
        outcomes.append(
            Outcome(request.change_request_id, result.classification.value, decision.value)
        )
        if decision is not Decision.APPROVED:
            continue
        if closed is not None:
            changes[closed.registry_version_id] = closed
        changes[new_row.registry_version_id] = new_row
        current[request.asset_id] = new_row

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
    return outcomes
