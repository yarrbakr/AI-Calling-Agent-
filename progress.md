# P1 — AI Calling Agent — Progress

> Bible of this project. Reflects current reality. Linked from this project's
> [CLAUDE.md](CLAUDE.md). Keep entries dated and current as work moves planned → done.
> A ticked `- [x]` item = merged to `main` and pushed to GitHub (see CLAUDE.md → Git & GitHub).

## Overview
An AI voice calling agent that places/receives phone calls, holds a natural spoken conversation
via STT → LLM (Claude) → TTS, and pursues a configurable goal (booking, lead qualification,
reminders, support triage). Rebuild of an in-demand Upwork project as proof-of-work.

## Implemented (on `main`, pushed)
- [x] [2026-06-30] Project scaffolding: `CLAUDE.md` (references root guide, carries the
  non-negotiable rules) and this `progress.md`. (branch: initial commit on `main`)
- [x] [2026-06-30] Git repo initialized with a project `.gitignore` and initial commit.
  (branch: `main`)

## In Progress
- [ ] [2026-06-30] Connect the GitHub remote — awaiting the repo URL from the owner, then
  `git remote add origin <url>` + `git push -u origin main`.
- [ ] [2026-06-30] Defining scope and locking the stack (telephony, STT, TTS). Pending the
  specific Upwork job text from the owner to tighten requirements.

## Future Phases
- [ ] Telephony integration: place/receive a call and establish a real-time media stream.
- [ ] Streaming STT: transcribe caller speech in real time with low latency.
- [ ] LLM dialog: Claude (`claude-opus-4-8`) driving the conversation toward a configurable
  goal, with system prompt + tool use for actions (e.g. booking).
- [ ] Streaming TTS: speak responses back with low end-to-end latency; barge-in handling.
- [ ] Orchestration: turn-taking, interruption, silence/timeouts, call-end conditions.
- [ ] Outcome logging + transcript storage; basic metrics (duration, goal success).
- [ ] Configurable scenarios (outbound vs inbound; per-goal prompts).
- [ ] Demo: a recorded sample call for the portfolio.

## Workflow reminder
- Every feature: **new branch → work → merge to `main` → push**, then tick its box here.
- Use `research.py` (shared venv) for each stack decision; save the report into this folder
  and reference it from this file before building on it.

## Decisions / Notes
- [2026-06-30] Stack not yet decided — no research run yet. Use `research.py` for each
  component (telephony, STT, LLM, TTS) and record choices + rationale here before building.
