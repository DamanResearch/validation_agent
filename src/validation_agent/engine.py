import hashlib
import json
from datetime import datetime

from validation_agent.models import (
    REQUIRED_FIELDS,
    TRACKED_FIELDS,
    ChangeRequest,
    Classification,
    Decision,
    Outcome,
    RegistryRow,
    ValidationResult,
)

RETIRED_STATUSES = frozenset({"retired", "decommissioned"})


def metadata_hash(record: ChangeRequest | RegistryRow) -> str:
    payload = {field: getattr(record, field) for field in TRACKED_FIELDS}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate(request: ChangeRequest, current: RegistryRow | None) -> ValidationResult:
    missing = [f for f in REQUIRED_FIELDS if not getattr(request, f)]
    if missing:
        return ValidationResult(
            request_id=request.change_request_id,
            classification=Classification.VALIDATION_FAILED,
            findings=[f"missing required field: {f}" for f in missing],
            proposed_hash=None,
        )

    proposed = metadata_hash(request)
    status = (request.asset_ware_status or "").strip().lower()

    if current is None:
        classification = Classification.RETIRED if status in RETIRED_STATUSES else Classification.NEW
    elif status in RETIRED_STATUSES and not current.is_retired:
        classification = Classification.RETIRED
    elif proposed == current.metadata_hash:
        classification = Classification.UNCHANGED
    else:
        classification = Classification.CHANGED

    return ValidationResult(
        request_id=request.change_request_id,
        classification=classification,
        findings=[],
        proposed_hash=proposed,
    )


def decide(result: ValidationResult) -> Decision:
    if result.classification is Classification.VALIDATION_FAILED:
        return Decision.REJECTED
    if result.classification is Classification.UNCHANGED:
        return Decision.NO_CHANGE
    if result.classification is Classification.POSSIBLE_DUPLICATE:
        return Decision.REVIEW_REQUIRED
    return Decision.APPROVED


def plan_scd2(
    request: ChangeRequest,
    result: ValidationResult,
    current: RegistryRow | None,
    applied_at: datetime,
) -> tuple[RegistryRow | None, RegistryRow | None]:
    """Return (row_to_close, row_to_insert). Both are None for NO_CHANGE or REJECTED."""
    if decide(result) is not Decision.APPROVED:
        return None, None

    closed = None
    if current is not None:
        closed = current.model_copy(update={"effective_to": applied_at, "is_current": False})

    new_row = RegistryRow(
        registry_version_id=f"{request.asset_id}:{request.change_request_id}",
        asset_id=request.asset_id,
        asset_functional_name=request.asset_functional_name,
        asset_type=request.asset_type,
        platform=request.platform,
        asset_group=request.asset_group,
        asset_physical_name=request.asset_physical_name,
        bitbucket_location=request.bitbucket_location,
        report_group_status=request.report_group_status,
        asset_refresh_cadence=request.asset_refresh_cadence,
        sub_category=request.sub_category,
        business_domain=request.business_domain,
        sme=request.sme,
        asset_ware_status=request.asset_ware_status,
        metadata_hash=result.proposed_hash or "",
        applied_request_id=request.change_request_id,
        effective_from=applied_at,
        effective_to=None,
        is_current=True,
        is_retired=result.classification is Classification.RETIRED,
        created_at=applied_at,
    )
    return closed, new_row


def plan_batch(
    requests: list[ChangeRequest],
    current: dict[str, RegistryRow],
    applied_ids: set[str],
    applied_at: datetime,
) -> tuple[dict[str, RegistryRow], list[Outcome]]:
    """Return final row state keyed by registry_version_id, plus per-request outcomes."""
    current = dict(current)
    changes: dict[str, RegistryRow] = {}
    outcomes: list[Outcome] = []
    for request in requests:
        if request.change_request_id in applied_ids:
            continue
        existing = current.get(request.asset_id)
        result = validate(request, existing)
        decision = decide(result)
        outcomes.append(
            Outcome(
                change_request_id=request.change_request_id,
                classification=result.classification,
                decision=decision,
            )
        )
        if decision is not Decision.APPROVED:
            continue
        closed, new_row = plan_scd2(request, result, existing, applied_at)
        if closed is not None:
            changes[closed.registry_version_id] = closed
        changes[new_row.registry_version_id] = new_row
        current[request.asset_id] = new_row
    return changes, outcomes
