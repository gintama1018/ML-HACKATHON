from typing import Dict, Any, List

SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "script": "Latin",
        "sample_greeting": "Hello! How can I assist you with school information today?",
        "deep_tested": True
    },
    "hi": {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिंदी",
        "script": "Devanagari",
        "sample_greeting": "नमस्ते! आज मैं विद्यालय की जानकारी के साथ आपकी क्या सहायता कर सकता हूँ?",
        "deep_tested": True
    },
    "ta": {
        "code": "ta",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "script": "Tamil",
        "sample_greeting": "வணக்கம்! பள்ளி தகவல்களுடன் இன்று உங்களுக்கு எவ்வாறு உதவ முடியும்?",
        "deep_tested": True
    },
    "bn": {
        "code": "bn",
        "name": "Bengali",
        "native_name": "বাংলা",
        "script": "Bengali",
        "sample_greeting": "নমস্কার! স্কুল সম্পর্কিত তথ্যের জন্য আমি আজ আপনাকে কীভাবে সাহায্য করতে পারি?",
        "deep_tested": True
    },
    "te": {
        "code": "te",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "script": "Telugu",
        "sample_greeting": "నమస్కారం! పాఠశాల సమాచారంతో ఈరోజు నేను మీకు ఎలా సహాయపడగలను?",
        "deep_tested": False
    },
    "mr": {
        "code": "mr",
        "name": "Marathi",
        "native_name": "मराठी",
        "script": "Devanagari",
        "sample_greeting": "नमस्कार! आज मी शाळेच्या माहितीबाबत आपल्याला कशी मदत करू शकतो?",
        "deep_tested": False
    },
    "gu": {
        "code": "gu",
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "script": "Gujarati",
        "sample_greeting": "નમસ્તે! આજે હું શાળાની માહિતી સાથે તમને કેવી રીતે મદદ કરી શકું?",
        "deep_tested": False
    },
    "kn": {
        "code": "kn",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "script": "Kannada",
        "sample_greeting": "ನಮಸ್ಕಾರ! ಶಾಲೆಯ ಮಾಹಿತಿಯೊಂದಿಗೆ ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "deep_tested": False
    },
    "ml": {
        "code": "ml",
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "script": "Malayalam",
        "sample_greeting": "നമസ്കാരം! സ്കൂൾ വിവരങ്ങളുമായി ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കും?",
        "deep_tested": False
    },
    "pa": {
        "code": "pa",
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "script": "Gurmukhi",
        "sample_greeting": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਸਕੂਲ ਦੀ ਜਾਣਕਾਰੀ ਲਈ ਮੈਂ ਅੱਜ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        "deep_tested": False
    },
    "ur": {
        "code": "ur",
        "name": "Urdu",
        "native_name": "اردو",
        "script": "Arabic-Persian",
        "sample_greeting": "السلام علیکم! میں اسکول کی معلومات کے سلسلے میں آپ کی کیا مدد کر سکتا ہوں؟",
        "deep_tested": False
    }
}

def get_language_metadata(lang_code: str) -> Dict[str, Any]:
    return SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES["en"])

def list_supported_languages() -> List[Dict[str, Any]]:
    return list(SUPPORTED_LANGUAGES.values())
