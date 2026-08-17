from typing import Dict, Any, Optional
from src.i18n.languages import SUPPORTED_LANGUAGES, get_language_metadata

LOCALIZED_TEMPLATES: Dict[str, Dict[str, str]] = {
    "en": {
        "attendance_report": "Here is the attendance report for **{name}**: Overall attendance is **{pct}%** across {tot} days ({pres} present, {abs_cnt} absences).",
        "confirm_escalation": "Your escalation ticket (#{ticket_id}) has been officially confirmed and sent to {target}.",
        "disambiguation_prompt": "You have {count} registered children. Which child would you like to review?"
    },
    "hi": {
        "attendance_report": "**{name}** की उपस्थिति रिपोर्ट: कुल {tot} दिनों में समग्र उपस्थिति **{pct}%** है ({pres} दिन उपस्थित, {abs_cnt} दिन अनुपस्थित)।",
        "confirm_escalation": "आपकी अनुरोध टिकट (#{ticket_id}) की पुष्टि हो गई है और इसे {target} को भेज दिया गया है।",
        "disambiguation_prompt": "आपके {count} बच्चे पंजीकृत हैं। आप किस बच्चे का विवरण देखना चाहते हैं?"
    },
    "ta": {
        "attendance_report": "**{name}** இன் வருகை அறிக்கை: மொத்தம் {tot} நாட்களில் ஒட்டுமொத்த வருகை **{pct}%** ({pres} நாட்கள் வருகை, {abs_cnt} நாட்கள் வரவில்லை).",
        "confirm_escalation": "உங்கள் கோரிக்கை எண் (#{ticket_id}) உறுதிசெய்யப்பட்டு {target} அவர்களுக்கு அனுப்பப்பட்டது.",
        "disambiguation_prompt": "உங்களுக்கு {count} குழந்தைகள் பதிவு செய்யப்பட்டுள்ளனர். எந்த குழந்தையின் விவரங்களை பார்க்க விரும்புகிறீர்கள்?"
    },
    "bn": {
        "attendance_report": "**{name}** এর উপস্থিতির বিবরণ: মোট {tot} দিনের মধ্যে সার্বিক উপস্থিতি **{pct}%** ({pres} দিন উপস্থিত, {abs_cnt} দিন অনুপস্থিত)।",
        "confirm_escalation": "আপনার অনুরোধ টিকিট (#{ticket_id}) সফলভাবে নিশ্চিত করা হয়েছে এবং {target} কে পাঠানো হয়েছে।",
        "disambiguation_prompt": "আপনার {count} জন সন্তান নিবন্ধিত রয়েছে। আপনি কার বিবরণ দেখতে চান?"
    }
}

class MultilingualService:
    """Multilingual pipeline supporting all 11 languages natively with deep localization for top 4."""
    
    @staticmethod
    def format_attendance_message(
        lang: str, student_name: str, percentage: float, total_days: int, present_days: int, absent_days: int
    ) -> str:
        lang_key = lang if lang in LOCALIZED_TEMPLATES else "en"
        tpl = LOCALIZED_TEMPLATES[lang_key]["attendance_report"]
        return tpl.format(
            name=student_name,
            pct=percentage,
            tot=total_days,
            pres=present_days,
            abs_cnt=absent_days
        )

    @staticmethod
    def get_greeting(lang: str) -> str:
        meta = get_language_metadata(lang)
        return meta.get("sample_greeting", SUPPORTED_LANGUAGES["en"]["sample_greeting"])

multilingual_service = MultilingualService()
