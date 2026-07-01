"""Central configuration + the mock-vs-real adapter switches.

Single source of truth for which implementation each port uses. The rule is
simple and safe-by-default:

* ``use_mocks=True`` (the default) -> every port uses its Mock adapter, so the
  whole system runs offline at $0 with no third-party accounts.
* Set ``use_mocks=False`` AND provide a service's credentials -> that one port
  switches to its real adapter. Missing creds always fall back to mock.

Values come from the project-level ``.env`` (gitignored). See ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve important paths relative to this file so the app is CWD-independent.
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../P1-AI-Calling-Agent
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
DB_PATH = DATA_DIR / "app.db"
OUTBOX_DIR = DATA_DIR / "outbox"  # where the mock email/SMS "sends" land


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Master switches ------------------------------------------------------
    use_mocks: bool = True            # True => all ports use Mock adapters
    # auto => prefer free Mistral -> Claude -> offline canned (see active_llm_backend):
    llm_backend: str = "auto"         # auto | mistral | claude | ollama | canned

    # --- LLM brain ------------------------------------------------------------
    # Mistral (free "Experiment" tier supports tool-use) — preferred real brain at $0:
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"
    mistral_model_realtime: str = "mistral-small-latest"   # lower latency for live calls
    # Claude — premium swap (small per-call cost):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    anthropic_model_realtime: str = "claude-sonnet-4-6"
    # Local Ollama — truly $0/offline once it's stable on this machine:
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:14b"

    # --- Speech (hero voice agent) -------------------------------------------
    # Mirrors the mock-vs-real pattern: `browser` = zero-install Web Speech API in
    # the client (default, $0, always works for the demo); `local` = server-side
    # faster-whisper + Piper + webrtcvad over the 16 kHz PCM telephony contract
    # (offline, env-gated; needs the voice deps installed).
    speech_mode: str = "browser"            # browser | local
    whisper_model: str = "base.en"          # faster-whisper size (local mode)
    piper_voice: str = "en_US-amy-medium"   # piper voice name (local mode)

    # --- Optional real CRM (Zoho) --------------------------------------------
    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_api_domain: str = "https://www.zohoapis.com"

    # --- Optional real ATS (Ceipal) ------------------------------------------
    ceipal_email: str = ""
    ceipal_password: str = ""
    ceipal_api_key: str = ""

    # --- Optional real telephony (Vonage) ------------------------------------
    vonage_application_id: str = ""
    vonage_private_key_path: str = ""
    vonage_number: str = ""
    public_base_url: str = ""               # e.g. an ngrok https URL for webhooks

    # --- Optional real email (SMTP) ------------------------------------------
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "ai-agent@example.com"

    # --- App ------------------------------------------------------------------
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    # --- Derived helpers ------------------------------------------------------
    @property
    def db_url(self) -> str:
        return f"sqlite:///{DB_PATH}"

    def active_llm_backend(self) -> str:
        """Resolve the concrete backend, honoring `auto` and falling back to
        `canned` when a chosen provider has no key."""
        b = (self.llm_backend or "auto").lower()
        if b == "auto":
            if self.mistral_api_key:
                return "mistral"
            if self.anthropic_api_key:
                return "claude"
            return "canned"
        if b == "mistral" and not self.mistral_api_key:
            return "canned"
        if b == "claude" and not self.anthropic_api_key:
            return "canned"
        return b

    def crm_is_real(self) -> bool:
        return not self.use_mocks and bool(self.zoho_client_id and self.zoho_refresh_token)

    def ats_is_real(self) -> bool:
        return not self.use_mocks and bool(self.ceipal_email and self.ceipal_password)

    def telephony_is_real(self) -> bool:
        return not self.use_mocks and bool(self.vonage_application_id and self.public_base_url)

    def email_is_real(self) -> bool:
        return not self.use_mocks and bool(self.smtp_host and self.smtp_user)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
