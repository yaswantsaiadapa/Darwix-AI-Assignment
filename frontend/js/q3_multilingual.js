/**
 * Question 3: Native-Language Voice Bots Interactive Controller
 * Features: Market switching (PH vs ID), Scenario playback with live native TTS,
 * interactive conversation sandbox, and cultural adaptation inspector.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const btnMarketPh = document.getElementById("q3-btn-market-ph");
  const btnMarketId = document.getElementById("q3-btn-market-id");
  const botNameBadge = document.getElementById("q3-bot-name");
  const botSectorBadge = document.getElementById("q3-bot-sector");
  const botDescText = document.getElementById("q3-bot-desc");
  const glossaryTagsBox = document.getElementById("q3-glossary-tags");

  const scenarioSelect = document.getElementById("q3-scenario-select");
  const btnPlayScenario = document.getElementById("q3-btn-play-scenario");
  const btnStopScenario = document.getElementById("q3-btn-stop-scenario");
  const scenarioDescText = document.getElementById("q3-scenario-desc");

  const chatCanvas = document.getElementById("q3-chat-canvas");
  const textInput = document.getElementById("q3-text-input");
  const btnSend = document.getElementById("q3-btn-send");
  const btnMic = document.getElementById("q3-btn-mic");
  const micIcon = document.getElementById("q3-mic-icon");
  const suggestedPills = document.querySelectorAll(".q3-pill-btn");

  // State
  let currentMarket = "PH";
  let scenarios = [];
  let currentScenario = null;
  let isPlayingScenario = false;
  let scenarioTimeouts = [];
  let conversationHistory = [];
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

  // 1. Initialize Markets & Scenarios
  async function init() {
    await loadScenarios();
    switchMarket("PH");
  }

  async function loadScenarios() {
    try {
      const res = await fetch("/api/v1/q3/scenarios");
      scenarios = await res.json();
      populateScenarioDropdown();
    } catch (e) {
      console.error("[Q3 Error] Failed to load scenarios:", e);
    }
  }

  function populateScenarioDropdown() {
    if (!scenarioSelect) return;
    scenarioSelect.innerHTML = "";
    const filtered = scenarios.filter(s => s.market_code === currentMarket);

    filtered.forEach(sc => {
      const opt = document.createElement("option");
      opt.value = sc.scenario_id;
      opt.textContent = sc.title;
      scenarioSelect.appendChild(opt);
    });

    if (filtered.length > 0) {
      currentScenario = filtered[0];
      updateScenarioInfo();
    }
  }

  function updateScenarioInfo() {
    if (!currentScenario) return;
    if (scenarioDescText) {
      scenarioDescText.textContent = `${currentScenario.description} (Category: ${currentScenario.test_category})`;
    }
  }

  // 2. Switch Market (Philippines vs Indonesia)
  function switchMarket(marketCode) {
    currentMarket = marketCode;
    stopScenario();
    conversationHistory = [];

    if (btnMarketPh) btnMarketPh.classList.toggle("active", marketCode === "PH");
    if (btnMarketId) btnMarketId.classList.toggle("active", marketCode === "ID");

    if (marketCode === "PH") {
      if (botNameBadge) botNameBadge.textContent = "🇵🇭 Maria Santos";
      if (botSectorBadge) botSectorBadge.textContent = "Bancassurance & Life Insurance";
      if (botDescText) botDescText.textContent = "Natural Taglish (Tagalog-English code-switching) with respectful 'po/opo' particles, bancassurance rider endorsements, and 31-day lapse grace period rules.";
      if (glossaryTagsBox) {
        glossaryTagsBox.innerHTML = `
          <span class="glossary-tag"><code>po / opo</code> (Honorific respect)</span>
          <span class="glossary-tag"><code>premium</code> (Hulog)</span>
          <span class="glossary-tag"><code>grace period</code> (31 Days)</span>
          <span class="glossary-tag"><code>lapse</code> (Policy expiration)</span>
          <span class="glossary-tag"><code>rider</code> (Hospital / Medical add-on)</span>
          <span class="glossary-tag"><code>beneficiary</code> (Tagapagmana)</span>
        `;
      }
    } else {
      if (botNameBadge) botNameBadge.textContent = "🇮🇩 Dewi Lestari";
      if (botSectorBadge) botSectorBadge.textContent = "Multifinance & Consumer Credit";
      if (botDescText) botDescText.textContent = "Colloquial & formal Bahasa Indonesia with Javanese dialect comprehension ('Nuwun sewu', 'nggih', 'kula', 'mboten'), OJK installment grace period, and tenor restructuring.";
      if (glossaryTagsBox) {
        glossaryTagsBox.innerHTML = `
          <span class="glossary-tag"><code>cicilan / angsuran</code> (Installment)</span>
          <span class="glossary-tag"><code>tenor</code> (Loan duration)</span>
          <span class="glossary-tag"><code>denda</code> (Late fee 0.5%/day)</span>
          <span class="glossary-tag"><code>jatuh tempo</code> (Due date)</span>
          <span class="glossary-tag"><code>DP / uang muka</code> (Down payment)</span>
          <span class="glossary-tag"><code>Nuwun sewu / nggih</code> (Javanese courtesy)</span>
        `;
      }
    }

    populateScenarioDropdown();
    renderWelcomeMessage();
  }

  function renderWelcomeMessage() {
    if (!chatCanvas) return;
    chatCanvas.innerHTML = "";

    const greeting = currentMarket === "PH"
      ? "Magandang araw po! Ako po si Maria mula sa Darwix Bancassurance. May maitutulong po ba ako sa inyong life policy, premium due date, o rider coverage?"
      : "Selamat pagi/siang Bapak/Ibu, saya Dewi dari Darwix Multifinance. Ada yang bisa kami bantu terkait angsuran pembiayaan, tanggal jatuh tempo, atau perpanjangan tenor?";

    appendMessage("assistant", greeting, currentMarket === "PH" ? "Maria (Agent)" : "Dewi (Agent)");
  }

  // 3. Spoken Voice Audio (Promise-based Async TTS - Zero Cut-offs)
  function speakNativeAsync(text, speakerRole) {
    return new Promise(resolve => {
      if (!("speechSynthesis" in window) || !text) {
        const wordCount = (text || "").split(" ").length;
        const dur = Math.max(1800, wordCount * 320);
        const tId = setTimeout(resolve, dur);
        scenarioTimeouts.push(tId);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;

      if (currentMarket === "PH") {
        utterance.lang = "fil-PH";
        utterance.pitch = speakerRole === "Agent" ? 1.15 : 0.95;
      } else {
        utterance.lang = "id-ID";
        utterance.pitch = speakerRole === "Agent" ? 1.10 : 0.90;
      }

      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();

      window.speechSynthesis.speak(utterance);
    });
  }

  // 4. Sequential Scenario Playback Controller (Chronological & Complete Audio)
  async function playScenario() {
    if (!currentScenario) return;
    stopScenario();

    isPlayingScenario = true;
    if (btnPlayScenario) btnPlayScenario.classList.add("hidden");
    if (btnStopScenario) btnStopScenario.classList.remove("hidden");

    chatCanvas.innerHTML = "";
    const turns = currentScenario.timeline || [];

    // Loop through turns sequentially, awaiting full speech before starting the next turn
    for (let idx = 0; idx < turns.length; idx++) {
      if (!isPlayingScenario) break;
      const turn = turns[idx];

      // Render chat message bubble
      const roleClass = turn.role === "Agent" ? "assistant" : "user";
      appendMessage(roleClass, turn.text, turn.speaker_name, turn.cultural_markers);

      // Play full voice audio and wait for speaker to finish sentence
      await speakNativeAsync(turn.text, turn.role);

      // Natural pause between dialogue turns (700ms)
      if (isPlayingScenario && idx < turns.length - 1) {
        await new Promise(r => {
          const pId = setTimeout(r, 700);
          scenarioTimeouts.push(pId);
        });
      }
    }

    if (isPlayingScenario) {
      stopScenario();
    }
  }

  function stopScenario() {
    isPlayingScenario = false;
    scenarioTimeouts.forEach(t => clearTimeout(t));
    scenarioTimeouts = [];

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }

    if (btnPlayScenario) btnPlayScenario.classList.remove("hidden");
    if (btnStopScenario) btnStopScenario.classList.add("hidden");
  }

  // 5. Append Chat Bubbles
  function appendMessage(role, text, speakerName = "", markers = []) {
    if (!chatCanvas) return;

    const row = document.createElement("div");
    row.className = `bubble-row ${role}`;

    if (role === "assistant") {
      const avatar = document.createElement("div");
      avatar.className = "avatar-circle agent";
      avatar.textContent = currentMarket === "PH" ? "🇵🇭" : "🇮🇩";
      row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = `bubble-card ${role}`;

    const speakerTag = document.createElement("div");
    speakerTag.style.fontSize = "11px";
    speakerTag.style.fontWeight = "700";
    speakerTag.style.marginBottom = "4px";
    speakerTag.style.color = role === "assistant" ? "#93c5fd" : "#ffffff";
    speakerTag.textContent = speakerName || (role === "assistant" ? (currentMarket === "PH" ? "Maria Santos" : "Dewi Lestari") : "You");

    const textDiv = document.createElement("div");
    textDiv.className = "bubble-text-content";
    textDiv.innerHTML = formatText(text);

    bubble.appendChild(speakerTag);
    bubble.appendChild(textDiv);

    if (markers && markers.length > 0) {
      const markDiv = document.createElement("div");
      markDiv.style.marginTop = "6px";
      markers.forEach(m => {
        const span = document.createElement("span");
        span.className = "citation-chip";
        span.style.background = "rgba(255,255,255,0.15)";
        span.textContent = `🏷️ ${m}`;
        markDiv.appendChild(span);
      });
      bubble.appendChild(markDiv);
    }

    row.appendChild(bubble);

    if (role === "user") {
      const avatar = document.createElement("div");
      avatar.className = "avatar-circle user";
      avatar.textContent = "👤";
      row.appendChild(avatar);
    }

    chatCanvas.appendChild(row);
    chatCanvas.scrollTop = chatCanvas.scrollHeight;
  }

  function formatText(raw) {
    if (!raw) return "";
    let clean = raw.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    const lines = clean.split("\n");
    return lines.map(l => l.trim() ? `<p>${l.trim()}</p>` : "").join("");
  }

  // 6. Interactive User Prompt Turn
  async function sendUserMessage(msgText) {
    const text = msgText || (textInput ? textInput.value.trim() : "");
    if (!text) return;

    if (textInput) textInput.value = "";
    appendMessage("user", text, "You");
    conversationHistory.push({ role: "user", content: text });

    try {
      const res = await fetch("/api/v1/q3/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          market_code: currentMarket,
          message: text,
          conversation_history: conversationHistory,
        }),
      });

      const data = await res.json();
      const botName = data.bot_name || (currentMarket === "PH" ? "Maria (Agent)" : "Dewi (Agent)");
      appendMessage("assistant", data.reply_text, botName, data.finance_terms_identified || []);
      conversationHistory.push({ role: "assistant", content: data.reply_text });
      speakNativeAsync(data.reply_text, "Agent");
    } catch (e) {
      console.error("[Q3 Chat Error]:", e);
      appendMessage("assistant", "Paumanhin po / Mohon maaf, may technical error po. Paki-ulit na lang po.", "System");
    }
  }

  // 7. Live Microphone Audio Recording & Speech-to-Text
  async function toggleMic() {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
          const formData = new FormData();
          formData.append("file", audioBlob, "q3_mic_voice.wav");

          if (textInput) textInput.placeholder = "Transcribing your voice...";
          try {
            const transRes = await fetch(`/api/v1/q3/transcribe?market_code=${currentMarket}`, {
              method: "POST",
              body: formData,
            });
            const transData = await transRes.json();
            if (transData && transData.transcription) {
              sendUserMessage(transData.transcription);
            }
          } catch (err) {
            console.error("[Q3 Mic Error]:", err);
          } finally {
            if (textInput) {
              textInput.placeholder = "Type a message in Taglish or Bahasa Indonesia...";
            }
          }
        };

        mediaRecorder.start();
        isRecording = true;
        if (btnMic) btnMic.classList.add("recording");
        if (micIcon) micIcon.textContent = "⏹️";
        if (textInput) textInput.placeholder = "Listening... Speak in Taglish or Bahasa!";
      } catch (err) {
        console.warn("[Q3 Mic Access Denied]:", err);
        alert("Microphone access is required to speak directly. Please check your browser permissions.");
      }
    } else {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      }
      isRecording = false;
      if (btnMic) btnMic.classList.remove("recording");
      if (micIcon) micIcon.textContent = "🎙️";
    }
  }

  // Event Listeners
  if (btnMarketPh) btnMarketPh.addEventListener("click", () => switchMarket("PH"));
  if (btnMarketId) btnMarketId.addEventListener("click", () => switchMarket("ID"));

  if (scenarioSelect) {
    scenarioSelect.addEventListener("change", (e) => {
      currentScenario = scenarios.find(s => s.scenario_id === e.target.value);
      updateScenarioInfo();
      stopScenario();
    });
  }

  if (btnPlayScenario) btnPlayScenario.addEventListener("click", playScenario);
  if (btnStopScenario) btnStopScenario.addEventListener("click", stopScenario);

  if (btnSend) btnSend.addEventListener("click", () => sendUserMessage());
  if (btnMic) btnMic.addEventListener("click", toggleMic);
  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendUserMessage();
    });
  }

  suggestedPills.forEach(pill => {
    pill.addEventListener("click", () => {
      const q = pill.getAttribute("data-q");
      if (q) sendUserMessage(q);
    });
  });

  init();
});
