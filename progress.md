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
- **Brain:** Claude (`claude-opus-4-8`; `claude-sonnet-4-6` for live-call latency). Speech local
  (faster-whisper + Piper + VAD). A `canned` LLM mode keeps a truly-$0 offline path.
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

## In Progress
- [ ] **Phase 2 — HERO Voice Screening Agent** (next): browser softphone, STT→LLM→TTS,
  VAD barge-in, screening script, RTR capture, live dashboard, `scripts/demo_call.py`.

## Future Phases
- [ ] **Phase 3 — Recruitment non-voice:** Recruiter Assistant (Boolean + search + rank),
  Candidate Relevancy (resume↔job scoring).
- [ ] **Phase 4 — Sales + AM agents:** lead qualification + scheduling; follow-up; AM requirements,
  CSAT survey, dissatisfaction→escalation, candidate status updates.
- [ ] **Phase 5 — Channels + sync:** email/SMS/WhatsApp (mock + real stubs); Zoho↔Ceipal sync.
- [ ] **Phase 6 — Vonage real-call path (optional):** NCCO connect→websocket + ngrok, env-gated.
- [ ] **Phase 7 — Polish:** dashboard, README, recorded demo call, tests, $0 verification.

## Research
Reports in [`research/`](research/), compiled 2026-06-30. **NOTE:** `research.py` (local Ollama)
was unreliable this session — the desktop Ollama proxy on `:11434` hung the API and a dedicated
`:11435` serve was unstable — so **at the owner's direction the reports were compiled via web
search/fetch and synthesized directly, then cited**. Re-run them via `research.py` once Ollama is
fixed (the source URLs are listed in each report).
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
