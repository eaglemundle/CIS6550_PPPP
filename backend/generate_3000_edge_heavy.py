import json
import random

random.seed(42)

FIRST_NAMES = [
    "Liam", "Noah", "Oliver", "Mateo", "Lucas", "Minji", "Joonho", "Seojun", "Jiwoo", "Haruto",
    "Priya", "Arjun", "Fatima", "Omar", "Chloe", "Jean-Luc", "Marie-Claire", "Amina", "Wei", "Sven"
]
LAST_NAMES = [
    "Smith", "Tremblay", "Gagnon", "Roy", "Lee", "MacDonald", "O'Connor", "Picard-Tremblay",
    "Patel", "Singh", "Wong", "Nguyen", "Al-Mansoor", "Khan", "Bouchard", "Van Der Berg", "Kim"
]

COMPLEX_FIRST = ["Jean-Luc", "Marie-Claire", "Min-Ji", "Abdul-Rahman"]
COMPLEX_LAST = ["O'Connor", "Picard-Tremblay", "Al-Mansoor", "Van Der Berg"]

POSTAL_PREFIXES = ["N1G", "M5V", "K1A", "V6B", "T2P", "H3Z", "R3C", "S7K", "B3H", "L5B"]
CITIES = ["Guelph, ON", "Toronto, ON", "Ottawa, ON", "Vancouver, BC", "Calgary, AB", "Montreal, QC", "Waterloo, ON"]

MEDICATIONS_KNOWN = ["amoxicillin", "lisinopril", "metformin", "atorvastatin", "omeprazole", "ibuprofen"]
MEDICATIONS_OOV = [
    "semaglutide", "tirzepatide", "adalimumab", "apixaban", "empagliflozin", "pembrolizumab",
    "ustekinumab", "dupilumab", "risankizumab", "sacubitril", "dapagliflozin", "ozanimod"
]

# IT frameworks and mathematical terms resembling person/location names (for False Positive testing)
AMBIGUOUS_TECH = [
    "Jenkins", "Docker", "Django", "Julia", "Cassandra", "Aurora", "Phoenix", "Jasper",
    "maven", "Ruby", "Swift", "Alice", "Bob", "Charlie", "Taylor", "Morgan"
]

UNSTRUCTURED_PW = ["winter2026!", "Guelph#99", "Summer$2025", "MapleLeaf!1", "Rocket*88", "BlueJay@42", "p@ssw0rd99"]


def gen_valid_ca_sin(formatted=True):
    # Generate a valid 9-digit Canadian SIN passing the Luhn checksum algorithm (first digit 1-9)
    digits = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(7)]
    total = 0
    for i, d in enumerate(digits):
        val = d * (2 if i % 2 == 1 else 1)
        total += val if val < 10 else (val - 9)
    check = (10 - (total % 10)) % 10
    digits.append(check)
    s = "".join(map(str, digits))
    if not formatted:
        return s
    sep = random.choice(["-", " "])
    return f"{s[:3]}{sep}{s[3:6]}{sep}{s[6:]}"


def gen_invalid_ca_sin():
    # Generate an invalid Canadian SIN with an intentionally corrupted Luhn check digit (for False Positive testing)
    valid = gen_valid_ca_sin(formatted=False)
    wrong_last = str((int(valid[-1]) + 1) % 10)
    s = valid[:-1] + wrong_last
    return f"{s[:3]}-{s[3:6]}-{s[6:]}"


def gen_ca_postal(formatted=True):
    p1 = random.choice(POSTAL_PREFIXES)
    p2 = f"{random.randint(0, 9)}{random.choice('ABCEGHJKLMNPRSTVWXYZ')}{random.randint(0, 9)}"
    return f"{p1} {p2}" if formatted else f"{p1}{p2}".lower()


def gen_phone():
    area = random.choice(["519", "416", "647", "613", "604", "403", "514", "226"])
    return f"{area}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def generate_dataset(total_samples=3000):
    dataset = []

    # Distribute 3,000 prompts: 40% (1,200) Baseline scenarios and 60% (1,800) Edge-Case scenarios
    category_weights = [
        # Baseline Categories (40% = 1,200)
        ("Baseline: Identity & Canadian IDs", 200),
        ("Baseline: Academic & Vehicle", 200),
        ("Baseline: Medical / PHI", 200),
        ("Baseline: Credentials & Secrets", 200),
        ("Baseline: Source Code & DB", 200),
        ("Baseline: Clean Prompt (No PII)", 200),

        # Edge-Case Categories (60% = 1,800)
        ("Edge: Unformatted & Lowercase", 250),
        ("Edge: Unseen Medical Terms (OOV)", 250),
        ("Edge: Ambiguous Tech Terms (FP)", 250),
        ("Edge: Unstructured Secrets", 250),
        ("Edge: Multicultural & Hyphenated Names", 200),
        ("Edge: Obfuscated Contact & IDs", 200),
        ("Edge: Invalid Checksum & Dummy PII (FP)", 200),
        ("Edge: Code Variables & Math 'sin' (FP)", 200),
    ]

    for cat, count in category_weights:
        for _ in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            name = f"{first_name} {last_name}"
            sin = gen_valid_ca_sin(True)
            postal = gen_ca_postal(True)
            phone = gen_phone()
            clean_last = last_name.lower().replace("'", "").replace(" ", "")
            email = f"{first_name.lower()}.{clean_last}@uoguelph.ca"

            if cat == "Baseline: Identity & Canadian IDs":
                text = f"Verify tax record for {name}, SIN {sin}, postal code {postal} in {random.choice(CITIES)}."
                entities = [name, sin, postal]

            elif cat == "Baseline: Academic & Vehicle":
                sid = f"11{random.randint(100000, 999999)}"
                plate = f"{''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ', k=4))}-{random.randint(100, 999)}"
                text = f"Student {name} (ID: {sid}) registered Ontario plate {plate}."
                entities = [name, sid, plate]

            elif cat == "Baseline: Medical / PHI":
                med = random.choice(MEDICATIONS_KNOWN)
                ohip = f"{random.randint(1000, 9999)}-{random.randint(100, 999)}-{random.randint(100, 999)}"
                text = f"Patient {name} (OHIP: {ohip}) prescribed {med} 500mg twice daily."
                entities = [name, ohip, med]

            elif cat == "Baseline: Credentials & Secrets":
                api_key = f"sk-proj-{''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=24))}"
                text = f"Revoke compromised key OPENAI_API_KEY={api_key} in production."
                entities = [api_key]

            elif cat == "Baseline: Source Code & DB":
                db_uri = f"postgresql://admin:Pass{random.randint(100, 999)}@10.0.{random.randint(1, 254)}.{random.randint(1, 254)}:5432/appdb"
                text = f"Fix connection pool timeout for {db_uri}."
                entities = [db_uri]

            elif cat == "Baseline: Clean Prompt (No PII)":
                text = random.choice([
                    "Explain the seven foundational principles of Privacy by Design.",
                    "How does Chrome Manifest V3 restrict remotely hosted code?",
                    "Compare latency between local FastAPI inference and cloud REST APIs."
                ])
                entities = []

            elif cat == "Edge: Unformatted & Lowercase":
                lname = name.lower()
                rsin = gen_valid_ca_sin(False)
                rpostal = gen_ca_postal(False)
                text = f"pls check profile for {lname} sin {rsin} postal {rpostal} asap"
                entities = [lname, rsin, rpostal]

            elif cat == "Edge: Unseen Medical Terms (OOV)":
                oov = random.choice(MEDICATIONS_OOV)
                text = f"Check drug interactions for {name} taking {oov} alongside standard therapy."
                entities = [name, oov]

            elif cat == "Edge: Ambiguous Tech Terms (FP)":
                t1, t2, t3 = random.sample(AMBIGUOUS_TECH, 3)
                text = f"Migrate {t1} worker jobs to {t2} and deploy the {t3} backend service."
                entities = []

            elif cat == "Edge: Unstructured Secrets":
                pw = random.choice(UNSTRUCTURED_PW)
                text = f"Hey {first_name}, use {pw} to unlock the staging VM if your key expires."
                entities = [first_name, pw]

            elif cat == "Edge: Multicultural & Hyphenated Names":
                complex_name = f"{random.choice(COMPLEX_FIRST)} {random.choice(COMPLEX_LAST)}"
                text = f"Schedule compliance interview with {complex_name} regarding PIPEDA audit."
                entities = [complex_name]

            elif cat == "Edge: Obfuscated Contact & IDs":
                obf_email = email.replace("@", " [at] ").replace(".", " [dot] ")
                obf_phone = phone.replace("-", " dot ")
                text = f"Reach out to {name} via {obf_email} or call {obf_phone} after 5pm."
                entities = [name, obf_email, obf_phone]

            elif cat == "Edge: Invalid Checksum & Dummy PII (FP)":
                fake_sin = gen_invalid_ca_sin()
                text = f"Unit test mock payload: sin='{fake_sin}', ip='127.0.0.1', email='test@example.com'."
                entities = []

            elif cat == "Edge: Code Variables & Math 'sin' (FP)":
                text = "In Python, compute `sin_val = math.sin(theta)` and log `user_id = 'guest_01'`."
                entities = []

            dataset.append({
                "id": len(dataset) + 1,
                "category": cat,
                "text": text,
                "prompt": text,
                "entities": entities
            })


    random.shuffle(dataset)
    for idx, item in enumerate(dataset, 1):
        item["id"] = idx

    return dataset


if __name__ == "__main__":
    data = generate_dataset(3000)
    total_entities = sum(len(item["entities"]) for item in data)
    edge_count = sum(1 for item in data if item["category"].startswith("Edge:"))
    with open("data/benchmark_3000_edge_heavy.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} prompts ({edge_count} Edge Cases / {len(data)-edge_count} Baseline) with {total_entities} ground-truth entities.")
