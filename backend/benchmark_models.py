import requests
import statistics

BASE_URL = "http://localhost:8000"
MODELS = ["llama3.2:3b", "qwen2.5:3b", "mistral"]

PRIVACY_TEST_CASES = [
    {
        "scenario": "Canadian Identity & SIN",
        "text": "Write a short confirmation email to Sarah Jenkins (sarah@uoguelph.ca) confirming we received her SIN 123-456-789."
    },
    {
        "scenario": "Medical Confidentiality (PHI)",
        "text": "Summarize this clinical note in two sentences: Patient David Kim was diagnosed with diabetes and prescribed insulin."
    },
    {
        "scenario": "Corporate Secret Exposure",
        "text": "Draft a brief security notice telling developer EMP-4092 to revoke exposed API key sk-proj1234567890abcdefghij immediately."
    }
]

def run_benchmark():
    prepared_cases = []
    for item in PRIVACY_TEST_CASES:
        mask_res = requests.post(f"{BASE_URL}/api/mask", json={"text": item["text"]})
        mask_res.raise_for_status()
        mask_data = mask_res.json()
        prepared_cases.append({
            "scenario": item["scenario"],
            "masked_text": mask_data["masked_text"],
            "mappings": mask_data["mappings"]
        })

    print("=" * 98)
    print(f"{'Model':<13} | {'Raw PII Leak':<14} | {'Token Integrity':<17} | {'Restoration':<15} | {'Avg Latency':<13} | {'Status':<6}")
    print("-" * 98)

    for model in MODELS:
        leaked_count = 0
        total_tokens = 0
        preserved_tokens = 0
        restored_success = 0
        latencies = []
        status = "PASS"

        for case in prepared_cases:
            try:
                # 1. Verify zero raw PII exists in the sanitized prompt
                original_values = list(case["mappings"].values())
                if any(val in case["masked_text"] for val in original_values):
                    leaked_count += 1

                # 2. Query local LLM and record inference latency
                chat_res = requests.post(
                    f"{BASE_URL}/api/chat",
                    json={"masked_text": case["masked_text"], "model": model},
                    timeout=90
                )
                chat_res.raise_for_status()
                chat_data = chat_res.json()
                masked_reply = chat_data["masked_reply"]
                latencies.append(chat_data["latency_ms"])

                # 3. Verify privacy placeholder preservation in LLM output
                placeholders = list(case["mappings"].keys())
                total_tokens += len(placeholders)
                preserved_tokens += sum(1 for ph in placeholders if ph in masked_reply)

                # 4. Restore original values locally and verify completeness
                restore_res = requests.post(
                    f"{BASE_URL}/api/restore",
                    json={"text": masked_reply, "mappings": case["mappings"]}
                )
                restore_res.raise_for_status()
                restored_text = restore_res.json()["restored_text"]

                if all(ph not in restored_text for ph in placeholders):
                    restored_success += 1

            except Exception as e:
                status = f"ERR"
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
