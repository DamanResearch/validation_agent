# Databricks notebook source
# MAGIC %pip install --no-deps agent-framework-core==1.24.0 agent-framework-openai==1.17.0
# MAGIC %pip install msgspec regex python-dotenv opentelemetry-api openai

# COMMAND ----------

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.append("../src")

from databricks.sdk import WorkspaceClient

from validation_agent.agent import DEFAULT_MODEL, build_databricks_client, run_validation_agent

dbutils.widgets.text("model", DEFAULT_MODEL)

w = WorkspaceClient()
token = w.config.authenticate()["Authorization"].removeprefix("Bearer ")
client = build_databricks_client(
    base_url=f"{w.config.host}/serving-endpoints",
    api_key=token,
    model=dbutils.widgets.get("model"),
)

# Databricks notebooks already run an event loop, so run the agent in a worker thread.
with ThreadPoolExecutor(max_workers=1) as pool:
    summary = pool.submit(asyncio.run, run_validation_agent(spark, client)).result()

print(json.dumps(summary, indent=2))
dbutils.notebook.exit(json.dumps({"decision_counts": summary["decision_counts"], "agent_text": summary["agent_text"]}))
