# P1 — AI Calling Agent — Progress

> Bible of this project. Reflects current reality. Linked from this project's
> [CLAUDE.md](CLAUDE.md). Keep entries dated and current as work moves planned → done.
> A ticked `- [x]` item = merged to `main` and pushed to GitHub (`origin`:
> [yarrbakr/AI-Calling-Agent-](https://github.com/yarrbakr/AI-Calling-Agent-)).

## Overview
AI calling agent for a **federal staffing firm** (the Upwork brief) that integrates **Zoho CRM**,
**Ceipal ATS**, and **Vonage** to automate **Sales**, **Account Management**, and **Recruitment**.
**Mock-first & ~$0**: every external system sits behind a port with a Mock adapter by default; the
brain is **Claude**; speech is **local**. The **hero** feature is the **Recruitment Voice Agent**
(call → screen → interest → **RTR**); all other agents are scaffolded with working logic.

## Decisions locked (2026-06-30 — kickoff Q&A + approved plan)
- **Integrations:** mock-first, swappable (Mock default; real adapter is env-gated).
- **Scope:** hero Voice Screening Agent end-to-end + scaffold all other agents.
- **Call demo:** local simulation (browser softphone); Vonage adapter built but optional.
- **Brain:** Claude (`claude-opus-4-8`; `claude-sonnet-4-6` for live-call latency). A `canned` LLM
  mode keeps a truly-$0 offline path.
- **Speech (2026-07-01):** speech is a **swappable port** like every integration — default
  `browser` (Web Speech API: STT/TTS in the client, zero install, $0, the reliable demo path);
  `local` = server-side faster-whisper + Piper over the 16 kHz PCM contract (env-gated, offline).
- **Architecture:** ports & adapters (hexagonal); SQLite = the mock CRM/ATS store; FastAPI app.

## Implemented (on `main`)
- [x] [2026-06-30] Project scaffolding: `CLAUDE.md` + this `progress.md`; git init + `.gitignore`.
- [x] [2026-06-30] **Phase 0 — research & foundations** (branch `feat/phase0-foundations`):
  - 6 cited research reports in `research/` (see Research section).
  - App skeleton: `app/config.py` (mock switches), domain models + SQLite `db`, seed loader +
    data (3 clients, 4 jobs, 6 candidates, 4 leads, 3 contacts), FastAPI app (`/health`,
    `/api/stats`, `/`). Verified: DB seeds and the app boots green via TestClient.
  - Core deps appended to root `requirements.txt` and installed in the shared `.venv`.
- [x] [2026-06-30] **Phase 1 — Foundations** (branch `feat/phase1-foundations`):
  - Swappable **LLM brain** behind one port — `mistral` (free, default), `claude`,
    `ollama`, `canned` (offline $0) — with a tool-use loop and `auto` backend selection.
  - All **integration ports + Mock adapters**: CRM (Zoho-shaped), ATS (Ceipal-shaped, incl.
    candidate match scoring + RTR), messaging (SMS/WhatsApp), email, and the telephony audio
    contract. `integrations/factory.py` picks mock-by-default.
  - Verified end-to-end: candidate search ranked the cleared Java candidate #1, RTR captured,
    multi-channel sends hit `data/outbox/`; `/health` reports brain + adapters.

- [x] [2026-07-01] **Phase 2 — HERO Voice Screening Agent** (branch `feat/phase2-voice-agent`):
  - **Swappable speech port** (`app/speech/`): `browser` (Web Speech API, default, $0, no install)
    + `local` (faster-whisper + Piper over the PCM contract, env-gated, lazy imports). Factory
    picks browser-by-default; `SPEECH_MODE` switches it. Mirrors the CRM/ATS mock-vs-real pattern.
  - **Screening brain** (`app/agents/voice_screening.py`): transport-agnostic `ScreeningSession`
    (text in → text + structured events out) — runs a real phone screen (identity → pitch →
    interest/availability/rate/work-auth/clearance fit → **RTR**), uses the LLM tool-loop with
    `capture_rtr` + `end_call` tools, logs every `TranscriptTurn`, writes outcome back to `Call`.
  - **Live dashboard + call websocket** (`app/web/`): softphone UI (candidate/job picker, mic,
    live transcript, outcome/RTR panel, recent calls), browser STT/TTS + client-side barge-in,
    text-input fallback when no mic STT. `/ws/call` runs the brain in a threadpool; `/api/calls`.
  - **`scripts/demo_call.py`**: headless, deterministic, $0 (canned LLM) — screens Priya Sharma
    for the Senior Java Developer role end-to-end, capturing an authorized RTR. Verified PASS
    (RTR row saved, outcome `rtr_collected`, 13 transcript turns). App boot + routes + websocket
    verified via FastAPI TestClient.

- [x] [2026-07-01] **Phase 2 fix** (branch `fix/mistral-2x-llm-fallback`): Mistral adapter now
  supports both SDK layouts (`mistralai.Mistral` 1.x / `mistralai.client.Mistral` 2.x — the
  installed 2.5.0 moved the client under `.client`); LLM factory **degrades to canned** if a
  provider dep is broken instead of crashing the call; websocket `start` guarded. Verified the
  live Mistral brain + tool-use (RTR capture) end-to-end.

## In Progress
- [ ] (nothing active — Phase 3 is next)

## Future Phases
- [ ] **Phase 3 — Recruitment non-voice:** Recruiter Assistant (Boolean + search + rank),
  Candidate Relevancy (resume↔job scoring).
- [ ] **Phase 4 — Sales + AM agents:** lead qualification + scheduling; follow-up; AM requirements,
  CSAT survey, dissatisfaction→escalation, candidate status updates.
- [ ] **Phase 5 — Channels + sync:** email/SMS/WhatsApp (mock + real stubs); Zoho↔Ceipal sync.
- [ ] **Phase 6 — Vonage real-call path (optional):** NCCO connect→websocket + ngrok, env-gated.
- [ ] **Phase 7 — Polish:** dashboard, README, recorded demo call, tests, $0 verification.

## Research
Reports in [`research/`](research/), compiled 2026-06-30. **DECISION (2026-07-01):** local Ollama
is down and **dropped for this project** — all web research is now done directly (search/fetch →
synthesize → cite), not via `research.py`. The existing reports stand; new research follows the
direct method and still lands cited `.md` files in `research/`.
- Vonage voice (websocket media) — `research/20260630-230001_vonage-voice-api-realtime-websocket.md`
- Zoho CRM API (self-client OAuth) — `research/20260630-230002_zoho-crm-api-v2-self-client-oauth.md`
- Ceipal ATS v1 API — `research/20260630-230003_ceipal-ats-v1-api.md`
- Real-time voice pipeline — `research/20260630-230004_realtime-voice-pipeline-whisper-piper-vad.md`
- Right to Represent + screening — `research/20260630-230005_right-to-represent-rtr-screening.md`
- Free WhatsApp/SMS (Vonage sandbox) — `research/20260630-230006_free-whatsapp-sms-vonage-sandbox.md`

## Open items
- [x] [2026-06-30] GitHub remote connected (`origin` → github.com/yarrbakr/AI-Calling-Agent-)
  and `main` pushed.
- Ceipal stays mock (no free tier). LLM brain is swappable; default prefers free Mistral →
  Claude → `canned` (offline $0), so a real AI brain can run at $0.

## Workflow reminder
- Every feature: **new branch → work → merge to `main` → (push when remote set)**, then tick here.
