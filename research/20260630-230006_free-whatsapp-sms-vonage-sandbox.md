# Research: Free WhatsApp / SMS for a developer demo (Vonage Messages Sandbox)

> Compiled 2026-06-30 via WebSearch (research.py/Ollama unavailable this session;
> re-run later per the root convention).

## Vonage Messages API Sandbox (the $0 path)
- A **free sandbox** lets you develop/test **WhatsApp, Viber, and Facebook
  Messenger** with **no plan fees and no credit card** [1][2][3].
- You **link your own WhatsApp** number and **send/receive test messages** to your
  own devices immediately — you **skip WhatsApp Business account approval** [2][4].
- The **Messages API** is one unified API across **SMS, WhatsApp, RCS, Viber, and
  Messenger** [5], so one adapter covers several channels.

## SMS note
- The sandbox focus is the social channels; **SMS** is sent via the Messages API and,
  on a trial account, is limited to **verified numbers** using trial credit [5].
  For a guaranteed-$0 demo we default SMS to the **mock**.

## Email
- Email is effectively free via **SMTP** (e.g. a Gmail App Password) and needs no
  paid API — good as the optional "real" email adapter; otherwise mock to an outbox.

## Implications for this project (Phase 5)
- `MessagingPort`: `send_sms(to, body)`, `send_whatsapp(to, body)`. **Mock** logs to
  the `Message` table + a `data/outbox/` file (always $0). The **VonageMessaging**
  adapter targets the **Messages API sandbox** for a real WhatsApp test when the
  owner links a number.
- `EmailPort`: `send_email(...)`. **Mock** writes an `.eml`-style file to the outbox;
  the **SMTP** adapter sends for real when `SMTP_*` is configured.
- This satisfies the brief's "follow-ups via phone, WhatsApp, SMS, and email" with a
  default that costs nothing and a clear real path.

## Sources
1. [Introducing the Messages API Sandbox (Vonage)](https://www.vonage.com/about-us/vonage-stories/introducing-vonage-messages-api-sandbox/)
2. [Messages API Sandbox — concepts (Vonage)](https://developer.vonage.com/en/messages/concepts/messages-api-sandbox)
3. [Introducing the Messages API Sandbox (Vonage blog)](https://developer.vonage.com/en/blog/introducing-the-messages-api-sandbox)
4. [Sandbox Quickstart: WhatsApp with Python (Vonage)](https://developer.vonage.com/en/blog/sandbox-quickstart-send-and-receive-whatsapp-messages-with-python)
5. [Vonage Messages API overview](https://www.vonage.com/communications-apis/messages/)
