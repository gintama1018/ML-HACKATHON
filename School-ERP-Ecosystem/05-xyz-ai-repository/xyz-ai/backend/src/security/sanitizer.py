import re
from typing import Tuple, List

# Multi-vector adversarial prompt injection patterns (English, Hindi, and transliterated)
INJECTION_PATTERNS: List[re.Pattern] = [
    # 1. Instruction overrides / jailbreaks
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|former)\s+(instructions|directives|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|the)\s+(rules|instructions|guidelines)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an?\s+)?(unrestricted|evil|admin|principal|developer|dan|jailbreak|chaos)", re.IGNORECASE),
    re.compile(r"dan\s+(mode|unrestricted)|jailbreak\s+mode", re.IGNORECASE),
    re.compile(r"sudo\s+mode|developer\s+mode|god\s+mode|admin\s+mode|root\s+mode", re.IGNORECASE),
    
    # 2. System prompt extraction attempts
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(initial|hidden|system|developer)\s+(instructions|prompt|rules)", re.IGNORECASE),
    re.compile(r"show\s+(me\s+)?(your\s+)?(initial|hidden|system)\s+(prompt|instructions)", re.IGNORECASE),
    re.compile(r"print\s+(your\s+)?(system\s+prompt|instructions\s+above)", re.IGNORECASE),
    re.compile(r"repeat\s+the\s+words\s+above", re.IGNORECASE),
    re.compile(r"what\s+(is|are)\s+your\s+(initial|hidden|system)\s+(instructions|prompt)", re.IGNORECASE),
    
    # 3. Security bypass and role overrides
    re.compile(r"bypass\s+(security|auth|permission|rbac|policy|filters)", re.IGNORECASE),
    re.compile(r"override\s+(system\s+role|permissions|security)", re.IGNORECASE),
    re.compile(r"i\s+am\s+the\s+(admin|principal|developer)\s*,?\s*(override|give\s+me)", re.IGNORECASE),
    
    # 4. Credential & secret phishing
    re.compile(r"output\s+database\s+(credentials|passwords|connection\s+string|keys)", re.IGNORECASE),
    re.compile(r"give\s+me\s+(the\s+)?(database\s+password|principal\s+password|api\s+key|jwt\s+secret)", re.IGNORECASE),
    re.compile(r"what\s+is\s+the\s+(database\s+password|principal\s+password|jwt\s+secret)", re.IGNORECASE),
    re.compile(r"show\s+(all\s+)?(passwords|hashes|secrets)", re.IGNORECASE),
    
    # 5. Multilingual jailbreak patterns (Hindi)
    re.compile(r"पिछला\s+निर्देश\s+(भूल|त्याग)", re.IGNORECASE),
    re.compile(r"सिस्टम\s+प्रॉम्प्ट\s+(दिखाओ|बताओ)", re.IGNORECASE),
    re.compile(r"पासवर्ड\s+(बताओ|दिखाओ)", re.IGNORECASE),

    # 6. Multilingual jailbreak patterns (Tamil)
    re.compile(r"முந்தைய\s+வழிமுறை\s+(மற|மற|புறக்கணி)", re.IGNORECASE),
    re.compile(r"கடவுச்சொல்\s+(சொல்|காட்டு)", re.IGNORECASE),
    re.compile(r"அமைப்பு\s+வழிமுறை\s+(காட்டு|சொல்)", re.IGNORECASE),

    # 7. Multilingual jailbreak patterns (Bengali)
    re.compile(r"পূর্ববর্তী\s+নির্দেশ\s+(ভুলে|উপেক্ষা)", re.IGNORECASE),
    re.compile(r"পাসওয়ার্ড\s+(বলুন|দেখান)", re.IGNORECASE),

    # 8. Multilingual jailbreak patterns (Urdu)
    re.compile(r"پچھلی\s+ہدایات\s+(بھول|نظرانداز)", re.IGNORECASE),
    re.compile(r"پاس\s+ورڈ\s+(بتاؤ|دکھاؤ)", re.IGNORECASE),

    # 9. Obfuscation: Character substitution / l33tspeak variants
    re.compile(r"ign0re\s+(pr3vious|previous)\s+(instr|inst)", re.IGNORECASE),
    re.compile(r"disreg4rd|byp4ss|j41lbr3ak", re.IGNORECASE),
    re.compile(r"y.u\s+ar.\s+now\s+(an?\s+)?(unr.strict|evil|adm.n)", re.IGNORECASE),

    # 10. Indirect role-claim injection
    re.compile(r"(act|pretend|behave)\s+as\s+(if\s+you\s+(are|were)\s+)?(an?\s+)?(admin|principal|unrestricted|teacher\s+with\s+all)", re.IGNORECASE),
    re.compile(r"role\s+play\s+as\s+(an?\s+)?(admin|school\s+admin|system\s+admin|developer)", re.IGNORECASE),

    # 11. Token stuffing / delimiter injection
    re.compile(r"<\|?im_start\|?>|<\|?system\|?>|<\|?user\|?>|\[INST\]|\[SYS\]", re.IGNORECASE),
    re.compile(r"###\s*(instruction|system|override|admin)", re.IGNORECASE),

    # 12. Payload in base64-like blobs (heuristic: >40 char alphanum string mid-sentence)
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
]

# Sensitive credential leakage regex masks
SENSITIVE_OUTPUT_PATTERNS: List[re.Pattern] = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    re.compile(r"postgresql://[^:]+:[^@]+@[^/]+/[a-zA-Z0-9_]+", re.IGNORECASE),
    re.compile(r"sqlite:///[^\s]+", re.IGNORECASE),
    re.compile(r"xyz_school_salt_[0-9]+", re.IGNORECASE),
    re.compile(r"[a-f0-9]{64}", re.IGNORECASE),
    re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", re.IGNORECASE),
]

def detect_prompt_injection(user_input: str) -> Tuple[bool, str]:
    """
    Inspect input text for adversarial prompt injection, jailbreak, or extraction attempts.
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
