OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

# Regex-based PII rules: (entity_type, pattern_name, regex, confidence_score)
REGEX_RULES = [
    # 1. Academic & Student Identifiers
    ("STUDENT_ID", "student_id_labeled", r"(?i)(?:student\s*(?:id|no|number|#)|uog\s*id|id\s*#)\s*[:=]?\s*\d{7,9}\b", 0.92),
    ("STUDENT_ID", "uog_7digit_id", r"\b[01]\d{6}\b", 0.75),

    # 2. Canadian Government & Regional IDs
    ("CA_SIN", "ca_sin", r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b", 0.85),
    ("CA_POSTAL_CODE", "ca_postal", r"\b[A-Za-z]\d[A-Za-z][-\s]?\d[A-Za-z]\d\b", 0.85),
    ("CA_DRIVER_LICENSE", "on_dl", r"\b[A-Z]\d{4}[-\s]?\d{5}[-\s]?\d{5}\b", 0.90),
    ("CA_HEALTH_CARD", "ohip", r"\b\d{4}[-\s]?\d{3}[-\s]?\d{3}[-\s]?[A-Z]{2}\b", 0.90),
    ("CA_PASSPORT", "ca_passport", r"\b[A-Z]{2}\d{6}\b", 0.80),
    ("CA_LICENSE_PLATE", "on_plate", r"\b[A-Z]{4}[-\s]?\d{3}\b", 0.78),

    # 3. Corporate Credentials, Keys & Secrets
    ("API_KEY", "openai_aws_gh_stripe", r"\b(sk-[a-zA-Z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|rk_live_[a-zA-Z0-9]{24})\b", 0.95),
    ("API_KEY", "jwt_token", r"\beyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b", 0.95),
    ("PRIVATE_KEY", "pem_ssh_key", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", 0.98),
    ("CREDENTIAL_SECRET", "pwd_secret_assign", r"(?i)(?:password|passwd|pwd|secret|api_secret|access_token|auth_token)\s*[:=]\s*['\"]?([^\s'\",.;]{4,})['\"]?", 0.90),

    ("DB_CONNECTION_STRING", "db_uri", r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|mssql)://[^\s'\"]+", 0.95),

    # 4. Network & Internal Infrastructure
    ("MAC_ADDRESS", "mac_addr", r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b", 0.90),
    ("INTERNAL_PATH", "win_unix_path", r"(?:[A-Za-z]:\\(?:[\w\-. ]+\\)+[\w\-. ]+|/(?:Users|home|var|etc|opt|srv)/(?:[\w\-.]+/)+[\w\-.]+)", 0.80),

    # 5. Proprietary Source Code & Database Queries
    ("SOURCE_CODE", "code_block", r"```[\s\(\S\)]*?```", 0.95),
    ("SOURCE_CODE", "func_sql_def", r"\b(?:def|function|class|SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+.+\s+SET)\b[^\n;]+", 0.80),

    # 6. Financial & HR Information
    ("BANK_ACCOUNT", "routing_acct", r"(?i)(?:account|acct|transit|institution|routing)\s*(?:#|no|number)?\s*[:=]?\s*\d{3,17}\b", 0.85),
    ("CRYPTO_WALLET", "btc_eth", r"\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b", 0.90),
    ("EMPLOYEE_ID", "emp_id", r"(?i)(?:employee|emp|staff)\s*(?:id|no|number|#)?\s*[:=]?\s*[A-Z0-9-]{4,12}\b", 0.85),
]

# Keyword-based Medical & Health Info (PHI)
MEDICAL_DENY_LIST = [
    "diabetes", "hypertension", "asthma", "depression", "anxiety", "cancer",
    "migraine", "insomnia", "arrhythmia", "pneumonia", "arthritis", "epilepsy",
    "biopsy", "chemotherapy", "insulin", "antidepressant", "MRI", "CT scan",
    "ADHD", "bipolar", "schizophrenia", "HIV", "hepatitis", "allergy", "pregnancy",
    "prescription", "dosage", "blood pressure", "cholesterol", "surgery"
]

MEDICAL_CONTEXT_WORDS = [
    "diagnosed", "symptom", "symptoms", "patient", "prescribed",
    "medication", "treatment", "suffering from", "clinic", "hospital", "doctor"
]

# Entities that immediately trigger a "HIGH" risk level
HIGH_RISK_ENTITIES = {
    "CA_SIN", "CA_DRIVER_LICENSE", "CA_HEALTH_CARD", "CA_PASSPORT", "US_SSN", "US_PASSPORT",
    "CREDIT_CARD", "BANK_ACCOUNT", "CRYPTO_WALLET",
    "API_KEY", "PRIVATE_KEY", "CREDENTIAL_SECRET", "DB_CONNECTION_STRING",
    "SOURCE_CODE", "MEDICAL_INFO", "STUDENT_ID"
}

# Words to ignore so they are not falsely flagged as organizations or names
ALLOW_LIST = [
    "SIN", "SSN", "API", "LLM", "AI", "PII", "OHIP", "SQL", "AWS",
    "UOG", "ID", "DB", "SSH", "MAC", "IP", "Plate", "Student", "Employee"
]
