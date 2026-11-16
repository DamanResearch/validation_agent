"""Validation agent built on Microsoft Agent Framework.

The agent runs after the change_request load. Its only tool applies pending
change requests through validation_agent.writer, so every registry write still
goes through the deterministic validation engine.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from agent_framework import Agent, tool
from agent_framework_openai import OpenAIChatCompletionClient
from pyspark.sql import SparkSession

from validation_agent.writer import apply_requests, load_requests

AGENT_NAME = "validation_agent"
DEFAULT_MODEL = "databricks-claude-haiku-5-5"

INSTRUCTIONS = """You are the validation agent for the asset registry.
When asked to process a batch, call apply_pending_change_requests exactly once.
Then reply with a short report: how many requests were applied, rejected,
or need review, and list the change_request_id of each rejected or review item.
Do not invent results. Report only what the tool returned."""

RUN_PROMPT = "Process the pending change requests for this batch and report the outcome."


def build_agent(spark: SparkSession, client: Any, outcomes: list[dict]) -> Agent:
    """Create the agent. `outcomes` collects the writer's results for the caller."""

    @tool(
        name="apply_pending_change_requests",
        description="Validate and apply all change requests not yet applied to the asset registry. "
        "Returns one JSON outcome per request with its classification and decision.",
    )
    def apply_pending_change_requests() -> str:
        requests = load_requests(spark)
        batch = apply_requests(spark, requests, applied_at=datetime.now(timezone.utc))
        results = [o.model_dump(mode="json") for o in batch]
        outcomes.extend(results)
        return json.dumps(results)

    return Agent(
        client=client,
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
        tools=[apply_pending_change_requests],
    )


def build_databricks_client(base_url: str, api_key: str, model: str = DEFAULT_MODEL) -> OpenAIChatCompletionClient:
    """Chat client for a Databricks Model Serving endpoint.

    Uses chat completions: Claude endpoints reject the Responses API.
    """
    return OpenAIChatCompletionClient(model=model, base_url=base_url, api_key=api_key)


async def run_validation_agent(spark: SparkSession, client: Any) -> dict[str, Any]:
    """Run the agent. Returns the agent's text plus the writer's outcomes and counts.

    The counts come from the writer, not the model, so they are reported even
    if the model's text is empty.
    """
    outcomes: list[dict] = []
    agent = build_agent(spark, client, outcomes)
    result = await agent.run(RUN_PROMPT)
    counts = Counter(o["decision"] for o in outcomes)
    agent_text = (result.text or "").strip() or fallback_report(dict(counts))
    return {
        "agent_text": agent_text,
        "decision_counts": dict(counts),
        "outcomes": outcomes,
    }


def fallback_report(decision_counts: dict[str, int]) -> str:
    """Deterministic summary used when the model returns no text."""
    if not decision_counts:
        return "No pending change requests were processed."
    parts = ", ".join(f"{n} {decision.lower()}" for decision, n in sorted(decision_counts.items()))
    return f"Processed pending change requests: {parts}. (Summary generated from writer outcomes.)"
