"""Load the Asset Inventory CSV extract into validation_agent.change_request.

Source: Asset_Inventory.xlsx (sheet Reporting_Asset), exported to CSV with the
original header row. Each source row becomes one change request.

Run on a cluster or serverless compute:
    spark-submit loader.py --csv-path /Workspace/.../asset_inventory_rows.csv
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from validation_agent.config.settings import settings

CHANGE_REQUEST_TABLE = f"{settings.fq}.change_request"
TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ss"
DEFAULT_BATCH_ID = "INV-2026-11-15"
DEFAULT_SRC_FILE = "Asset_Inventory.xlsx"

# CSV header (source spreadsheet column) -> change_request column.
SOURCE_COLUMN_MAP: dict[str, str] = {
    "ASSET FUNCTIONAL NAME": "asset_functional_name",
    "ASSET TYPE": "asset_type",
    "PLATFORM": "platform",
    "ASSET GROUP": "asset_group",
    "ASSET PHYSICAL NAME": "asset_physical_name",
    "REPORT GROUP STATUS": "report_group_status",
    "ASSET WARE STATUS": "asset_ware_status",
    "ASSET REFRESH CADENCE": "asset_refresh_cadence",
    "SUBCATEGORY": "sub_category",
    "BUSINESS DOMAIN": "business_domain",
    "SME": "sme",
}

TIMESTAMP_SOURCE_MAP: dict[str, str] = {
    "DATE INVENTORY": "date_inventory",
    "ASSET LAST MODIFIED": "asset_last_modified",
}


def _clean(column: str) -> F.Column:
    """Trim a source column and turn blank cells into NULL."""
    value = F.trim(F.col(f"`{column}`"))
    return F.when(value == "", F.lit(None)).otherwise(value)


def read_inventory_csv(spark: SparkSession, csv_path: str) -> DataFrame:
    return (
        spark.read.option("header", True)
        .option("escape", '"')
        .option("multiLine", True)
        .csv(csv_path)
    )


def to_change_requests(
    raw: DataFrame,
    batch_id: str,
    src_file_name: str,
    received_at: datetime,
) -> DataFrame:
    """Map source rows to change_request rows, in the table's column order."""
    rows = raw.where(_clean("ASSET FUNCTIONAL NAME").isNotNull())

    # Natural key of the inventory row. Unique across the current extract.
    asset_id = F.concat_ws(
        "|",
        F.coalesce(_clean("PLATFORM"), F.lit("")),
        F.coalesce(_clean("ASSET PHYSICAL NAME"), F.lit("")),
        F.coalesce(_clean("SUBCATEGORY"), F.lit("")),
        F.coalesce(_clean("ASSET GROUP"), F.lit("")),
    )
    # Deterministic id: rerunning the load produces the same ids, so duplicates are skipped.
    change_request_id = F.concat(
        F.lit(f"CR-{batch_id}-"),
        F.substring(
            F.sha2(F.concat_ws("|", asset_id, _clean("ASSET FUNCTIONAL NAME")), 256), 1, 12
        ),
    )

    columns = [
        change_request_id.alias("change_request_id"),
        F.lit(batch_id).alias("ingestion_batch_id"),
        asset_id.alias("asset_id"),
        F.lit(src_file_name).alias("src_file_name"),
        F.lit(received_at).cast("timestamp").alias("received_at"),
    ]
    columns += [_clean(src).alias(dst) for src, dst in SOURCE_COLUMN_MAP.items()]
    columns.append(F.lit(None).cast("string").alias("bitbucket_location"))
    columns += [
        F.to_timestamp(_clean(src), TIMESTAMP_FORMAT).alias(dst)
        for src, dst in TIMESTAMP_SOURCE_MAP.items()
    ]
    return rows.select(*columns)


def load_change_requests(
    spark: SparkSession,
    csv_path: str,
    batch_id: str = DEFAULT_BATCH_ID,
    src_file_name: str = DEFAULT_SRC_FILE,
    received_at: datetime | None = None,
) -> int:
    """Append new change requests to change_request. Returns the number of rows written."""
    received_at = received_at or datetime.now(timezone.utc)
    incoming = to_change_requests(
        read_inventory_csv(spark, csv_path), batch_id, src_file_name, received_at
    )

    # Idempotent: skip change requests that are already in the table.
    existing = spark.table(CHANGE_REQUEST_TABLE).select("change_request_id")
    new_rows = incoming.join(existing, on="change_request_id", how="left_anti")

    # Match the table's column order before inserting by position.
    table_columns = spark.table(CHANGE_REQUEST_TABLE).columns
    new_rows = new_rows.select(*table_columns)
    count = new_rows.count()
    if count:
        new_rows.write.mode("append").insertInto(CHANGE_REQUEST_TABLE)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Asset Inventory CSV into change_request.")
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--src-file-name", default=DEFAULT_SRC_FILE)
    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()
    written = load_change_requests(spark, args.csv_path, args.batch_id, args.src_file_name)
    print(f"Loaded {written} new change request(s) into {CHANGE_REQUEST_TABLE}")


if __name__ == "__main__":
    main()
