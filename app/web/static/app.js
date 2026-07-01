/* Voice screening dashboard — browser speech mode.
   The browser owns mic capture, STT (SpeechRecognition), TTS (speechSynthesis)
   and barge-in; the server runs the screening brain over text on the websocket. */
(() => {
  "use strict";

  const boot = JSON.parse(document.getElementById("bootstrap").textContent);
  const $ = (id) => document.getElementById(id);

  // --- elements ---
  const candSel = $("candidate-select");
  const jobSel = $("job-select");
  const matchHint = $("match-hint");
  const callBtn = $("call-btn");
  const hangupBtn = $("hangup-btn");
  const softphone = $("softphone");
  const micBtn = $("mic-btn");
  const micState = $("mic-state");
  const autoListen = $("auto-listen");
  const textForm = $("text-fallback");
  const textInput = $("text-input");
  const transcript = $("transcript");
  const connBadge = $("conn-badge");

  // --- state ---
  let ws = null;
  let inCall = false;
  let agentSpeaking = false;
  let listening = false;

  // ---------- speech synthesis (TTS) ----------
  let voice = null;
  function pickVoice() {
    const voices = speechSynthesis.getVoices();
    voice =
      voices.find((v) => /en-US/i.test(v.lang) && /female|Samantha|Zira|Aria|Jenny/i.test(v.name)) ||
      voices.find((v) => /en/i.test(v.lang)) ||
      voices[0] ||
      null;
  }
  if ("speechSynthesis" in window) {
    pickVoice();
    speechSynthesis.onvoiceschanged = pickVoice;
  }
  function speak(text, onDone) {
    if (!("speechSynthesis" in window) || !text) return onDone && onDone();
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    if (voice) u.voice = voice;
    u.rate = 1.03;
    u.pitch = 1.0;
    agentSpeaking = true;
    setMic("agent speaking…");
    u.onend = () => {
      agentSpeaking = false;
      onDone && onDone();
    };
    u.onerror = () => {
      agentSpeaking = false;
      onDone && onDone();
    };
    speechSynthesis.speak(u);
  }

  // ---------- speech recognition (STT) ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recog = null;
  let finalText = "";
  if (SR) {
    recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = true;
    recog.continuous = false;
    recog.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript;
        else interim += r[0].transcript;
      }
      showInterim(finalText + interim);
    };
    recog.onend = () => {
      listening = false;
      micBtn.classList.remove("live");
      clearInterim();
      const said = finalText.trim();
      finalText = "";
      if (said) {
        addBubble("human", said);
        sendUser(said);
      } else if (inCall) {
        setMic("idle — click 🎙️ to talk");
      }
    };
    recog.onerror = () => {
      listening = false;
      micBtn.classList.remove("live");
    };
  }

  function startListening() {
    if (!recog || listening || !inCall) return;
    if (agentSpeaking) speechSynthesis.cancel(); // barge-in
    try {
      finalText = "";
      recog.start();
      listening = true;
      micBtn.classList.add("live");
      setMic("listening…");
    } catch (_) {
      /* start() throws if already started; ignore */
    }
  }
  function stopListening() {
    if (recog && listening) recog.stop();
  }

  // ---------- transcript rendering ----------
  function clearEmpty() {
    const e = $("transcript-empty");
    if (e) e.remove();
  }
  function addBubble(role, text) {
    clearEmpty();
    const el = document.createElement("div");
    el.className = "bubble " + (role === "human" ? "human" : "agent");
    el.innerHTML = `<span class="who">${role === "human" ? "Candidate" : "Agent · Alex"}</span>`;
    el.appendChild(document.createTextNode(text));
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
  }
  let interimEl = null;
  function showInterim(text) {
    clearEmpty();
    if (!interimEl) {
      interimEl = document.createElement("div");
      interimEl.className = "bubble human interim";
      transcript.appendChild(interimEl);
    }
    interimEl.textContent = text;
    transcript.scrollTop = transcript.scrollHeight;
  }
  function clearInterim() {
    if (interimEl) {
      interimEl.remove();
      interimEl = null;
    }
  }
  function sysLine(text) {
    clearEmpty();
    const el = document.createElement("div");
    el.className = "sys-line";
    el.textContent = text;
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
  }

  function setMic(s) {
    micState.textContent = s;
  }

  // ---------- websocket ----------
  function sendUser(text) {
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "user", text }));
  }
  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/call`);
    ws.onopen = () => {
      connBadge.textContent = "connected";
      connBadge.classList.add("on");
      ws.send(
        JSON.stringify({
          type: "start",
          candidate_id: Number(candSel.value),
          job_id: Number(jobSel.value),
        })
      );
    };
    ws.onclose = () => {
      connBadge.textContent = "offline";
      connBadge.classList.remove("on");
    };
    ws.onmessage = (ev) => handleServer(JSON.parse(ev.data));
  }

  function handleServer(msg) {
    switch (msg.type) {
      case "ready":
        $("o-status").textContent = "in progress";
        break;
      case "agent":
        addBubble("agent", msg.text);
        speak(msg.text, () => {
          if (inCall && autoListen.checked) startListening();
          else setMic("idle — click 🎙️ to talk");
        });
        break;
      case "event":
        if (msg.event === "rtr_captured") {
          const chip = $("o-rtr");
          chip.textContent = msg.authorized ? "AUTHORIZED ✓" : "declined";
          chip.className = "chip " + (msg.authorized ? "good" : "bad");
          sysLine(msg.authorized ? "— Right to Represent captured —" : "— RTR declined —");
        }
        break;
      case "end":
        endCallUI(msg);
        break;
      case "error":
        sysLine("error: " + msg.error);
        break;
    }
  }

  // ---------- outcome panel ----------
  function endCallUI(msg) {
    inCall = false;
    stopListening();
    setMic("call ended");
    $("o-status").textContent = "completed";
    const oc = $("o-outcome");
    oc.textContent = msg.outcome || "—";
    oc.className = "chip " + outcomeClass(msg.outcome);
    const st = msg.structured || {};
    if ("interested" in st) $("o-interested").textContent = st.interested ? "yes" : "no";
    if (st.availability) $("o-availability").textContent = st.availability;
    if (st.pay_rate) $("o-rate").textContent = st.pay_rate;
    if (msg.summary) $("o-summary").textContent = msg.summary;
    callBtn.hidden = false;
    callBtn.disabled = false;
    hangupBtn.hidden = true;
    softphone.hidden = true;
    loadRecent();
    if (ws && ws.readyState === 1) ws.close();
  }
  function outcomeClass(o) {
    if (o === "rtr_collected" || o === "interested") return "good";
    if (o === "not_interested" || o === "not_a_fit") return "bad";
    return "warn";
  }

  // ---------- controls ----------
  function startCall() {
    resetOutcome();
    inCall = true;
    callBtn.hidden = true;
    hangupBtn.hidden = false;
    softphone.hidden = false;
    setMic(SR ? "starting…" : "no mic STT — type replies below");
    if (!SR) textInput.focus();
    connect();
  }
  function hangup() {
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "hangup" }));
    speechSynthesis.cancel();
    stopListening();
    inCall = false;
  }
  function resetOutcome() {
    transcript.innerHTML = "";
    ["o-interested", "o-availability", "o-rate"].forEach((id) => ($(id).textContent = "—"));
    $("o-summary").textContent = "—";
    $("o-status").textContent = "dialing…";
    const oc = $("o-outcome"); oc.textContent = "—"; oc.className = "chip";
    const rc = $("o-rtr"); rc.textContent = "—"; rc.className = "chip";
  }

  micBtn.addEventListener("click", () => {
    if (!inCall) return;
    if (listening) stopListening();
    else startListening(); // also cancels agent TTS => barge-in
  });
  callBtn.addEventListener("click", startCall);
  hangupBtn.addEventListener("click", hangup);
  textForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const t = textInput.value.trim();
    if (!t || !inCall) return;
    speechSynthesis.cancel();
    addBubble("human", t);
    sendUser(t);
    textInput.value = "";
  });

  // ---------- setup: dropdowns, match hint, recent ----------
  function fillSelects() {
    boot.candidates.forEach((c) => {
      const o = document.createElement("option");
      o.value = c.id;
      o.textContent = `${c.name} — ${c.current_title} (${c.clearance})`;
      candSel.appendChild(o);
    });
    boot.jobs.forEach((j) => {
      const o = document.createElement("option");
      o.value = j.id;
      o.textContent = `${j.title} — ${j.client_name} (${j.clearance})`;
      jobSel.appendChild(o);
    });
    updateHint();
  }
  const RANK = { none: 0, "public trust": 1, secret: 2, "top secret": 3, "ts/sci": 4 };
  function updateHint() {
    const c = boot.candidates.find((x) => x.id == candSel.value);
    const j = boot.jobs.find((x) => x.id == jobSel.value);
    if (!c || !j) { matchHint.textContent = ""; return; }
    const have = new Set((c.skills || []).map((s) => s.toLowerCase()));
    const need = (j.skills || []).map((s) => s.toLowerCase());
    const hits = need.filter((s) => have.has(s));
    const clrOk = (RANK[(c.clearance || "none").toLowerCase()] ?? 0) >= (RANK[(j.clearance || "none").toLowerCase()] ?? 0);
    matchHint.innerHTML =
      `skills <b>${hits.length}/${need.length}</b> · ` +
      `clearance <span class="${clrOk ? "ok" : "gap"}">${clrOk ? "meets " + j.clearance : c.clearance + " < " + j.clearance}</span>`;
  }
  candSel.addEventListener("change", updateHint);
  jobSel.addEventListener("change", updateHint);

  async function loadRecent() {
    try {
      const res = await fetch("/api/calls?limit=8");
      const calls = await res.json();
      const ul = $("recent");
      ul.innerHTML = "";
      calls.forEach((c) => {
        const li = document.createElement("li");
        li.innerHTML =
          `<div class="r-top"><b>${c.party_name || "—"}</b><span class="chip ${outcomeClass(c.outcome)}">${c.outcome || c.status}</span></div>` +
          `<div class="r-sub">${c.job_title || ""}</div>`;
        ul.appendChild(li);
      });
    } catch (_) {}
  }

  fillSelects();
  loadRecent();
})();
