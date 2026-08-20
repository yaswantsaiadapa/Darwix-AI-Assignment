import sys
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import httpx
import json

def run_tests():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Test scenarios listing
    res = httpx.get(f"{base_url}/api/v1/q4/scenarios", timeout=20.0)
    scenarios = res.json().get("scenarios", [])
    print(f"✅ Available Q4 Scenarios: {len(scenarios)}")
    for s in scenarios:
        print(f" - [{s['scenario_id']}] {s['name']} ({s['turns_count']} turns, {s['duration_seconds']}s)")

    # 2. Test Scenario 1: Missed Cross-Sell
    print("\n--- 🧪 TEST 1: SCENARIO 1 (MISSED CROSS-SELL) ---")
    session_id = "test_q4_s1"
    s1 = next(s for s in scenarios if s["scenario_id"] == "missed_cross_sell")
    nudges_s1 = []
    for turn in s1["timeline"]:
        res = httpx.post(f"{base_url}/api/v1/q4/process-chunk", json={
            "session_id": session_id,
            "chunk_index": turn["turn_index"] + 1,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "start_time": turn["start_time"],
            "end_time": turn["end_time"],
            "is_noisy": False
        })
        data = res.json()
        for n in data.get("new_nudges", []):
            nudges_s1.append(n)
            print(f"  ⚡ [NUDGE TRIGGERED at {turn['start_time']}s] Priority: {n['priority']} | {n['headline']}")
            print(f"     💡 Guidance: {n['actionable_recommendation']}")

    telemetry_s1 = httpx.get(f"{base_url}/api/v1/q4/telemetry/{session_id}").json()
    print(f"  📊 Telemetry: P50 Latency={telemetry_s1['p50_total_latency_ms']}ms, Cross-Sells Detected={telemetry_s1['cross_sell_opportunities_detected']}")
    assert len(nudges_s1) > 0, "Scenario 1 should have produced at least 1 cross-sell nudge"

    # 3. Test Scenario 2: Skipped Compliance Disclosure
    print("\n--- 🧪 TEST 2: SCENARIO 2 (SKIPPED COMPLIANCE DISCLOSURE) ---")
    session_id = "test_q4_s2"
    s2 = next(s for s in scenarios if s["scenario_id"] == "compliance_gap")
    nudges_s2 = []
    for turn in s2["timeline"]:
        res = httpx.post(f"{base_url}/api/v1/q4/process-chunk", json={
            "session_id": session_id,
            "chunk_index": turn["turn_index"] + 1,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "start_time": turn["start_time"],
            "end_time": turn["end_time"],
            "is_noisy": False
        })
        data = res.json()
        for n in data.get("new_nudges", []):
            nudges_s2.append(n)
            print(f"  🚨 [CRITICAL ALERT at {turn['start_time']}s] Priority: {n['priority']} | {n['headline']}")
            print(f"     ⚠️ Compliance Action: {n['actionable_recommendation']}")

    telemetry_s2 = httpx.get(f"{base_url}/api/v1/q4/telemetry/{session_id}").json()
    print(f"  📊 Telemetry: P50 Latency={telemetry_s2['p50_total_latency_ms']}ms, Violations Prevented={telemetry_s2['compliance_violations_prevented']}")
    assert any(n["priority"] == "CRITICAL" for n in nudges_s2), "Scenario 2 should have produced a CRITICAL compliance alert"

    # 4. Test Scenario 3: Rising Frustration
    print("\n--- 🧪 TEST 3: SCENARIO 3 (RISING FRUSTRATION) ---")
    session_id = "test_q4_s3"
    s3 = next(s for s in scenarios if s["scenario_id"] == "rising_frustration")
    nudges_s3 = []
    for turn in s3["timeline"]:
        res = httpx.post(f"{base_url}/api/v1/q4/process-chunk", json={
            "session_id": session_id,
            "chunk_index": turn["turn_index"] + 1,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "start_time": turn["start_time"],
            "end_time": turn["end_time"],
            "is_noisy": False
        })
        data = res.json()
        for n in data.get("new_nudges", []):
            nudges_s3.append(n)
            print(f"  ⚠️ [DE-ESCALATION NUDGE at {turn['start_time']}s] Priority: {n['priority']} | {n['headline']}")

    assert len(nudges_s3) > 0, "Scenario 3 should have produced a de-escalation nudge"

    # 5. Test Scenario 4: Noisy Ambient Audio
    print("\n--- 🧪 TEST 4: SCENARIO 4 (NOISY AMBIENT SUPPRESSION) ---")
    session_id = "test_q4_s4"
    s4 = next(s for s in scenarios if s["scenario_id"] == "noisy_audio")
    nudges_s4 = []
    for turn in s4["timeline"]:
        res = httpx.post(f"{base_url}/api/v1/q4/process-chunk", json={
            "session_id": session_id,
            "chunk_index": turn["turn_index"] + 1,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "start_time": turn["start_time"],
            "end_time": turn["end_time"],
            "is_noisy": True
        })
        data = res.json()
        for n in data.get("new_nudges", []):
            nudges_s4.append(n)

    telemetry_s4 = httpx.get(f"{base_url}/api/v1/q4/telemetry/{session_id}").json()
    print(f"  📊 Telemetry: Nudges Generated={telemetry_s4['total_nudges_generated']}, Noise Suppressed={telemetry_s4['total_nudges_suppressed']}")
    assert len(nudges_s4) == 0, "Scenario 4 should have 0 false-positive alerts (100% suppressed)"

    print("\n🎉 ALL 4 QUESTION 4 SCENARIOS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_tests()
