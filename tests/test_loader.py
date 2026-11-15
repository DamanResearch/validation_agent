import pytest

from validation_agent.models import ChangeRequest

pytest.importorskip("pyspark")

from validation_agent.loader import SOURCE_COLUMN_MAP, TIMESTAMP_SOURCE_MAP  # noqa: E402


def test_mapped_columns_exist_on_change_request():
    targets = set(SOURCE_COLUMN_MAP.values()) | set(TIMESTAMP_SOURCE_MAP.values())
    fields = set(ChangeRequest.model_fields)
    assert targets <= fields


def test_every_change_request_field_is_populated_or_derived():
    derived = {
        "change_request_id",
        "ingestion_batch_id",
        "asset_id",
        "src_file_name",
        "received_at",
        "bitbucket_location",
    }
    mapped = set(SOURCE_COLUMN_MAP.values()) | set(TIMESTAMP_SOURCE_MAP.values())
    assert set(ChangeRequest.model_fields) == mapped | derived
