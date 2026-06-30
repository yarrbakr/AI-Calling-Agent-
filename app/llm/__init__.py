"""LLM layer: a provider-neutral brain behind one interface.

Agents depend only on the `LLM` port (`base.py`) and never import a vendor SDK.
Adapters: `canned` (offline, $0), `mistral` (free tier), `claude` (premium),
`ollama` (local). `factory.get_llm()` picks one via config / available keys.
"""
