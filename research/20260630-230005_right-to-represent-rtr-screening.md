# Research: Right to Represent (RTR) + recruiter phone screening (for the Voice Agent)

> Compiled 2026-06-30 via WebSearch (research.py/Ollama unavailable this session;
> re-run later per the root convention).

## What an RTR is
- A **Right to Represent** is an agreement between a **candidate** and a **staffing
  agency** that **authorizes the agency to submit the candidate to a *specific*
  employer for a *specific* role** [1][2].
- It (a) establishes the agency's **claim to the placement fee** if the candidate is
  hired and (b) **protects the candidate from being submitted without their
  knowledge** [2][3].
- It is frequently **required as part of screening** before a third party can submit
  a candidate; **no RTR → the candidate can't be put forward** [3].

## What an RTR must capture
- All pertinent **job specifics**: job/req number, client/employer, role title,
  description, **pay rate**, and **location** [1].
- A candidate should **not sign two RTRs for the same role** (double-submission is
  the exact problem RTR prevents) [1].

## Screening conversation (initial phone screen)
A first screen typically confirms, before any RTR: **interest** in the role,
**availability / notice period**, **work authorization & clearance**, **location /
onsite-vs-remote** fit, **rate expectations**, and a quick confirmation of **key
skills/experience** against the requirement (domain-standard).

## Implications for this project (Phase 2 — Voice Screening Agent)
Script the agent as a state machine:
1. **Greet + verify identity** (right person, ok to talk).
2. **Describe the role** (client is often withheld until interest/RTR — configurable).
3. **Screen:** work authorization & clearance, years/skills vs the requirement,
   availability/notice, location/onsite, **rate** expectations.
4. **Gauge interest** explicitly.
5. **If interested → capture RTR**: state client, role title, pay rate, and location,
   then ask for **explicit verbal authorization** to represent them for *that*
   specific role, and record the consent.
6. **Log** a structured outcome (interested? authorized? rate? notes) + transcript.

This maps directly to the `RTR` model (`client_name`, `job_title`, `pay_rate`,
`location`, `authorized`) and the `Call.structured` outcome payload.

## Sources
1. [What Is the Right to Represent (RTR) Agreement? (OPTnation)](https://www.optnation.com/blog/right-to-represent-rtr-agreement/)
2. [What Is Right to Represent and How Does RTR Work (United OPT)](https://www.unitedopt.com/Home/blogdetail/what-is-right-to-represent-and-how-does-RTR-works)
3. [Learning More About Right to Represent Documents (Edge Services)](https://www.edgeservices.com/pages/blog/learning-more-about-right-to-represent-documentsrtr-s)
