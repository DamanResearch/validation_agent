# Databricks notebook source
import sys
from datetime import datetime, timezone

sys.path.append("../src")

from validation_agent.writer import apply_requests, load_requests

requests = load_requests(spark)
outcomes = apply_requests(spark, requests, applied_at=datetime.now(timezone.utc))

for outcome in outcomes:
    print(outcome)
