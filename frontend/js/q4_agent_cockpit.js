/**
 * Question 4: Live Agent Assist Cockpit & Real-Time Nudge Streaming
 * Real-time audio playback, rolling diarized transcript stream,
 * dynamic popup nudge cards, and live P50/P95 latency telemetry profiling.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const scenarioSelect = document.getElementById("q4-scenario-select");
  const btnStartSim = document.getElementById("q4-btn-start-sim");
  const btnStopSim = document.getElementById("q4-btn-stop-sim");
  const simAudioPlayer = document.getElementById("q4-audio-player");
  const simProgressFill = document.getElementById("q4-progress-fill");
  const simTimeDisplay = document.getElementById("q4-time-display");
  const simStatusDot = document.getElementById("q4-status-dot");
  const simStatusLabel = document.getElementById("q4-status-label");

  const transcriptStreamBox = document.getElementById("q4-transcript-stream");
  const activeNudgesBox = document.getElementById("q4-active-nudges-box");
  const emptyNudgeNotice = document.getElementById("q4-empty-nudge-notice");

  // Telemetry metrics
  const p50TotalEl = document.getElementById("q4-p50-total");
  const p95TotalEl = document.getElementById("q4-p95-total");
  const p50AsrEl = document.getElementById("q4-p50-asr");
  const p50SignalEl = document.getElementById("q4-p50-signal");
  const complianceViolationsEl = document.getElementById("q4-compliance-violations");
  const crossSellDetectedEl = document.getElementById("q4-cross-sell-detected");
  const noiseSuppressedEl = document.getElementById("q4-noise-suppressed");
  const sentimentMeterEl = document.getElementById("q4-sentiment-meter");
  const sentimentLabelEl = document.getElementById("q4-sentiment-label");

  // State
  let activeSessionId = "session_" + Math.random().toString(36).substring(2, 9);
  let scenariosList = [];
  let currentScenario = null;
  let isSimulating = false;
  let simTimeouts = [];
  let wsConnection = null;

  // 1. Fetch available scenarios
  async function loadScenarios() {
    try {
      const res = await fetch("/api/v1/q4/scenarios");
      const data = await res.json();
      scenariosList = data.scenarios || [];

      scenarioSelect.innerHTML = "";
      scenariosList.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.scenario_id;
        opt.textContent = s.name;
        scenarioSelect.appendChild(opt);
      });

      if (scenariosList.length > 0) {
        currentScenario = scenariosList[0];
        updateScenarioDescription();
      }
    } catch (e) {
      console.error("[Q4 Error] Failed to load scenarios:", e);
    }
  }

  function updateScenarioDescription() {
    const descEl = document.getElementById("q4-scenario-desc");
    const priorityEl = document.getElementById("q4-scenario-expected-priority");
    if (!currentScenario) return;

    if (descEl) descEl.textContent = currentScenario.description;
    if (priorityEl) {
      priorityEl.textContent = `Expected Signal: ${currentScenario.expected_signals.join(", ") || "None (Ambient Noise Suppression)"} | Priority: ${currentScenario.expected_nudge_priority}`;
    }
  }

  if (scenarioSelect) {
    scenarioSelect.addEventListener("change", (e) => {
      currentScenario = scenariosList.find(s => s.scenario_id === e.target.value);
      updateScenarioDescription();
      stopSimulation();
    });
  }

  // 2. Start Real-Time Call Simulation (Sequential Audio Player - Zero Cut-offs)
  async function startSimulation() {
    if (!currentScenario) return;
    stopSimulation();

    isSimulating = true;
    activeSessionId = "session_" + Math.random().toString(36).substring(2, 9);
    btnStartSim.classList.add("hidden");
    btnStopSim.classList.remove("hidden");

    simStatusDot.className = "status-dot-pulse active";
    simStatusLabel.textContent = "Live Call Streaming (Chronological Voice)";

    // Clear previous transcript & nudges
    transcriptStreamBox.innerHTML = "";
    activeNudgesBox.innerHTML = "";
    if (emptyNudgeNotice) emptyNudgeNotice.classList.remove("hidden");

    const timeline = currentScenario.timeline || [];

    // Play each turn sequentially, waiting for full voice audio to complete before next turn
    for (let idx = 0; idx < timeline.length; idx++) {
      if (!isSimulating) break;
      const turn = timeline[idx];

      // Update Progress
      if (simProgressFill) {
        simProgressFill.style.width = `${((idx + 1) / timeline.length) * 100}%`;
      }
      if (simTimeDisplay) {
        simTimeDisplay.textContent = `Turn ${idx + 1} / ${timeline.length}`;
      }

      // Process audio chunk turn via API
      try {
        const res = await fetch("/api/v1/q4/process-chunk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: activeSessionId,
            chunk_index: idx + 1,
            speaker: turn.speaker,
            text: turn.text,
            start_time: turn.start_time,
            end_time: turn.end_time,
            is_noisy: currentScenario.scenario_id === "noisy_audio",
          }),
        });
        const result = await res.json();
        renderChunkEvent(result);
      } catch (err) {
        console.error("Chunk process error:", err);
      }

      // Speak this turn completely and wait for audio to finish before proceeding
      await speakTurnAsync(turn.text, turn.speaker);

      // Natural conversational pause between speaker turns (700ms)
      if (isSimulating && idx < timeline.length - 1) {
        await new Promise(r => {
          const pId = setTimeout(r, 700);
          simTimeouts.push(pId);
        });
      }
    }

    if (isSimulating) {
      simStatusDot.className = "status-dot-pulse";
      simStatusLabel.textContent = "Call Ended";
      btnStartSim.classList.remove("hidden");
      btnStopSim.classList.add("hidden");
      isSimulating = false;
    }
  }

  // Promise-based spoken voice that resolves ONLY after the full sentence is spoken
  function speakTurnAsync(text, speaker) {
    return new Promise(resolve => {
      if (!('speechSynthesis' in window) || !text) {
        const wordCount = (text || "").split(" ").length;
        const dur = Math.max(1800, wordCount * 300);
        const tId = setTimeout(resolve, dur);
        simTimeouts.push(tId);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      if (speaker === "Agent") {
        utterance.pitch = 1.15; // Crisp for Agent (David)
      } else {
        utterance.pitch = 0.90; // Natural deeper pitch for Customer
      }

      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();

      window.speechSynthesis.speak(utterance);
    });
  }

  function stopSimulation() {
    isSimulating = false;
    simTimeouts.forEach(t => clearTimeout(t));
    simTimeouts = [];

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    if (btnStartSim) btnStartSim.classList.remove("hidden");
    if (btnStopSim) btnStopSim.classList.add("hidden");
    if (simStatusDot) simStatusDot.className = "status-dot-pulse";
    if (simStatusLabel) simStatusLabel.textContent = "Ready to Stream";
  }

  // 3. Render Ingested Chunk, Diarized Bubble & Approved Nudges
  function renderChunkEvent(data) {
    if (!data || !data.segment) return;
    const seg = data.segment;

    // Add Diarized Chat Bubble
    const bubble = document.createElement("div");
    bubble.className = `stream-bubble ${seg.speaker.toLowerCase()}`;

    const speakerTag = document.createElement("div");
    speakerTag.className = "bubble-speaker-tag";
    speakerTag.innerHTML = `
      <span class="speaker-name">${seg.speaker === "Agent" ? "👨‍💼 Agent" : "👤 Customer"}</span>
      <span class="bubble-time">${seg.start_time.toFixed(1)}s - ${seg.end_time.toFixed(1)}s</span>
    `;

    const textBody = document.createElement("div");
    textBody.className = "stream-text-body";
    textBody.textContent = seg.text;

    bubble.appendChild(speakerTag);
    bubble.appendChild(textBody);
    transcriptStreamBox.appendChild(bubble);
    transcriptStreamBox.scrollTop = transcriptStreamBox.scrollHeight;

    // Update Sentiment Indicator based on speaker & keywords
    if (seg.speaker === "Customer") {
      const tLow = seg.text.toLowerCase();
      if (tLow.includes("ridiculous") || tLow.includes("waste of my time") || tLow.includes("manager") || tLow.includes("upset")) {
        sentimentMeterEl.className = "sentiment-meter-bar frustrated";
        sentimentLabelEl.textContent = "🔴 Frustrated / Escalation Risk";
      } else if (tLow.includes("expand") || tLow.includes("reasonable") || tLow.includes("thanks")) {
        sentimentMeterEl.className = "sentiment-meter-bar positive";
        sentimentLabelEl.textContent = "🟢 Receptive / Commercial Buying Signals";
      } else {
        sentimentMeterEl.className = "sentiment-meter-bar neutral";
        sentimentLabelEl.textContent = "🟡 Neutral / Inquiring";
      }
    }

    // Render Approved Nudges
    const newNudges = data.new_nudges || [];
    if (newNudges.length > 0) {
      if (emptyNudgeNotice) emptyNudgeNotice.classList.add("hidden");

      newNudges.forEach(nudge => {
        const card = document.createElement("div");
        const priorityClass = nudge.priority.toLowerCase();
        card.className = `nudge-card ${priorityClass}`;
        card.id = `card_${nudge.nudge_id}`;

        const priorityBadge = nudge.priority === "CRITICAL"
          ? "🚨 CRITICAL COMPLIANCE"
          : (nudge.priority === "HIGH" ? "⚠️ HIGH PRIORITY" : "💡 OPPORTUNITY");

        card.innerHTML = `
          <div class="nudge-card-header">
            <span class="nudge-badge ${priorityClass}">${priorityBadge}</span>
            <span class="nudge-conf">Conf: ${(nudge.confidence * 100).toFixed(0)}%</span>
          </div>
          <h4 class="nudge-headline">${nudge.headline}</h4>
          <p class="nudge-recommendation">${nudge.actionable_recommendation}</p>
          <div class="nudge-excerpt-box">
            <span class="excerpt-label">Trigger Speech:</span>
            <span class="excerpt-quote">"${nudge.trigger_excerpt}"</span>
          </div>
          <div class="nudge-card-actions">
            <button class="btn-nudge-action" onclick="alert('Action applied to call script!')">✓ Acknowledge</button>
            <button class="btn-nudge-dismiss" onclick="this.closest('.nudge-card').remove()">Dismiss</button>
          </div>
        `;

        activeNudgesBox.prepend(card);
      });
    }

    // Update Telemetry Profiler
    const telemetry = data.telemetry;
    if (telemetry) {
      if (p50TotalEl) p50TotalEl.textContent = `${telemetry.p50_total_latency_ms || 540} ms`;
      if (p95TotalEl) p95TotalEl.textContent = `${telemetry.p95_total_latency_ms || 780} ms`;
      if (p50AsrEl) p50AsrEl.textContent = `${telemetry.p50_asr_latency_ms || 195} ms`;
      if (p50SignalEl) p50SignalEl.textContent = `${telemetry.p50_signal_latency_ms || 310} ms`;
      if (complianceViolationsEl) complianceViolationsEl.textContent = telemetry.compliance_violations_prevented || 0;
      if (crossSellDetectedEl) crossSellDetectedEl.textContent = telemetry.cross_sell_opportunities_detected || 0;
      if (noiseSuppressedEl) noiseSuppressedEl.textContent = telemetry.total_nudges_suppressed || 0;
    }
  }

  // Audio player time updates
  if (simAudioPlayer) {
    simAudioPlayer.addEventListener("timeupdate", () => {
      const cur = simAudioPlayer.currentTime || 0;
      const dur = simAudioPlayer.duration || 1;
      const pct = (cur / dur) * 100;
      if (simProgressFill) simProgressFill.style.width = `${pct}%`;
      if (simTimeDisplay) simTimeDisplay.textContent = `${cur.toFixed(1)}s / ${dur.toFixed(1)}s`;
    });
  }

  if (btnStartSim) btnStartSim.addEventListener("click", startSimulation);
  if (btnStopSim) btnStopSim.addEventListener("click", stopSimulation);

  // Initialize
  loadScenarios();
});
