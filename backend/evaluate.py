import json
import time
import statistics
import requests
from pathlib import Path
from collections import defaultdict

# Use 127.0.0.1 instead of localhost to avoid Windows IPv6 DNS resolution delay
BASE_URL = "http://127.0.0.1:8000"

_BASE_DIR = Path(__file__).resolve().parent
_CANDIDATE_PATHS = [
    _BASE_DIR / "data" / "benchmark_3000_edge_heavy.json",
    _BASE_DIR.parent / "data" / "benchmark_3000_edge_heavy.json",
    _BASE_DIR / "benchmark_3000_edge_heavy.json",
    _BASE_DIR.parent / "benchmark_3000_edge_heavy.json",
]

_TEST_FILE = next((p for p in _CANDIDATE_PATHS if p.exists()), None)
if _TEST_FILE is None:
    raise FileNotFoundError("Could not find benchmark_3000_edge_heavy.json in expected directories.")

TEST_CASES = json.loads(_TEST_FILE.read_text(encoding="utf-8"))


def evaluate_case(session: requests.Session, text: str, expected_entities: list[str]):
    start = time.perf_counter()
    res = session.post(f"{BASE_URL}/api/mask", json={"text": text}, timeout=30)
    res.raise_for_status()
    latency_ms = (time.perf_counter() - start) * 1000.0

    data = res.json()
    mappings = data.get("mappings", {})
    detected_values = list(mappings.values())

    matched_expected = set()
    matched_detected = set()

    for d_idx, det in enumerate(detected_values):
        det_norm = det.strip().lower()
        for e_idx, exp in enumerate(expected_entities):
            if e_idx in matched_expected:
                continue
            exp_norm = exp.strip().lower()
            if det_norm == exp_norm or exp_norm in det_norm or det_norm in exp_norm:
                matched_expected.add(e_idx)
                matched_detected.add(d_idx)
                break

    tp = len(matched_expected)
    fn = len(expected_entities) - tp
    fp = len(detected_values) - len(matched_detected)

    return tp, fp, fn, latency_ms


def main():
    print(f"Loaded {len(TEST_CASES)} test cases from: {_TEST_FILE.name}")
    print("Running local PII detection & masking benchmark...\n")

    stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "latencies": []})
    category_order = []

    with requests.Session() as session:
        # Warm-up request
        session.post(f"{BASE_URL}/api/mask", json={"text": "warmup"}, timeout=10)

        for idx, item in enumerate(TEST_CASES, 1):
            if idx % 200 == 0:
                print(f"  Evaluated {idx}/{len(TEST_CASES)} prompts...", end="\r", flush=True)

            cat = item.get("category", "Uncategorized")
            if cat not in stats:
                category_order.append(cat)

            text = item.get("text") or item.get("prompt", "")
            expected = item.get("entities", [])

            tp, fp, fn, lat = evaluate_case(session, text, expected)
            stats[cat]["tp"] += tp
            stats[cat]["fp"] += fp
            stats[cat]["fn"] += fn
            stats[cat]["latencies"].append(lat)

    print(" " * 50, end="\r")
    print("=" * 96)
    print(f"{'Test Category':<42} | {'TP':>6} | {'FP':>6} | {'FN':>6} | {'Avg Latency (ms)':>18}")
    print("-" * 96)

    total_tp = total_fp = total_fn = 0
    all_latencies = []

    for cat in category_order:
        s = stats[cat]
        tp, fp, fn = s["tp"], s["fp"], s["fn"]
        avg_lat = statistics.mean(s["latencies"]) if s["latencies"] else 0.0

        total_tp += tp
        total_fp += fp
        total_fn += fn
        all_latencies.extend(s["latencies"])

        print(f"{cat:<42} | {tp:>6} | {fp:>6} | {fn:>6} | {avg_lat:>15.2f} ms")

    overall_avg_lat = statistics.mean(all_latencies) if all_latencies else 0.0
    precision = (total_tp / (total_tp + total_fp) * 100) if (total_tp + total_fp) > 0 else 0.0
    recall = (total_tp / (total_tp + total_fn) * 100) if (total_tp + total_fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("-" * 96)
    print(f"{'Total / Average':<42} | {total_tp:>6} | {total_fp:>6} | {total_fn:>6} | {overall_avg_lat:>15.2f} ms")
    print("=" * 96)
    print(f"Overall Precision : {precision:.2f}%")
    print(f"Overall Recall    : {recall:.2f}%")
    print(f"Overall F1-Score  : {f1:.2f}%")
    print("=" * 96)


if __name__ == "__main__":
    main()
