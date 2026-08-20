/**
 * Question 1: AI Voice Assistant - HDFC Bank Lead Qualification Controller
 * Matches exact UI structure and behavior from user reference images
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- TAB SWITCHING ---
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabViews = document.querySelectorAll(".tab-view");

  navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      navTabs.forEach(t => t.classList.remove("active"));
      tabViews.forEach(v => v.classList.remove("active"));

      tab.classList.add("active");
      const targetView = document.getElementById(tab.getAttribute("data-tab"));
      if (targetView) targetView.classList.add("active");
    });
  });

  // --- STATE & DOM ELEMENTS ---
  let isCallActive = false;
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];

  const btnStartCall = document.getElementById("btn-start-call");
  const btnMicToggle = document.getElementById("btn-mic-toggle");
  const btnEndCall = document.getElementById("btn-end-call");
  const btnClearChat = document.getElementById("btn-clear-chat");
  const micText = document.getElementById("mic-text");

  const callStatusDot = document.getElementById("call-status-dot");
  const callStatusLabel = document.getElementById("call-status-label");
  const waveformBars = document.getElementById("waveform-bars");

  const chatCanvas = document.getElementById("chat-stream-canvas");
  const userTextInput = document.getElementById("user-text-input");
  const btnSendText = document.getElementById("btn-send-text");

  const crmContainer = document.getElementById("crm-lead-container");
  const crmStatusPill = document.getElementById("crm-status-pill");
  const crmLeadId = document.getElementById("crm-lead-id");
  const crmApprovedAmount = document.getElementById("crm-approved-amount");
  const crmCompanyName = document.getElementById("crm-company-name");
  const crmProgram = document.getElementById("crm-program");
  const crmRevenue = document.getElementById("crm-revenue");
  const crmMonthly = document.getElementById("crm-monthly");
  const crmFlagsBox = document.getElementById("crm-flags-box");

  // --- AUDIO SYNTHESIS & PLAYBACK ---
  function playAudio(b64Audio, fallbackText) {
    if (b64Audio && b64Audio.length > 50) {
      const audio = new Audio("data:audio/mp3;base64," + b64Audio);
      callStatusLabel.textContent = "Agent is speaking...";
      waveformBars.classList.remove("hidden");
      audio.play().catch(e => {
        console.warn("Audio play blocked, falling back to Web Speech:", e);
        fallbackSpeech(fallbackText);
      });
      audio.onended = () => {
        callStatusLabel.textContent = "Listening...";
        waveformBars.classList.add("hidden");
      };
    } else {
      fallbackSpeech(fallbackText);
    }
  }

  function fallbackSpeech(text) {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const cleanUtterance = text.replace(/\[.*?\]/g, "").replace(/📌.*/g, "");
      const utterance = new SpeechSynthesisUtterance(cleanUtterance);
      utterance.rate = 1.05;
      callStatusLabel.textContent = "Agent is speaking...";
      waveformBars.classList.remove("hidden");
      utterance.onend = () => {
        callStatusLabel.textContent = "Listening...";
        waveformBars.classList.add("hidden");
      };
      window.speechSynthesis.speak(utterance);
    }
  }

  // Clean markdown and render clean HTML for chat bubbles
  function formatMarkdownMessage(rawText) {
    if (!rawText) return "";
    
    // Clean inline bracket citations if any (e.g. 【kb_...】 or [kb_...])
    let formatted = rawText.replace(/【[^】]+】/g, "").replace(/\[kb_[^\]]+\]/g, "").trim();

    // Convert bold **text** to <strong>text</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Split lines into structured paragraphs / list items
    const lines = formatted.split("\n");
    let html = "";
    let inList = false;

    lines.forEach(line => {
      const trimmed = line.trim();
      if (!trimmed) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        return;
      }

      // Check if line starts with a bullet (*, -, •)
      if (trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
        if (!inList) {
          html += "<ul>";
          inList = true;
        }
        const itemContent = trimmed.replace(/^[\*\-•]\s*/, "").trim();
        html += `<li>${itemContent}</li>`;
      } else {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        html += `<p>${trimmed}</p>`;
      }
    });

    if (inList) {
      html += "</ul>";
    }

    return html || formatted;
  }

  // --- RENDER CHAT BUBBLES ---
  function appendMessage(role, text, citations = []) {
    const idleBox = chatCanvas.querySelector(".idle-placeholder");
    if (idleBox) idleBox.remove();

    const row = document.createElement("div");
    row.className = `bubble-row ${role}`;

    // Agent Avatar on left (Lightning badge)
    if (role === "assistant") {
      const avatar = document.createElement("div");
      avatar.className = "avatar-circle agent";
      avatar.textContent = "⚡";
      row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = `bubble-card ${role}`;

    const textDiv = document.createElement("div");
    textDiv.className = "bubble-text-content";
    textDiv.innerHTML = formatMarkdownMessage(text);
    bubble.appendChild(textDiv);

    // Citations chip
    if (citations && citations.length > 0) {
      const citContainer = document.createElement("div");
      citations.forEach(c => {
        const chip = document.createElement("span");
        chip.className = "citation-chip";
        chip.textContent = `📌 ${c.record_id} (${Math.round(c.confidence_score * 100)}% match)`;
        citContainer.appendChild(chip);
      });
      bubble.appendChild(citContainer);
    }

    row.appendChild(bubble);

    // User Avatar on right
    if (role === "user") {
      const avatar = document.createElement("div");
      avatar.className = "avatar-circle user";
      avatar.textContent = "👤";
      row.appendChild(avatar);
    }

    chatCanvas.appendChild(row);
    chatCanvas.scrollTop = chatCanvas.scrollHeight;
  }

  // --- CRM LEAD CARD UPDATE (IN INR ₹) ---
  function renderCRMLead(lead) {
    if (!lead) return;
    crmContainer.classList.remove("hidden");
    crmLeadId.textContent = lead.lead_id;
    crmStatusPill.textContent = lead.status;
    crmStatusPill.style.background = lead.status === "QUALIFIED" ? "#10b981" : "#f59e0b";

    const approvedAmt = lead.underwriting_assessment.preliminary_max_approved || 0;
    crmApprovedAmount.textContent = `₹${approvedAmt.toLocaleString("en-IN")}`;

    crmCompanyName.textContent = lead.business_profile.business_name || "Applicant Enterprise";
    crmProgram.textContent = lead.underwriting_assessment.recommended_program || "Commercial Business Loan";
    crmRevenue.textContent = `₹${(lead.business_profile.annual_revenue || 0).toLocaleString("en-IN")}`;
    crmMonthly.textContent = `₹${Math.round(lead.underwriting_assessment.monthly_payment_estimate || 0).toLocaleString("en-IN")}/mo`;

    crmFlagsBox.innerHTML = "";
    if (lead.underwriting_assessment.underwriting_flags && lead.underwriting_assessment.underwriting_flags.length > 0) {
      lead.underwriting_assessment.underwriting_flags.forEach(flag => {
        const fDiv = document.createElement("div");
        fDiv.style.fontSize = "12px";
        fDiv.style.color = "#d97706";
        fDiv.style.marginTop = "4px";
        fDiv.textContent = `⚠️ ${flag}`;
        crmFlagsBox.appendChild(fDiv);
      });
    }
  }

  // --- START / END CALL ---
  async function startCall() {
    isCallActive = true;
    btnStartCall.classList.add("hidden");
    btnMicToggle.classList.remove("hidden");
    btnEndCall.classList.remove("hidden");

    userTextInput.disabled = false;
    btnSendText.disabled = false;

    callStatusDot.className = "status-dot active";
    callStatusLabel.textContent = "In call (Connecting...)";

    try {
      const res = await fetch("/api/v1/voice/greet", { method: "POST" });
      const data = await res.json();
      appendMessage("assistant", data.agent_response);
      playAudio(data.audio_base64, data.agent_response);
    } catch (e) {
      console.error("Greet error:", e);
      appendMessage("assistant", "Hello! Thank you for calling Darwix AI commercial lending. May I know the legal name of your business?");
    }
  }

  function endCall() {
    isCallActive = false;
    btnStartCall.classList.remove("hidden");
    btnMicToggle.classList.add("hidden");
    btnEndCall.classList.add("hidden");

    userTextInput.disabled = true;
    btnSendText.disabled = true;

    callStatusDot.className = "status-dot ready";
    callStatusLabel.textContent = "Ready";
    waveformBars.classList.add("hidden");
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  }

  async function sendMessage(text) {
    if (!text.trim()) return;
    if (!isCallActive) await startCall();

    appendMessage("user", text);
    userTextInput.value = "";
    callStatusLabel.textContent = "Analyzing knowledge base guidelines...";

    try {
      const res = await fetch("/api/v1/voice/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      appendMessage("assistant", data.agent_response, data.citations);
      playAudio(data.audio_base64, data.agent_response);

      if (data.crm_lead) {
        renderCRMLead(data.crm_lead);
      }
    } catch (e) {
      console.error("Chat turn error:", e);
      appendMessage("assistant", "I am having trouble accessing underwriting records. Connecting you with a senior loan specialist.");
    }
  }

  // --- EVENT LISTENERS ---
  btnStartCall.addEventListener("click", startCall);
  btnEndCall.addEventListener("click", endCall);

  btnSendText.addEventListener("click", () => sendMessage(userTextInput.value));
  userTextInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage(userTextInput.value);
  });

  btnClearChat.addEventListener("click", () => {
    chatCanvas.innerHTML = '<div class="idle-placeholder"><p>Start a call to see the AI qualify a lead in real time.</p></div>';
    crmContainer.classList.add("hidden");
  });

  // FAQ PILLS
  document.querySelectorAll(".faq-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const q = btn.getAttribute("data-q");
      if (q) sendMessage(q);
    });
  });

  // --- MICROPHONE CAPTURE VIA GROQ WHISPER ---
  btnMicToggle.addEventListener("click", async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
          const formData = new FormData();
          formData.append("file", audioBlob, "mic_voice.wav");

          callStatusLabel.textContent = "Transcribing with Groq Whisper...";
          try {
            const transRes = await fetch("/api/v1/voice/transcribe", {
              method: "POST",
              body: formData,
            });
            const transData = await transRes.json();
            if (transData.transcription && transData.transcription.trim().length > 1 && !transData.transcription.toLowerCase().includes("error")) {
              sendMessage(transData.transcription.trim());
            } else {
              callStatusLabel.textContent = "Could not capture clear speech. Please hold the mic button while speaking or type below.";
            }
          } catch (err) {
            console.error("Transcription failed:", err);
            callStatusLabel.textContent = "Voice input error. Please type your message below.";
          }
        };

        mediaRecorder.start();
        isRecording = true;
        btnMicToggle.classList.add("recording");
        micText.textContent = "Recording... (Click to Send)";
        waveformBars.classList.remove("hidden");
      } catch (err) {
        alert("Microphone permission denied. You can type in the text box below!");
      }
    } else {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
      isRecording = false;
      btnMicToggle.classList.remove("recording");
      micText.textContent = "Hold to Speak";
      waveformBars.classList.add("hidden");
    }
  });
});
