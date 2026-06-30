# P1 — AI Calling Agent

> Inherits workflow conventions from [../CLAUDE.md](../CLAUDE.md). **Read it first.**
> Running record of work lives in [progress.md](progress.md) — keep it current.

This project rebuilds an **in-demand Upwork project**: an **AI voice calling agent** that can
place and/or receive phone calls, hold a natural spoken conversation with a human, and act on a
defined goal (e.g. appointment booking, lead qualification, reminders, support triage).

---

## Non-negotiable rules (carried forward from the root guide — do not violate)

- **Web search/research → use the shared `research.py`.** For ANY web search or research,
  Claude must run the root `research.py` script (see the root guide's "Research workflow").
  Do not use other web-search tools/connectors for research unless the owner explicitly asks.
- **Python → use the shared venv.** All Python in this project runs through the shared venv at
  the repo root (`.venv`). Do not create a per-project venv or install packages globally. Add
  new dependencies to the root `requirements.txt` and install them into the shared venv.

Run helpers via the shared interpreter:

```bash
# research (writes the .md report into this project folder when run from here)
../.venv/Scripts/python.exe ../research.py "your topic" --out .

# any project python
../.venv/Scripts/python.exe <script.py>
```

---

## Git & GitHub (this project is its own repo)

This folder is an **independent GitHub repository** (the parent folder is not a repo). See the
root guide's "Git & GitHub workflow" for the full rules. In short:

- **Remote:** `origin` → _TODO: paste this project's GitHub repo URL._ Until set, work stays
  local.
- **Per-feature flow — new branch → work → merge to `main` → push:**
  1. `git checkout -b feat/<short-name>` (branch off `main`).
  2. Do the work, committing as you go.
  3. `git checkout main && git merge feat/<short-name>`.
  4. `git push origin main`.
- **A feature is only ticked `- [x]` in [progress.md](progress.md) once it is merged to `main`
  and pushed.** Ticking the box and pushing happen together; note the branch next to the entry.

---

## Project goal

A working AI calling agent that:
1. Connects to the telephone network (place/receive calls).
2. Streams the caller's speech to **speech-to-text** in real time.
3. Generates the agent's responses with an **LLM** (default to the latest, most capable Claude
   model — `claude-opus-4-8`).
4. Speaks responses back via **text-to-speech** with low latency.
5. Pursues a configurable conversation goal and logs the outcome.

## Stack

Not yet decided. Research each component (telephony, STT, LLM, TTS) via `research.py` and
record the choice and rationale in [progress.md](progress.md) before building on it.

## Originating Upwork demand (context)

Clients on Upwork are paying for AI phone agents that handle outbound/inbound calls
(appointment setting, lead qualification, reminders, first-line support) so staff don't have to.
This project is the portfolio / proof-of-work rebuild of that demand.

> TODO: paste the specific Upwork job text/link the owner is targeting so scope can be tightened.

---

## Where things live

- [CLAUDE.md](CLAUDE.md) — this file (project conventions + context).
- [progress.md](progress.md) — **the bible**: Implemented / In progress / Future phases.
- Research reports — saved into this folder and referenced from `progress.md`.
