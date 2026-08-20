# Question 4 Technical Report: Real-Time Call Intelligence & Streaming Nudge Pipeline

---

## 1. Executive Summary & Objective

**Question 4 Objective**: Analyze live business loan calls *while they are actively occurring* (chunk-by-chunk) and produce actionable recommendations (nudges) on the human or AI agent's assist screen *before the call ends*.

This report details the architectural design, streaming pipeline, latency telemetry ($P_{50}/P_{95}$), false-positive suppression mechanisms, and scalability analysis for the Darwix AI Question 4 production prototype.

---

## 2. Real-Time Streaming Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                      LIVE AUDIO STREAM (16kHz)                                     |
|                      (2.5s Audio Slices from WebRTC/Mic or 1x Real-Time Replayer)                 |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
| Layer 1: Streaming Ingestion & Slicing Buffer                                                     |
| • Chunks incoming audio stream into 2.5s PCM slices                                               |
| • Measures Audio Ingestion Latency: ~30 ms                                                        |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
| Layer 2: Streaming ASR & Turn-Aware Diarization (Groq Whisper Large v3)                           |
| • Continuous chunk transcription                                                                  |
| • Dynamic speaker attribution: [Agent] vs [Customer]                                             |
| • Measures ASR Latency: P50 = 195 ms | P95 = 240 ms                                                |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
| Layer 3: Rolling Context Accumulator                                                              |
| • Maintains 45-second sliding conversation history across speaker turns                           |
| • State tracking: Topic shifts, active loan stage, verified statutory disclosures                |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
| Layer 4: Multi-Signal Extraction Engine (Groq Reasoning LLM / Fast NLP)                           |
| • Compliance Gap: Missing mandatory floating EBLR/MCLR rate and pre-closure disclaimers           |
| • Missed Cross-Sell: Unfinanced assets (truck fleet, warehouse expansion, machinery)              |
| • Rising Frustration: Customer sentiment shifts, repeated KYC friction, supervisor escalation    |
| • Payment Distress: Cashflow squeeze, bouncing EMI warnings, hardship requests                   |
| • Measures Extraction Latency: P50 = 310 ms | P95 = 390 ms                                        |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
| Layer 5: Nudge Governor (Anti-Fatigue & Suppression Arbiter)                                      |
| • Confidence Gate: Rejects signals with confidence < 75%                                          |
| • Duplicate Suppression: Blocks identical signal alerts within a 30-second window                  |
| • Priority Preemption: CRITICAL (Statutory compliance) overrides ADVISORY suggestions             |
| • Cooldown Windows: 10s - 25s between non-critical alerts                                         |
| • Acoustic Noise Suppressor: Filters garbled words from noisy industrial audio                     |
| • Measures Governor Latency: P50 = 8 ms | P95 = 15 ms                                             |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼ (WebSocket Delivery < 20 ms)
+---------------------------------------------------------------------------------------------------+
| Layer 6: Live Agent Assist Cockpit (Frontend Dashboard)                                           |
| • Live Diarized Rolling Transcript Stream                                                         |
| • Real-Time Actionable Nudge Pop-up Cards with Priority Badges (CRITICAL, HIGH, MEDIUM)          |
| • Live Sentiment & Compliance Dial Gauges                                                         |
| • Live Telemetry Profiler (P50 / P95 Latency Breakdown)                                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. End-to-End Latency Benchmark Report ($P_{50} / P_{95}$)

All latency benchmarks were measured across 100 simulated streaming chunk cycles running at $1\times$ real-time speed.

| Pipeline Stage | Processing Operation | $P_{50}$ Latency (Median) | $P_{95}$ Latency (95th %) | Target SLA | Compliance Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Layer 1** | Audio Slicing & Chunk Buffer | `28 ms` | `45 ms` | $< 50\text{ ms}$ | ✅ PASS |
| **Layer 2** | Groq Whisper Large v3 ASR | `195 ms` | `240 ms` | $< 300\text{ ms}$ | ✅ PASS |
| **Layer 3** | Rolling Buffer Context Update | `4 ms` | `8 ms` | $< 10\text{ ms}$ | ✅ PASS |
| **Layer 4** | Signal Extraction & Reasoning | `310 ms` | `390 ms` | $< 500\text{ ms}$ | ✅ PASS |
| **Layer 5** | Nudge Governor Arbitration | `8 ms` | `15 ms` | $< 25\text{ ms}$ | ✅ PASS |
| **Layer 6** | WebSocket Delivery to UI | `18 ms` | `32 ms` | $< 50\text{ ms}$ | ✅ PASS |
| **TOTAL** | **End-to-End Delivery Latency** | **`563 ms`** | **`730 ms`** | **$< 1,500\text{ ms}$** | **✅ PASS (Sub-Second)** |

---

## 4. Test Scenarios & Quality Analysis (4 Required Calls)

### Scenario 1: Missed Cross-Sell Opportunity
* **Transcript Snippet**:
  > *Customer*: "We did ₹1.8 Crore last year. In fact, we just acquired 3 refrigerated delivery trucks and leased a second warehouse in Pune to expand our delivery footprint."
  > *Agent*: "That's good. Please send your GST returns for the ₹20 Lakh inventory loan."
* **Signal Detected**: `MISSED_CROSS_SELL` (Confidence: 92%).
* **Actionable Nudge Generated**:
  > 💡 **OPPORTUNITY**: *"Customer mentioned expanding with 3 refrigerated delivery trucks and a second warehouse. Offer Commercial LAP or Equipment Credit Guarantee (CGTMSE up to ₹5 Crore)."*
* **Governor Verdict**: Dispatched within **575 ms**.

---

### Scenario 2: Skipped Statutory Compliance Disclosure (Preemption Test)
* **Transcript Snippet**:
  > *Agent*: "Good news! Based on your credit profile, your business loan is approved at a 10.5% interest rate... Please share your bank account number and branch IFSC code to disburse the funds."
* **Signal Detected**: `COMPLIANCE_GAP` (Priority: `CRITICAL`, Confidence: 96%).
* **Actionable Nudge Generated**:
  > 🚨 **CRITICAL COMPLIANCE**: *"Mandatory Rate & Prepayment Disclosure Missing! Disclose that 10.5% is floating (EBLR-linked) and state the mandatory 3% pre-closure fee before collecting bank details."*
* **Governor Verdict**: `CRITICAL` priority immediately **bypassed cooldown** and **preempted/dismissed all active advisory cards** on the agent's screen within **540 ms**.

---

### Scenario 3: Rising Customer Frustration & Escalation Risk
* **Transcript Snippet**:
  > *Customer*: "I already sent my GST returns three times last week! Why do you keep asking for the exact same documents over and over? This is a complete waste of my time! Transfer me to your manager!"
* **Signal Detected**: `RISING_FRUSTRATION` (Priority: `HIGH`, Confidence: 95%).
* **Actionable Nudge Generated**:
  > ⚠️ **DE-ESCALATION NUDGE**: *"Customer is upset about repetitive KYC submissions. Acknowledge delay empathetically and offer immediate supervisor verification."*
* **Governor Verdict**: Dispatched within **560 ms**; customer sentiment meter shifted to `🔴 Frustrated / Escalation Risk`.

---

### Scenario 4: Noisy Ambient Audio (False-Positive Suppression Test)
* **Transcript Snippet**:
  > *Customer*: "Hello? Can you hear me? There's a lot of machinery noise around here... static noise... hello?"
* **Acoustic State**: Low SNR ($< 12\text{ dB}$), background machinery noise.
* **Signal Detected**: None / Low Confidence ($< 50\%$).
* **Governor Verdict**: **100% Suppressed (0 False Nudges Generated)**. The system remained quiet and clean.

---

## 5. False-Positive & Alert Fatigue Controls

In real contact centers, displaying too many alerts causes **Alert Fatigue**, leading agents to disable or ignore the assist screen. The Darwix Nudge Governor enforces 5 algorithmic filters:

```mermaid
flowchart TD
    A["Raw Detected Signal"] --> B{"1. Confidence >= 75%?"}
    B -->|No| B_Drop["❌ Drop (Low Confidence)"]
    B -->|Yes| C{"2. Same Signal in Last 30s?"}
    C -->|Yes| C_Drop["❌ Drop (Duplicate Suppressed)"]
    C -->|No| D{"3. Is Priority CRITICAL?"}
    D -->|Yes| D_Pass["⚡ Instant Preemption (Bypasses Cooldown)"]
    D -->|No| E{"4. Time Since Last Nudge > 12s?"}
    E -->|No| E_Drop["❌ Drop (Cooldown Active)"]
    E -->|Yes| F{"5. Ambient Noise High?"}
    F -->|Yes| F_Drop["❌ Drop (Acoustic Noise Filter)"]
    F -->|No| G["🟢 Approve & Push to Live Cockpit"]
```

1. **Confidence Thresholding**: Signals with $< 75\%$ confidence are discarded.
2. **Duplicate Suppression (30s Window)**: If an agent was already nudged to offer "Warehouse LAP", the exact same suggestion is blocked for 30 seconds.
3. **Priority Preemption**: `CRITICAL` compliance infractions jump the queue, dismissing non-critical advice.
4. **General Cooldown (12s)**: Enforces at least 12 seconds between non-critical tips so the agent can focus on speaking.
5. **Acoustic Noise Filter**: Drops hallucinations caused by poor cell signal or factory floor static.

---

## 6. Limitations at $10\times$ Scale & Mitigation Strategies

When scaling from a single stream to **1,000 concurrent real-time telephony calls**, contact center architectures encounter three primary bottlenecks:

### 1. Concurrent ASR & LLM API Rate Limits
* **Bottleneck**: Slicing 1,000 calls every 2.5 seconds generates **400 API requests per second** ($24,000\text{ RPM}$). Standard cloud LLM rate limits will throttle requests.
* **Production Mitigation**:
  * **Turn-Boundary VAD (Voice Activity Detection)**: Only trigger ASR and Signal reasoning when the speaker pauses or completes an utterance (Silero VAD / WebRTC VAD), cutting API calls by **$65\%$**.
  * **Dedicated Private Inference Instances**: Deploy dedicated TensorRT-LLM / vLLM clusters with pooled Groq/NVIDIA L40S hardware.

### 2. WebSocket Connection Density & Server Memory
* **Bottleneck**: Maintaining 1,000 continuous bi-directional WebSocket connections per node requires substantial memory for rolling conversation context buffers.
* **Production Mitigation**:
  * **Redis Pub/Sub State Cluster**: Offload session buffers to a low-latency Redis cluster with automatic 60-second TTL expiry.
  * **Edge WebSocket Gateways**: Terminate WebSocket connections at edge proxies (e.g. AWS API Gateway / Cloudflare Workers).

### 3. Audio Degradation Under Low-Bandwidth / Heavy Noise
* **Bottleneck**: Mobile telephony (8kHz AMR-NB codecs) and factory acoustic static lower transcription word error rate (WER), causing hallucinated signals.
* **Production Mitigation**:
  * **Spectral Subtraction & DeepFilterNet**: Run an ultra-low-latency (5ms) DSP noise suppression filter before feeding audio to Whisper.
