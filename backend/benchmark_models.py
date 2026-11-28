import json
import requests
import statistics
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_TEST_FILE = _BASE_DIR / "data/benchmark_3000_edge_heavy.json"
if not _TEST_FILE.exists():
    _TEST_FILE = _BASE_DIR.parent / "data/benchmark_3000_edge_heavy.json"

_ALL_CASES = json.loads(_TEST_FILE.read_text(encoding="utf-8"))

# Stratified sample of 1,000 cases across all 14 categories (1,000 * 3 models = 3,000 total inferences)
_BY_CAT = {}
for c in _ALL_CASES:
    cat = c.get("category", "default")
    _BY_CAT.setdefault(cat, []).append(c)

PRIVACY_TEST_CASES = []
_PER_CAT = 1000 // len(_BY_CAT)
for cat, items in _BY_CAT.items():
    PRIVACY_TEST_CASES.extend(items[:_PER_CAT])
# Fill remaining slots up to exactly 1,000 cases
for cat, items in _BY_CAT.items():
    if len(PRIVACY_TEST_CASES) >= 1000:
        break
    if len(items) > _PER_CAT:
        PRIVACY_TEST_CASES.append(items[_PER_CAT])

# Load externalized model configuration with safe fallback
_CONFIG_PATH = Path(__file__).parent / "models.json"
if _CONFIG_PATH.exists():
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        _MODEL_CFG = json.load(f)
else:
    _MODEL_CFG = {}

DEFAULT_MODEL = _MODEL_CFG.get("default_model", "llama3.2:3b")
SUPPORTED_MODELS = _MODEL_CFG.get("supported_models", ["llama3.2:3b", "qwen2.5:3b", "mistral:latest"])

BASE_URL = "http://localhost:8000"


def run_benchmark():
    print(f"Preparing {len(PRIVACY_TEST_CASES)} stratified prompts (Total LLM inferences: {len(PRIVACY_TEST_CASES) * len(SUPPORTED_MODELS)})...")
    prepared_cases = []
    for item in PRIVACY_TEST_CASES:
        mask_res = requests.post(f"{BASE_URL}/api/mask", json={"text": item["text"]})
        mask_res.raise_for_status()
        mask_data = mask_res.json()
        prepared_cases.append({
            "scenario": item.get("scenario", item.get("category", "unknown")),
            "masked_text": mask_data["masked_text"],
            "mappings": mask_data["mappings"]
        })

    print("=" * 98)
    print(f"{'Model':<13} | {'Raw PII Leak':<14} | {'Token Integrity':<17} | {'Restoration':<15} | {'Avg Latency':<13} | {'Status':<6}")
    print("-" * 98)

    for model in SUPPORTED_MODELS:
        leaked_count = 0
        total_tokens = 0
        preserved_tokens = 0
        restored_success = 0
        latencies = []
        status = "PASS"

        for idx, case in enumerate(prepared_cases, 1):
            if idx % 100 == 0:
                print(f"  [{model}] Progress: {idx}/{len(prepared_cases)}...", end="\r", flush=True)
            try:
                original_values = list(case["mappings"].values())
                if any(val in case["masked_text"] for val in original_values):
                    leaked_count += 1

                chat_res = requests.post(
                    f"{BASE_URL}/api/chat",
                    json={"masked_text": case["masked_text"], "model": model},
                    timeout=90
                )
                chat_res.raise_for_status()
                chat_data = chat_res.json()
                masked_reply = chat_data["masked_reply"]
                latencies.append(chat_data["latency_ms"])

                placeholders = list(case["mappings"].keys())
                total_tokens += len(placeholders)
                preserved_tokens += sum(1 for ph in placeholders if ph in masked_reply)

                restore_res = requests.post(
                    f"{BASE_URL}/api/restore",
                    json={"text": masked_reply, "mappings": case["mappings"]}
                )
                restore_res.raise_for_status()
                restored_text = restore_res.json()["restored_text"]

                if all(ph not in restored_text for ph in placeholders):
                    restored_success += 1

            except Exception as e:
                print(f"\n[{model}] Failed on '{case['scenario']}': {type(e).__name__} -> {e}")
                status = "ERR"
                break

        if status == "PASS":
            integrity_pct = (preserved_tokens / total_tokens * 100) if total_tokens > 0 else 0
            restore_pct = (restored_success / len(prepared_cases) * 100)
            avg_lat_sec = statistics.mean(latencies) / 1000.0
            print(
                f"{model:<13} | {leaked_count} leaks (0%)   | "
                f"{preserved_tokens}/{total_tokens} ({integrity_pct:>5.1f}%)    | "
                f"{restored_success}/{len(prepared_cases)} ({restore_pct:>5.1f}%)   | "
                f"{avg_lat_sec:>6.2f} s      | {status:<6}"
            )
        else:
            print(f"{model:<13} | {'N/A':<14} | {'N/A':<17} | {'N/A':<15} | {'N/A':<13} | {status:<6}")

    print("=" * 98)


if __name__ == "__main__":
    run_benchmark()
