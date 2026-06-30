# Research: Zoho CRM REST API (v2/v8) — Self Client OAuth + records

> Compiled 2026-06-30 via WebSearch + WebFetch (research.py/Ollama unavailable this
> session; re-run later per the root convention).

## Authentication (server-to-server)
- Zoho CRM uses **OAuth 2.0 (authorization-code grant)** [1].
- For a backend service with no UI, use a **Self Client**: in the Zoho API Console
  pick "Self Client", set Client Name / Homepage / Redirect URI. You get **one
  client-id/secret** per self client [2][5].
- Flow: generate a **grant token** (short-lived code, scoped) in the console →
  exchange it at the **token endpoint** for an **access token + refresh token** →
  thereafter **refresh** the access token with `grant_type=refresh_token` [1][3].
  - Token endpoint (US DC): `https://accounts.zoho.com/oauth/v2/token`
    (`.eu`, `.in`, `.com.au` for other data centers).
  - Access token ≈ 1 hour; refresh token is long-lived.
- **Scopes** limit access, e.g. `ZohoCRM.modules.ALL` or granular
  `ZohoCRM.modules.leads.{READ,CREATE}`, `...contacts.*`, `...calls.*`,
  `...events.*` (events = meetings) [4].

## Working with records
- REST, JSON, standard verbs. API domain (US): `https://www.zohoapis.com` [1].
- Create a lead: `POST /crm/v2/Leads` with `{"data":[{"Company":"…","Last_Name":"…"}]}`;
  success returns **HTTP 201** plus the new record **id** [1].
- Relevant modules for this project: **Leads, Contacts, Accounts, Deals, Calls
  (call logging), Events (meetings), Tasks** [1][4].
- Free edition exposes the REST API; per-day API **credit limits** scale with edition.

## Implications for this project
- `CrmPort` (Zoho) methods: `create_lead`, `update_lead`, `create_contact`,
  `log_call`, `schedule_event`, `create_task`. **MockZoho** persists to SQLite; the
  real **ZohoAdapter** maps the same calls onto `/crm/v2/*` with an auto-refreshing
  access token (store `ZOHO_REFRESH_TOKEN` in `.env`).
- Maps cleanly to our domain: Calls module ↔ `Call`, Events ↔ `Meeting`, Leads ↔
  `Lead`, Contacts ↔ `Contact`, Accounts ↔ `Client`.

## Sources
1. [OAuth 2.0 Authentication — Zoho CRM API](https://www.zoho.com/crm/developer/docs/api/v8/oauth-overview.html)
2. [Zoho CRM API Integration Guide: OAuth 2.0 (Knit)](https://www.getknit.dev/blog/zoho-crm-api-integration-guide-oauth-2-0-use-cases-step-by-step-tutorial)
3. [How to Find and Use Your Zoho API Token (LeadCRM)](https://www.leadcrm.io/blog/zoho-api-key/)
4. [Scopes — Zoho CRM API](https://www.zoho.com/crm/developer/docs/api/v8/scopes.html)
5. [Kaizen #2 — OAuth2.0 and Self Client (Zoho)](https://help.zoho.com/portal/en/community/topic/kaizen-2-oauth2-0-and-self-client-api)
