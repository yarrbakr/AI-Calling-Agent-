# Research: Real-time local voice pipeline — faster-whisper + Piper + VAD + barge-in

> Compiled 2026-06-30 via WebSearch (research.py/Ollama unavailable this session;
> re-run later per the root convention).

## Pipeline shape
Audio in → **VAD endpointing** → **streaming STT (faster-whisper)** on rolling
chunks → **LLM** → **streaming TTS (Piper)** emitted at sentence boundaries while
the LLM keeps generating [1][2].

## Components & numbers
- **faster-whisper** (CTranslate2 Whisper): distil models reach **RTF ≈ 0.05
  (~50× real-time)**; roughly **4× faster than vanilla Whisper** [2][3]. Wants
  **16 kHz mono PCM** — matches the telephony format.
- **Silero VAD**: probability-based, **~85–100 ms** detection latency; Python use:
  `from silero_vad import load_silero_vad` [4][2]. (`webrtcvad` is a lighter,
  prebuilt-wheel alternative for Windows.)
- **End-to-end audio→transcript ≈ 380–520 ms** combining Silero VAD + optimized
  STT [2].
- **Piper TTS**: fast **local neural** TTS used in low-latency local voice agents
  (e.g. LiveKit + Piper) [5][6].

## Barge-in / turn-taking (the hard part)
- On user interruption, three things must happen ~instantly: **echo cancellation**
  (remove the agent's own voice), **VAD detects the user**, and **immediate TTS
  cancellation**; **stop latency < 200 ms** feels natural [2].
- **Dynamic endpointing**: combine the fast VAD signal with a **semantic check** of
  the partial transcript to decide if the caller actually finished [2].
- Start TTS at **sentence boundaries** (buffer until punctuation) so the agent
  starts speaking before the LLM finishes the full reply [1].

## Implications for this project (Phase 2)
- Pipeline: 16 kHz PCM frames from `TelephonyPort` → **VAD** (start with `webrtcvad`
  for an easy Windows install; Silero optional) → **faster-whisper** (`base.en`)
  transcribe on utterance end → **Claude** (`claude-sonnet-4-6` for live latency) →
  **Piper** TTS → frames back to telephony.
- **Barge-in:** when VAD detects caller speech during agent playback, send the
  telephony **stop/`clear`** signal and cancel the current TTS task. Because the
  LocalSim adapter mirrors Vonage's 16 kHz/20 ms framing, the same loop runs in the
  browser demo and over a real Vonage call unchanged.

## Sources
1. [2025 Voice AI Guide — Real-Time Voice Agent (Part 3, DEV)](https://dev.to/programmerraja/2025-voice-ai-guide-how-to-make-your-own-real-time-voice-agent-part-3-3ocb)
2. [High-Speed Voice Recognition with WhisperX & Silero-VAD (Medium)](https://medium.com/@aidenkoh/how-to-implement-high-speed-voice-recognition-in-chatbot-systems-with-whisperx-silero-vad-cdd45ea30904)
3. [Whisper v4 / Production ASR on GPU Cloud (Spheron)](https://www.spheron.network/blog/whisper-v4-asr-gpu-cloud-production-guide/)
4. [How to Use Silero VAD: Real-Time VAD in Python (Rajat Pandit)](https://rajatpandit.com/agentic-ai/real-time-audio-vad/)
5. [LiveKit + Piper TTS: Low-Latency Local Voice Agent (Medium)](https://medium.com/@mail2chasif/livekit-piper-tts-building-a-low-latency-local-voice-agent-with-real-time-latency-tracking-92a1008416e4)
6. [Build a Local Voice Assistant: Whisper + Ollama + Piper](https://localaimaster.com/blog/local-voice-assistant-whisper-ollama-piper)
