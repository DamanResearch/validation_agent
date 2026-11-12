from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Classification(str, Enum):
    NEW = "NEW"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"
    RETIRED = "RETIRED"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class Decision(str, Enum):
    APPROVED = "APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    NO_CHANGE = "NO_CHANGE"


TRACKED_FIELDS: tuple[str, ...] = (
    "asset_functional_name",
    "asset_type",
    "platform",
    "asset_group",
    "asset_physical_name",
    "bitbucket_location",
    "report_group_status",
    "asset_refresh_cadence",
    "sub_category",
    "business_domain",
    "sme",
    "asset_ware_status",
)

REQUIRED_FIELDS: tuple[str, ...] = ("asset_id", "asset_type", "asset_functional_name", "platform")


class ChangeRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    change_request_id: str
    ingestion_batch_id: str
    asset_id: str
    src_file_name: str
    received_at: datetime
    asset_functional_name: str | None = None
    asset_type: str | None = None
    platform: str | None = None
    asset_group: str | None = None
    asset_physical_name: str | None = None
    bitbucket_location: str | None = None
    report_group_status: str | None = None
    asset_refresh_cadence: str | None = None
    sub_category: str | None = None
    business_domain: str | None = None
    date_inventory: datetime | None = None
    asset_last_modified: datetime | None = None
    sme: str | None = None
    asset_ware_status: str | None = None


class RegistryRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    registry_version_id: str
    asset_id: str
    asset_functional_name: str | None
    asset_type: str | None
    platform: str | None
    asset_group: str | None
    asset_physical_name: str | None
    bitbucket_location: str | None
    report_group_status: str | None
    asset_refresh_cadence: str | None
    sub_category: str | None
    business_domain: str | None
    sme: str | None
    asset_ware_status: str | None
    metadata_hash: str
    applied_request_id: str
    effective_from: datetime
    effective_to: datetime | None
    is_current: bool
    is_retired: bool
    created_at: datetime


class ValidationResult(BaseModel):
    request_id: str
    classification: Classification
    findings: list[str]
    proposed_hash: str | None
