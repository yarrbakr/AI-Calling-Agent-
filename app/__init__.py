"""P1 AI Calling Agent — application package.

A mock-first, swappable AI calling agent for a federal staffing firm that
integrates (conceptually) Zoho CRM, Ceipal ATS, and Vonage. Everything runs at
~$0: external systems sit behind ports with Mock adapters by default; the LLM
brain is Claude (with a zero-cost ``canned`` fallback); speech is local.
"""

__version__ = "0.1.0"
