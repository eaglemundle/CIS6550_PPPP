import requests
import statistics

API_URL = "http://localhost:8000/api/mask"

# Synthetic test dataset covering diverse privacy scenarios (Proposal Objective 3)
TEST_CASES = [
    {
        "category": "Identity & Canadian IDs",
        "text": "My name is Sarah Jenkins, my SIN is 123-456-789, and my postal code is N1G 2W1.",
        "expected_values": ["Sarah Jenkins", "123-456-789", "N1G 2W1"]
    },
    {
        "category": "Academic & Vehicle",
        "text": "Student Michael Chen (Student ID: 1184920) registered vehicle plate ABCD 123.",
        "expected_values": ["Michael Chen", "Student ID: 1184920", "ABCD 123"]
    },
    {
        "category": "Medical / PHI",
        "text": "Patient David Kim was diagnosed with diabetes and prescribed insulin at the clinic.",
        "expected_values": ["David Kim", "diabetes", "insulin"]
    },
    {
        "category": "Credentials & Secrets",
        "text": "Deploy using API key sk-proj1234567890abcdefghij and password=SecretPass99.",
        "expected_values": ["sk-proj1234567890abcdefghij", "password=SecretPass99"]
    },
    {
        "category": "Source Code & DB",
        "text": "Developer EMP-4092 connected to postgres://admin:pass123@10.0.0.5:5432/prod to run def get_users(): pass.",
        "expected_values": ["EMP-4092", "postgres://admin:pass123@10.0.0.5:5432/prod", "def get_users(): pass."]
    },
    {
        "category": "Financial & Contact",
        "text": "Transfer funds to account #987654321 or email sarah.j@uoguelph.ca for confirmation.",
        "expected_values": ["account #987654321", "sarah.j@uoguelph.ca"]
    },
    {
        "category": "Clean Prompt (No PII)",
        "text": "Can you explain how asymmetric encryption works in modern web browsers?",
        "expected_values": []
    }
]

def run_evaluation():
    total_tp = 0  # True Positives (Correctly detected PII)
    total_fp = 0  # False Positives (Non-PII falsely flagged)
    total_fn = 0  # False Negatives (Actual PII missed)
    latencies = []

    print("=" * 65)
    print(f"{'Category':<25} | {'TP':<3} | {'FP':<3} | {'FN':<3} | {'Latency (ms)':<12}")
    print("-" * 65)

    for case in TEST_CASES:
        response = requests.post(API_URL, json={"text": case["text"]})
        response.raise_for_status()
        data = response.json()

        predicted_values = [item["value"] for item in data["detected_items"]]
        expected_values = case["expected_values"]
        latency = data["latency_ms"]
        latencies.append(latency)

        tp = sum(1 for val in predicted_values if val in expected_values)
        fp = sum(1 for val in predicted_values if val not in expected_values)
        fn = sum(1 for val in expected_values if val not in predicted_values)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        print(f"{case['category']:<25} | {tp:<3} | {fp:<3} | {fn:<3} | {latency:<12.2f}")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    avg_latency = statistics.mean(latencies)

    print("=" * 65)
    print(f"Total True Positives (TP) : {total_tp}")
    print(f"Total False Positives (FP): {total_fp}")
    print(f"Total False Negatives (FN): {total_fn}")
    print("-" * 65)
    print(f"Precision                 : {precision * 100:.2f}%")
    print(f"Recall                    : {recall * 100:.2f}%")
    print(f"F1-Score                  : {f1_score * 100:.2f}%")
    print(f"Average Masking Latency   : {avg_latency:.2f} ms")
    print("=" * 65)

if __name__ == "__main__":
    run_evaluation()
