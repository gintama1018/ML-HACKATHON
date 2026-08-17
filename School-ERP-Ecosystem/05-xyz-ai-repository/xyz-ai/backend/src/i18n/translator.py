from typing import Dict, Any, Optional
import re
from src.i18n.languages import SUPPORTED_LANGUAGES, get_language_metadata

LOCALIZED_PHRASES: Dict[str, Dict[str, str]] = {
    "en": {
        "greeting_student": "Hello {name}! I'm doing well, thank you for asking. How are you doing today? I can help you check your attendance, study tips, or connect with your teacher.",
        "greeting_parent": "Hello {name}. Welcome! How may I assist you today with your child's school attendance or activities?",
        "greeting_teacher": "Hello {name}. Hope you are having a productive day! I am here to help you mark attendance or review class rosters.",
        "greeting_principal": "Good day {name}. I am ready to assist you with school analytics, executive reports, and administrative tasks.",
        "homework_help": "I'd be glad to help you with study strategies and understanding concepts for your homework! What topic or problem are you working on?",
        "attendance_student": "Here is your attendance breakdown, {name}: Your overall attendance is **{pct}%** across {tot} school days ({pres} days present, {abs_cnt} absences, {late} late arrivals). Keep up the great effort!",
        "attendance_parent": "Here is the attendance report for **{name}** (Class {class_name}-{section}):\n• Overall Attendance: **{pct}%**\n• Present: {pres} / {tot} days\n• Absences: {abs_cnt} days\n• Late: {late} days\nPlease let me know if you would like me to connect you with {name}'s class teacher.",
        "attendance_generic": "Attendance report for **{name}**: Overall attendance is **{pct}%** ({pres}/{tot} days present, {abs_cnt} absences).",
        "confirm_escalation": "Your escalation ticket (#{ticket_id}) has been **officially confirmed** and dispatched to the {target}. A school representative will contact you shortly.",
        "pending_escalation": "I have created an escalation ticket (#{ticket_id}) to contact the **{target}** regarding: *'{reason}'*.\n\nWould you like me to confirm and dispatch this request now?",
        "disambiguation_parent": "You have {count} registered children with XYZ School: {children}. Which child would you like me to look up?",
        "disambiguation_teacher": "Which student in Class {class_name}-{section} would you like to mark as {status}? Please provide the student's name or roll number (e.g. Aarav Sharma, Diya Patel).",
        "attendance_marked": "Attendance confirmed: Student **{name}** has been marked **{status}** for {date}.",
        "rate_limited": "You have sent too many requests in a short period. Please wait a moment before trying again.",
        "security_refusal": "Security Notice: Your message contains prohibited instruction overrides or system alteration commands. As XYZ AI Assistant, I operate strictly within designated school role boundaries."
    },
    "hi": {
        "greeting_student": "नमस्ते {name}! मैं बहुत अच्छा हूँ, पूछने के लिए धन्यवाद। आज आप कैसे हैं? मैं आपकी उपस्थिति, पढ़ाई के सुझावों या शिक्षक से संपर्क करने में मदद कर सकता हूँ।",
        "greeting_parent": "नमस्ते {name} जी। आपका स्वागत है! आज मैं आपके बच्चे की स्कूल उपस्थिति या गतिविधियों के संबंध में आपकी क्या सहायता कर सकता हूँ?",
        "greeting_teacher": "नमस्ते {name} जी। आशा है आपका दिन अच्छा बीत रहा है! मैं कक्षा की उपस्थिति दर्ज करने और रजिस्टर की समीक्षा करने में आपकी मदद के लिए तैयार हूँ।",
        "greeting_principal": "सादर प्रणाम {name} जी। मैं स्कूल उपस्थिति विश्लेषण, रिपोर्ट और प्रशासनिक कार्यों में आपकी सहायता के लिए तैयार हूँ।",
        "homework_help": "मुझे आपके गृहकार्य (homework) और विषयों को समझने में आपकी मदद करने में बहुत खुशी होगी! आप किस विषय या प्रश्न पर काम कर रहे हैं?",
        "attendance_student": "{name}, यह रहा आपकी उपस्थिति का विवरण: कुल {tot} स्कूल दिनों में आपकी समग्र उपस्थिति **{pct}%** है ({pres} दिन उपस्थित, {abs_cnt} दिन अनुपस्थित, {late} दिन विलंब)। बहुत अच्छा प्रयास!",
        "attendance_parent": "**{name}** (कक्षा {class_name}-{section}) की उपस्थिति रिपोर्ट:\n• कुल उपस्थिति: **{pct}%**\n• उपस्थित: {pres} / {tot} दिन\n• अनुपस्थित: {abs_cnt} दिन\n• विलंब: {late} दिन\nयदि आप {name} के शिक्षक से बात करना चाहते हैं, तो कृपया मुझे बताएं।",
        "attendance_generic": "**{name}** की उपस्थिति रिपोर्ट: कुल {tot} दिनों में समग्र उपस्थिति **{pct}%** है ({pres} दिन उपस्थित, {abs_cnt} दिन अनुपस्थित)।",
        "confirm_escalation": "आपकी अनुरोध टिकट (#{ticket_id}) की आधिकारिक पुष्टि हो गई है और इसे {target} को भेज दिया गया है। जल्द ही स्कूल प्रतिनिधि आपसे संपर्क करेंगे।",
        "pending_escalation": "मैंने **{target}** से संपर्क करने के लिए एक अनुरोध टिकट (#{ticket_id}) तैयार किया है। विषय: *'{reason}'*।\n\nक्या आप चाहते हैं कि मैं अभी इस अनुरोध की पुष्टि करके इसे भेज दूँ?",
        "disambiguation_parent": "XYZ स्कूल में आपके {count} बच्चे पंजीकृत हैं: {children}। आप किस बच्चे का विवरण देखना चाहते हैं?",
        "disambiguation_teacher": "आप कक्षा {class_name}-{section} के किस छात्र को {status} के रूप में दर्ज करना चाहते हैं? कृपया छात्र का नाम या रोल नंबर बताएं (जैसे: आरव शर्मा, दिया पटेल)।",
        "attendance_marked": "उपस्थिति दर्ज की गई: छात्र **{name}** को {date} के लिए **{status}** दर्ज कर दिया गया है।",
        "rate_limited": "आपने कम समय में बहुत अधिक अनुरोध भेजे हैं। कृपया कुछ समय प्रतीक्षा करें।",
        "security_refusal": "सुरक्षा सूचना: आपके संदेश में अनधिकृत निर्देश या सिस्टम परिवर्तन आदेश शामिल हैं। XYZ AI सहायक के रूप में, मैं केवल निर्धारित स्कूल भूमिका सीमाओं में कार्य करता हूँ।"
    },
    "ta": {
        "greeting_student": "வணக்கம் {name}! நான் நலமாக இருக்கிறேன், கேட்டதற்கு நன்றி. இன்று உங்களுக்கு நான் எவ்வாறு உதவ முடியும்?",
        "greeting_parent": "வணக்கம் {name}. நல்வரவு! உங்கள் குழந்தையின் பள்ளி வருகை அல்லது தகவல்களில் நான் எவ்வாறு உதவலாம்?",
        "greeting_teacher": "வணக்கம் {name}. வருகை பதிவு செய்யவும் மாணவர் பட்டியலை சரிபார்க்கவும் நான் தயாராக உள்ளேன்.",
        "greeting_principal": "வணக்கம் {name} முதல்வர் அவர்களே. பள்ளி பகுப்பாய்வு மற்றும் அறிக்கைகளில் உதவ நான் தயாராக உள்ளேன்.",
        "homework_help": "உங்கள் வீட்டுப்பாடம் மற்றும் பாடங்களை புரிந்துகொள்ள உதவ நான் மகிழ்ச்சியடைகிறேன்! எந்த தலைப்பில் உதவி வேண்டும்?",
        "attendance_student": "{name}, உங்கள் வருகை விவரம்: மொத்தம் {tot} பள்ளி நாட்களில் உங்கள் வருகை **{pct}%** ({pres} நாட்கள் வருகை, {abs_cnt} நாட்கள் வரவில்லை).",
        "attendance_parent": "**{name}** (வகுப்பு {class_name}-{section}) வருகை அறிக்கை:\n• ஒட்டமொத்த வருகை: **{pct}%**\n• வருகை: {pres} / {tot} நாட்கள்\n• வரவில்லை: {abs_cnt} நாட்கள்",
        "attendance_generic": "**{name}** இன் வருகை அறிக்கை: மொத்தம் {tot} நாட்களில் ஒட்டுமொத்த வருகை **{pct}%**.",
        "confirm_escalation": "உங்கள் கோரிக்கை எண் (#{ticket_id}) உறுதிசெய்யப்பட்டு {target} அவர்களுக்கு அனுப்பப்பட்டது.",
        "pending_escalation": "**{target}** அவர்களை தொடர்பு கொள்ள கோரிக்கை (#{ticket_id}) உருவாக்கப்பட்டுள்ளது. காரணம்: *'{reason}'*.\n\nஇதை இப்போது உறுதிப்படுத்த விரும்புகிறீர்களா?",
        "disambiguation_parent": "உங்களுக்கு {count} குழந்தைகள் பதிவு செய்யப்பட்டுள்ளனர்: {children}. எந்த குழந்தையின் விவரங்களை பார்க்க விரும்புகிறீர்கள்?",
        "disambiguation_teacher": "வகுப்பு {class_name}-{section} இல் எந்த மாணவருக்கு வருகை பதிவு செய்ய வேண்டும்? பெயர் அல்லது ரோல் எண்ணை குறிப்பிடவும்.",
        "attendance_marked": "வருகை பதிவு செய்யப்பட்டது: மாணவர் **{name}** ({date}) **{status}** என குறிக்கப்பட்டார்.",
        "rate_limited": "குறைந்த நேரத்தில் அதிக கோரிக்கைகள் அனுப்பப்பட்டுள்ளன. சற்று பொறுத்திருக்கவும்.",
        "security_refusal": "பாதுகாப்பு அறிவிப்பு: உங்கள் செய்தி அனுமதிக்கப்படாத கட்டளைகளை கொண்டுள்ளது."
    },
    "bn": {
        "greeting_student": "নমস্কার {name}! আমি ভালো আছি, জিজ্ঞাসা করার জন্য ধন্যবাদ। আজ আপনি কেমন আছেন? আমি কীভাবে আপনাকে সাহায্য করতে পারি?",
        "greeting_parent": "নমস্কার {name}। স্বাগতম! আপনার সন্তানের স্কুলের উপস্থিতি বা তথ্যের ব্যাপারে আমি কীভাবে সাহায্য করতে পারি?",
        "greeting_teacher": "নমস্কার {name}। ক্লাসের উপস্থিতি রেকর্ড ও তালিকা পর্যালোচনায় সাহায্য করতে আমি প্রস্তুত।",
        "greeting_principal": "নমস্কার {name} মহাশয়া। স্কুলের অ্যানালিটিক্স ও প্রশাসনিক রিপোর্টে সাহায্য করতে আমি প্রস্তুত।",
        "homework_help": "আপনার হোমওয়ার্ক এবং পড়াশোনায় সাহায্য করতে আমি আনন্দিত! আপনি কোন বিষয়ের উপর কাজ করছেন?",
        "attendance_student": "{name}, আপনার উপস্থিতির বিবরণ: মোট {tot} দিনের মধ্যে সার্বিক উপস্থিতি **{pct}%** ({pres} দিন উপস্থিত, {abs_cnt} দিন অনুপস্থিত)।",
        "attendance_parent": "**{name}** (ক্লাস {class_name}-{section}) এর উপস্থিতির বিবরণ:\n• সার্বিক উপস্থিতি: **{pct}%**\n• উপস্থিত: {pres} / {tot} দিন\n• অনুপস্থিত: {abs_cnt} দিন",
        "attendance_generic": "**{name}** এর উপস্থিতির বিবরণ: মোট {tot} দিনের মধ্যে সার্বিক উপস্থিতি **{pct}%**।",
        "confirm_escalation": "আপনার অনুরোধ টিকিট (#{ticket_id}) নিশ্চিত করা হয়েছে এবং {target} কে পাঠানো হয়েছে।",
        "pending_escalation": "**{target}** এর সাথে যোগাযোগের জন্য একটি টিকিট (#{ticket_id}) তৈরি করা হয়েছে। কারণ: *'{reason}'*।\n\nআপনি কি এটি এখনই নিশ্চিত করতে চান?",
        "disambiguation_parent": "আপনার {count} জন সন্তান নিবন্ধিত রয়েছে: {children}। আপনি কার বিবরণ দেখতে চান?",
        "disambiguation_teacher": "ক্লাস {class_name}-{section} এর কোন छात्र/ছাত্রীর উপস্থিতি রেকর্ড করতে চান? নাম বা রোল নম্বর প্রদান করুন।",
        "attendance_marked": "উপস্থিতি নিশ্চিত করা হয়েছে: শিক্ষার্থী **{name}** কে {date} এর জন্য **{status}** হিসেবে চিহ্নিত করা হয়েছে।",
        "rate_limited": "আপনি খুব অল্প সময়ে অনেক অনুরোধ পাঠিয়েছেন। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।",
        "security_refusal": "নিরাপত্তা বিজ্ঞপ্তি: আপনার বার্তায় নিষিদ্ধ কমান্ড পাওয়া গেছে।"
    }
}

class MultilingualService:
    """Multilingual pipeline providing native localization for all responses."""
    
    @staticmethod
    def get_phrase(phrase_key: str, lang: str = "en", **kwargs) -> str:
        lang_code = lang if lang in LOCALIZED_PHRASES else "en"
        phrases = LOCALIZED_PHRASES.get(lang_code, LOCALIZED_PHRASES["en"])
        template = phrases.get(phrase_key, LOCALIZED_PHRASES["en"].get(phrase_key, ""))
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    @staticmethod
    def format_attendance_message(
        lang: str, student_name: str, percentage: float, total_days: int, present_days: int, absent_days: int
    ) -> str:
        """Format localized attendance report string (backward compatibility & direct unit testing)."""
        return MultilingualService.get_phrase(
            "attendance_generic",
            lang=lang,
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

    @staticmethod
    def detect_script_language(text: str) -> Optional[str]:
        """Detect language based on Unicode script ranges."""
        if not text:
            return None
        # Devanagari (Hindi, Marathi)
        if re.search(r'[\u0900-\u097F]', text):
            return "hi"
        # Tamil
        if re.search(r'[\u0B80-\u0BFF]', text):
            return "ta"
        # Bengali
        if re.search(r'[\u0980-\u09FF]', text):
            return "bn"
        # Telugu
        if re.search(r'[\u0C00-\u0C7F]', text):
            return "te"
        # Gujarati
        if re.search(r'[\u0A80-\u0AFF]', text):
            return "gu"
        # Kannada
        if re.search(r'[\u0C80-\u0CFF]', text):
            return "kn"
        # Malayalam
        if re.search(r'[\u0D00-\u0D7F]', text):
            return "ml"
        # Gurmukhi (Punjabi)
        if re.search(r'[\u0A00-\u0A7F]', text):
            return "pa"
        # Arabic/Persian/Urdu
        if re.search(r'[\u0600-\u06FF]', text):
            return "ur"
        return None

multilingual_service = MultilingualService()
