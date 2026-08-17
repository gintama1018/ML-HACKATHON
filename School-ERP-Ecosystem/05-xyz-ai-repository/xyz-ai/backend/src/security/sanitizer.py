import re
from typing import Tuple, List

# Adversarial prompt injection signatures
INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+)?(unrestricted|evil|admin|principal|developer|dan|jailbreak)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?rules", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(initial|hidden|system)\s+instructions", re.IGNORECASE),
    re.compile(r"sudo\s+mode|developer\s+mode|god\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(security|auth|permission|rbac)", re.IGNORECASE),
    re.compile(r"override\s+system\s+role", re.IGNORECASE),
    re.compile(r"output\s+database\s+(credentials|passwords|connection\s+string)", re.IGNORECASE),
]

# Sensitive credentials & internal pattern filters
SENSITIVE_OUTPUT_PATTERNS: List[re.Pattern] = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # API keys
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE), # Google API key
    re.compile(r"postgresql://[^:]+:[^@]+@[^/]+/[a-zA-Z0-9_]+", re.IGNORECASE), # Postgres connection
    re.compile(r"sqlite:///[^\s]+", re.IGNORECASE), # Sqlite connection string
    re.compile(r"xyz_school_salt_[0-9]+", re.IGNORECASE), # System salt
    re.compile(r"[a-f0-9]{64}", re.IGNORECASE), # 64-char sha256 password hashes
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", re.IGNORECASE), # Raw JWT strings
]

def detect_prompt_injection(user_input: str) -> Tuple[bool, str]:
    """
    Inspect input text for malicious prompt injection or jailbreak attempts.
    Returns: (is_injection, matched_pattern_description)
    """
    if not user_input or not isinstance(user_input, str):
        return False, ""
        
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(user_input)
        if match:
            return True, f"Blocked adversarial pattern match: '{match.group(0)}'"
            
    return False, ""

def filter_sensitive_output(text: str) -> str:
    """
    Scan outgoing text and mask any accidentally leaked internal secrets,
    credentials, or connection strings.
    """
    if not text or not isinstance(text, str):
        return text
        
    sanitized = text
    for pattern in SENSITIVE_OUTPUT_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SENSITIVE_SECRET]", sanitized)
        
    return sanitized
