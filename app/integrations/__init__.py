"""Integrations: ports (interfaces) + adapters for the external systems.

Each subpackage has a `base.py` (the port), a `mock_*.py` (default, $0, over SQLite),
and a real adapter stub selected only when `USE_MOCKS=false` and creds are present.
`factory.py` resolves which to use.
"""
