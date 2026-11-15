# Databricks notebook source
import sys

sys.path.append("../src")

from validation_agent.loader import DEFAULT_BATCH_ID, DEFAULT_SRC_FILE, load_change_requests

dbutils.widgets.text("csv_path", "/Workspace/Users/srivalli.tata@secure.damaninc.com/validation_agent/data/asset_inventory_rows.csv")
dbutils.widgets.text("batch_id", DEFAULT_BATCH_ID)
dbutils.widgets.text("src_file_name", DEFAULT_SRC_FILE)

written = load_change_requests(
    spark,
    csv_path=dbutils.widgets.get("csv_path"),
    batch_id=dbutils.widgets.get("batch_id"),
    src_file_name=dbutils.widgets.get("src_file_name"),
)
print(f"Loaded {written} new change request(s)")
