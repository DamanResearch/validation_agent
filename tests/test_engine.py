from datetime import datetime, timezone

from validation_agent.engine import decide, metadata_hash, plan_scd2, validate
from validation_agent.models import ChangeRequest, Classification, Decision, RegistryRow

NOW = datetime(2026, 11, 12, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 13, tzinfo=timezone.utc)


def make_request(**overrides) -> ChangeRequest:
    base = dict(
        change_request_id="CR-001",
        ingestion_batch_id="RUN-1",
        asset_id="TBL-100",
        src_file_name="reports.xlsx",
        received_at=NOW,
        asset_functional_name="Daily Sales",
        asset_type="Tableau Report",
        platform="Tableau",
        asset_group="HR",
        sme="a@b.com",
        asset_ware_status="active",
    )
    base.update(overrides)
    return ChangeRequest(**base)


def registry_from(request: ChangeRequest, request_id: str = "CR-000") -> RegistryRow:
    from validation_agent.models import TRACKED_FIELDS

    values = {f: getattr(request, f) for f in TRACKED_FIELDS}
    return RegistryRow(
        registry_version_id=f"{request.asset_id}:{request_id}",
        asset_id=request.asset_id,
        **values,
        metadata_hash=metadata_hash(request),
        applied_request_id=request_id,
        effective_from=NOW,
        effective_to=None,
        is_current=True,
        is_retired=False,
        created_at=NOW,
    )


def test_new_asset_is_approved_and_inserted():
    req = make_request()
    result = validate(req, None)
    assert result.classification is Classification.NEW
    closed, new_row = plan_scd2(req, result, None, LATER)
    assert closed is None
    assert new_row.is_current and new_row.effective_to is None


def test_unchanged_request_writes_nothing():
    req = make_request()
    current = registry_from(req)
    result = validate(req, current)
    assert result.classification is Classification.UNCHANGED
    assert decide(result) is Decision.NO_CHANGE
    assert plan_scd2(req, result, current, LATER) == (None, None)


def test_changed_name_closes_old_row_and_opens_new():
    original = make_request()
    current = registry_from(original)
    changed = make_request(change_request_id="CR-002", asset_functional_name="Daily Sales v2")
    result = validate(changed, current)
    assert result.classification is Classification.CHANGED
    closed, new_row = plan_scd2(changed, result, current, LATER)
    assert closed.is_current is False and closed.effective_to == LATER
    assert new_row.is_current is True and new_row.effective_from == LATER
    assert new_row.effective_to is None


def test_missing_required_field_fails_validation():
    req = make_request(platform=None)
    result = validate(req, None)
    assert result.classification is Classification.VALIDATION_FAILED
    assert decide(result) is Decision.REJECTED


def test_retired_status_creates_tombstone():
    original = make_request()
    current = registry_from(original)
    retired = make_request(change_request_id="CR-003", asset_ware_status="Retired")
    result = validate(retired, current)
    assert result.classification is Classification.RETIRED
    _, tombstone = plan_scd2(retired, result, current, LATER)
    assert tombstone.is_retired is True and tombstone.is_current is True


def test_hash_ignores_non_tracked_fields():
    a = make_request(src_file_name="one.xlsx")
    b = make_request(src_file_name="two.xlsx", ingestion_batch_id="RUN-9")
    assert metadata_hash(a) == metadata_hash(b)
