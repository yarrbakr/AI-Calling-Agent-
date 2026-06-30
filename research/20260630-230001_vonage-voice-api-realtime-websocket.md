# Research: Vonage Voice API — real-time audio over WebSocket (for an AI voice agent)

> Compiled 2026-06-30 via WebSearch + WebFetch. NOTE: the shared `research.py`
> (local Ollama) was unavailable this session, so this was synthesized directly
> from the same web sources and cited below. Re-run via `research.py` once Ollama
> is fixed, per the root convention.

## How call control works
- Vonage Voice API controls calls with an **NCCO** (Nexmo Call Control Object): a
  JSON array of "actions" (`talk`, `stream`, `input`, `connect`, …) returned from
  your answer webhook [1][2].
- To get the live audio into your own server you use the **`connect`** action with
  an **`endpoint` of type `websocket`**. This "forks" the call's audio over a
  secure WebSocket to your URI [2][3].

```json
{ "action": "connect",
  "endpoint": [{ "type": "websocket",
                 "uri": "wss://your-server.example.com/socket",
                 "content-type": "audio/l16;rate=16000" }] }
```

## Audio format (what flows on the socket)
- **16-bit signed little-endian PCM**, mono. Sample rate set via `content-type`:
  `audio/l16;rate=16000` (also `8000` or `24000`). **16 kHz is recommended for
  speech recognition** [3].
- Audio arrives as **binary WebSocket frames of ~20 ms each**. At 16 kHz that is
  **320 samples × 2 bytes = 640 bytes per frame** [3][1].
- On open, Vonage first sends a **JSON text** message:
  `{"event":"websocket:connected","content-type":"audio/l16;rate=16000"}` [3].

## Sending audio back (the agent speaking)
- Write **raw binary PCM** frames (same rate/format) back over the socket. Vonage
  **buffers and plays them in order**, with a buffer of ~**3072 packets (~60 s)** [3].
- **Barge-in / interruption:** send `{"action":"clear"}` to **immediately stop**
  buffered playback; Vonage replies `{"event":"websocket:cleared"}` [3]. This is the
  hook we use to cut the agent off when the caller starts talking.

## Ecosystem / latency
- Vonage ships an **Audio Connector Python Server SDK** and a **Pipecat serializer**,
  plus reference bridges to ElevenLabs, Deepgram, and AWS Nova Sonic, targeting
  **sub-second** conversational latency [1][4][5].

## Implications for this project
- Our `TelephonyPort` standardizes on **16 kHz, 16-bit signed LE mono PCM, 20 ms
  frames over a binary WebSocket** — exactly Vonage's contract. The **LocalSim**
  (browser) adapter emits/consumes the same framing, so the **VonageAdapter** is a
  drop-in (Phase 6) with no agent changes.
- The `{"action":"clear"}` semantics map directly to our **barge-in "stop TTS"**
  signal. 16 kHz PCM is also exactly what **faster-whisper** wants — no resampling.

## Sources
1. [Vonage Voice API Media Streaming for AI Voice in 2026 (CallSphere)](https://callsphere.ai/blog/vw4d-vonage-voice-api-media-streaming-ai-2026)
2. [Vonage NCCO – API Reference](https://developer.vonage.com/en/voice/voice-api/ncco-reference)
3. [WebSocket Voice Chat — Vonage Voice API concepts](https://developer.vonage.com/en/voice/voice-api/concepts/websockets)
4. [Introducing Audio Connector SDK & Pipecat Serializer (Vonage)](https://developer.vonage.com/en/blog/introducing-audio-connector-sdk-and-pipecat-serializer-for-ai-audio-apps)
5. [Connect Vonage to ElevenLabs Conversational AI](https://elevenlabs.io/agents/integrations/vonage)
