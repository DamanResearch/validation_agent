from datetime import datetime, timezone

from validation_agent.engine import plan_batch
from validation_agent.models import Classification, Decision, RegistryRow
from tests.test_engine import LATER, NOW, make_request, registry_from


def test_two_changes_same_asset_in_one_batch_leave_one_current_row():
    original = make_request(change_request_id="CR-000")
    current = {original.asset_id: registry_from(original, "CR-000")}
    first = make_request(change_request_id="CR-001", asset_functional_name="Name A")
    second = make_request(change_request_id="CR-002", asset_functional_name="Name B")

    changes, outcomes = plan_batch([first, second], current, {"CR-000"}, LATER)

    current_rows = [row for row in changes.values() if row.is_current]
    assert len(current_rows) == 1
    assert current_rows[0].applied_request_id == "CR-002"
    assert changes[f"{original.asset_id}:CR-000"].is_current is False
    assert [o.decision for o in outcomes] == [Decision.APPROVED, Decision.APPROVED]


def test_already_applied_requests_are_skipped():
    request = make_request(change_request_id="CR-001")
    changes, outcomes = plan_batch([request], {}, {"CR-001"}, LATER)
    assert changes == {}
    assert outcomes == []


def test_rejected_request_produces_outcome_but_no_writes():
    bad = make_request(change_request_id="CR-009", platform=None)
    changes, outcomes = plan_batch([bad], {}, set(), LATER)
    assert changes == {}
    assert outcomes[0].classification is Classification.VALIDATION_FAILED
    assert outcomes[0].decision is Decision.REJECTED


def test_new_then_unchanged_in_same_batch_writes_only_the_new_row():
    request = make_request(change_request_id="CR-001")
    repeat = make_request(change_request_id="CR-002")
    changes, outcomes = plan_batch([request, repeat], {}, set(), NOW)
    assert len(changes) == 1
    assert outcomes[1].classification is Classification.UNCHANGED
    assert outcomes[1].decision is Decision.NO_CHANGE
