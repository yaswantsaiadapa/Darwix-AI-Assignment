/**
 * Question 2: Universal Multi-Format Knowledge Base & Dynamic Ingestion Controller
 * Includes Gemini-style slide-out benchmark drawer and compact bottom upload controls.
 */

document.addEventListener("DOMContentLoaded", () => {
  const kbSearchInput = document.getElementById("kb-search-input");
  const btnKbSearch = document.getElementById("btn-kb-search");
  const kbResultsFeed = document.getElementById("kb-search-results");
  const benchmarkContainer = document.getElementById("benchmark-report-container");

  const btnPresetHdfc = document.getElementById("btn-preset-hdfc");
  const btnPresetSbi = document.getElementById("btn-preset-sbi");
  const btnPresetDefault = document.getElementById("btn-preset-default");

  const btnCompactUpload = document.getElementById("btn-compact-upload");
  const fileUploadInput = document.getElementById("file-upload-input");
  const ingestionStatusBadge = document.getElementById("ingestion-status-badge");
  const ingestionStatusText = document.getElementById("ingestion-status-text");

  const headerStatusText = document.getElementById("header-status-text");

  // --- GEMINI-STYLE LEFT SIDEBAR DRAWER CONTROLLER ---
  const benchmarkSidebar = document.getElementById("benchmark-sidebar");
  const drawerOverlay = document.getElementById("drawer-overlay");
  const btnToggleBenchmark = document.getElementById("btn-toggle-benchmark");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");

  function openDrawer() {
    if (benchmarkSidebar) benchmarkSidebar.classList.add("open");
    if (drawerOverlay) drawerOverlay.classList.remove("hidden");
  }

  function closeDrawer() {
    if (benchmarkSidebar) benchmarkSidebar.classList.remove("open");
    if (drawerOverlay) drawerOverlay.classList.add("hidden");
  }

  if (btnToggleBenchmark) btnToggleBenchmark.addEventListener("click", openDrawer);
  if (btnCloseDrawer) btnCloseDrawer.addEventListener("click", closeDrawer);
  if (drawerOverlay) drawerOverlay.addEventListener("click", closeDrawer);

  // --- INITIAL KB STATUS CHECK ---
  async function checkInitialStatus() {
    try {
      const res = await fetch("/api/v1/kb/status");
      const data = await res.json();
      if (data.is_empty) {
        if (headerStatusText) headerStatusText.textContent = "Knowledge Base Empty";
        [btnPresetHdfc, btnPresetSbi, btnPresetDefault].forEach(b => { if (b) b.classList.remove("active"); });
      } else {
        if (headerStatusText) headerStatusText.textContent = `${data.active_records} Records Active (${data.source})`;
      }
    } catch (e) {
      console.warn("Could not check KB status:", e);
    }
  }

  // --- PRESET INGESTION ---
  async function switchPreset(presetName, targetBtn) {
    [btnPresetHdfc, btnPresetSbi, btnPresetDefault].forEach(b => { if (b) b.classList.remove("active"); });
    if (targetBtn) targetBtn.classList.add("active");

    showStatus(`Ingesting ${presetName.toUpperCase()} multi-format dataset (PDF, CSV, HTML, TXT)...`);

    try {
      const res = await fetch("/api/v1/kb/ingest-preset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset: presetName }),
      });
      const data = await res.json();
      if (data.status === "success") {
        showStatus(`✅ Successfully indexed ${data.total_records} chunks from ${data.source_dir} (${data.pii_redacted_records} PII scrubbed).`);
        if (headerStatusText) headerStatusText.textContent = `${data.total_records} Records Active (${data.source_dir})`;
        executeSearch(presetName === "sbi" ? "What is SBI SME interest rate?" : "What is the maximum loan limit for Unsecured Business Growth Loans?");
      } else {
        showStatus(`❌ Ingestion failed: ${data.message || "Unknown error"}`);
      }
    } catch (e) {
      console.error("Preset ingestion error:", e);
      showStatus("❌ Failed to contact ingestion API.");
    }
  }

  if (btnPresetHdfc) btnPresetHdfc.addEventListener("click", () => switchPreset("hdfc", btnPresetHdfc));
  if (btnPresetSbi) btnPresetSbi.addEventListener("click", () => switchPreset("sbi", btnPresetSbi));
  if (btnPresetDefault) btnPresetDefault.addEventListener("click", () => switchPreset("default", btnPresetDefault));

  // --- COMPACT FILE UPLOADER & DRAG-DROP ---
  if (fileUploadInput) {
    fileUploadInput.addEventListener("change", () => {
      if (fileUploadInput.files && fileUploadInput.files.length > 0) {
        const file = fileUploadInput.files[0];
        handleFileUpload(file);
        fileUploadInput.value = ""; // Reset input so same file can be selected again
      }
    });
  }

  const compactUploadBar = document.querySelector(".compact-upload-bar");
  if (compactUploadBar) {
    compactUploadBar.addEventListener("dragover", (e) => {
      e.preventDefault();
      compactUploadBar.style.borderColor = "#4f46e5";
      compactUploadBar.style.backgroundColor = "#eff6ff";
    });
    compactUploadBar.addEventListener("dragleave", (e) => {
      e.preventDefault();
      compactUploadBar.style.borderColor = "";
      compactUploadBar.style.backgroundColor = "";
    });
    compactUploadBar.addEventListener("drop", (e) => {
      e.preventDefault();
      compactUploadBar.style.borderColor = "";
      compactUploadBar.style.backgroundColor = "";
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });
  }

  async function handleFileUpload(file) {
    showStatus(`Uploading & parsing "${file.name}" (Extracting text, scrubbing PII, chunking)...`);
    [btnPresetHdfc, btnPresetSbi, btnPresetDefault].forEach(b => { if (b) b.classList.remove("active"); });

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/v1/kb/upload-file", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.status === "success") {
        showStatus(`✅ Ingested ONLY "${file.name}": ${data.new_chunks_added} active chunks (${data.pii_redacted_records || 0} PII scrubbed). All other bank data cleared.`);
        if (headerStatusText) headerStatusText.textContent = `${data.new_chunks_added} Records Active (${file.name})`;
        executeSearch("What is the penalty fee or eligibility?");
      } else {
        showStatus(`❌ Upload failed: ${data.message}`);
      }
    } catch (e) {
      console.error("Upload error:", e);
      showStatus("❌ File upload failed.");
    }
  }

  function showStatus(text) {
    if (ingestionStatusBadge && ingestionStatusText) {
      ingestionStatusBadge.classList.remove("hidden");
      ingestionStatusText.textContent = text;
    }
  }

  // --- EXECUTE HYBRID KB SEARCH ---
  async function executeSearch(query) {
    if (!query || !query.trim()) return;
    kbResultsFeed.innerHTML = '<p class="empty-muted">Searching hybrid vector index...</p>';

    try {
      const res = await fetch("/api/v1/kb/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, top_k: 3 }),
      });
      const data = await res.json();

      if (!data.results || data.results.length === 0) {
        kbResultsFeed.innerHTML = `
          <div class="empty-state-notice">
            <span class="empty-icon">📂</span>
            <p><strong>${data.explanation || "No knowledge chunks found."}</strong></p>
            <span>Please select a bank preset above or upload a document to index chunks.</span>
          </div>
        `;
        return;
      }

      kbResultsFeed.innerHTML = "";

      // Add Grounding Gate Status Banner
      const statusBanner = document.createElement("div");
      statusBanner.style.padding = "10px 14px";
      statusBanner.style.borderRadius = "8px";
      statusBanner.style.fontSize = "13px";
      statusBanner.style.fontWeight = "600";
      statusBanner.style.marginBottom = "14px";
      statusBanner.style.background = data.is_supported ? "#f0fdf4" : "#fef2f2";
      statusBanner.style.color = data.is_supported ? "#166534" : "#991b1b";
      statusBanner.style.border = `1px solid ${data.is_supported ? "#bbf7d0" : "#fecaca"}`;
      statusBanner.textContent = `🛡️ Grounding Gate: ${data.is_supported ? "SUPPORTED" : "UNSUPPORTED / OUT-OF-SCOPE"} (${data.explanation})`;
      kbResultsFeed.appendChild(statusBanner);

      data.results.forEach((r, idx) => {
        const card = document.createElement("div");
        card.className = "benchmark-card";
        card.style.marginBottom = "10px";

        card.innerHTML = `
          <h4>
            <span>#${idx + 1} ${r.record.title}</span>
            <span style="font-family:monospace; color:var(--primary-blue);">Score: ${Math.round(r.score * 100)}% (Dense: ${Math.round(r.dense_score * 100)}% | BM25: ${Math.round(r.sparse_score * 100)}%)</span>
          </h4>
          <p style="margin: 6px 0; font-size: 13px; color: var(--text-dark);">${r.record.content}</p>
          <div style="font-size: 11.5px; color: var(--text-muted); display: flex; gap: 12px; flex-wrap: wrap;">
            <span>ID: <code>${r.record.record_id}</code></span>
            <span>Category: <strong>${r.record.category}</strong></span>
            <span>Source: <em>${r.record.source}</em></span>
            <span>PII Scrubbed: <strong style="color:${r.record.has_pii ? '#10b981' : '#64748b'}">${r.record.has_pii ? "YES (" + r.record.pii_types_redacted.join(", ") + ")" : "NO"}</strong></span>
          </div>
        `;
        kbResultsFeed.appendChild(card);
      });
    } catch (e) {
      console.error("Search error:", e);
      kbResultsFeed.innerHTML = '<p class="empty-muted">Error querying vector index.</p>';
    }
  }

  // --- FETCH & RENDER 5-QUERY BENCHMARK REPORT (FOR DRAWER) ---
  async function loadBenchmarkReport() {
    if (!benchmarkContainer) return;
    benchmarkContainer.innerHTML = '<p class="empty-muted">Loading benchmark evaluation results...</p>';
    try {
      const res = await fetch("/api/v1/evaluations/q2");
      const report = await res.json();

      if (!report || report.length === 0) {
        benchmarkContainer.innerHTML = '<p class="empty-muted">Run pytest to generate formal evaluation report.</p>';
        return;
      }

      benchmarkContainer.innerHTML = "";
      report.forEach(item => {
        const itemElem = document.createElement("div");
        itemElem.className = "benchmark-card";

        const isCorrect = item.verdict.includes("correct") || item.verdict.includes("safely_rejected");
        const verdictColor = isCorrect ? "#166534" : "#991b1b";

        itemElem.innerHTML = `
          <h4>
            <span>Query ${item.query_id} [${item.query_type.toUpperCase()}]</span>
            <span style="color:${verdictColor}; font-weight:700;">${item.verdict.toUpperCase()} (${Math.round(item.similarity_score * 100)}%)</span>
          </h4>
          <p><strong>Q:</strong> "${item.question}"</p>
          <p class="reason">${item.relevance_explanation}</p>
        `;
        benchmarkContainer.appendChild(itemElem);
      });
    } catch (e) {
      console.error("Benchmark report error:", e);
    }
  }

  if (btnKbSearch && kbSearchInput) {
    btnKbSearch.addEventListener("click", () => executeSearch(kbSearchInput.value));
    kbSearchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") executeSearch(kbSearchInput.value);
    });
  }

  checkInitialStatus();
  loadBenchmarkReport();
});
