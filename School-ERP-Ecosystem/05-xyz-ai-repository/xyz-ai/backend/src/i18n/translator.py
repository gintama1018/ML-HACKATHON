from typing import Dict, Any, Optional
import re
from src.i18n.languages import SUPPORTED_LANGUAGES, get_language_metadata

# All-language phrase catalog. Every key present in en/hi/ta/bn must appear in all 11 languages.
LOCALIZED_PHRASES: Dict[str, Dict[str, str]] = {
    "en": {
        "greeting_student": "Hello {name}! I'm doing well, thank you for asking. How are you doing today? I can help you check your attendance, study tips, or connect with your teacher.",
        "greeting_parent": "Hello {name}. Welcome! How may I assist you today with your child's school attendance or activities?",
        "greeting_teacher": "Hello {name}. Hope you are having a productive day! I am here to help you mark attendance or review class rosters.",
        "greeting_principal": "Good day {name}. I am ready to assist you with school analytics, executive reports, and administrative tasks.",
        "homework_help": "I'd be glad to help you with study strategies and understanding concepts for your homework! What topic or problem are you working on?",
        "escalation_offer": "I'm sorry that wasn't helpful. Would you like me to connect you with your teacher, or with school management? Reply 'teacher' or 'management'.",
        "attendance_student": "{name}, here is your attendance breakdown: Your overall attendance is **{pct}%** across {tot} school days ({pres} days present, {abs_cnt} absences, {late} late arrivals). Keep up the great effort!",
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
        "escalation_offer": "मुझे खेद है कि यह सहायक नहीं रहा। क्या आप अपने शिक्षक से संपर्क करना चाहेंगे, या स्कूल प्रबंधन से? 'teacher' या 'management' टाइप करें।",
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
        "escalation_offer": "மன்னிக்கவும், அது உதவியாக இல்லை. உங்கள் ஆசிரியரிடம் இணைக்கட்டுமா, அல்லது பள்ளி நிர்வாகத்திடம்? 'teacher' அல்லது 'management' என்று பதிலளிக்கவும்.",
        "attendance_student": "{name}, உங்கள் வருகை விவரம்: மொத்தம் {tot} பள்ளி நாட்களில் உங்கள் வருகை **{pct}%** ({pres} நாட்கள் வருகை, {abs_cnt} நாட்கள் வரவில்லை, {late} நாட்கள் தாமதம்).",
        "attendance_parent": "**{name}** (வகுப்பு {class_name}-{section}) வருகை அறிக்கை:\n• ஒட்டமொத்த வருகை: **{pct}%**\n• வருகை: {pres} / {tot} நாட்கள்\n• வரவில்லை: {abs_cnt} நாட்கள்\n• தாமதம்: {late} நாட்கள்",
        "attendance_generic": "**{name}** இன் வருகை அறிக்கை: மொத்தம் {tot} நாட்களில் ஒட்டுமொத்த வருகை **{pct}%**.",
        "confirm_escalation": "உங்கள் கோரிக்கை எண் (#{ticket_id}) உறுதிசெய்யப்பட்டு {target} அவர்களுக்கு அனுப்பப்பட்டது.",
        "pending_escalation": "**{target}** அவர்களை தொடர்பு கொள்ள கோரிக்கை (#{ticket_id}) உருவாக்கப்பட்டுள்ளது. காரணம்: *'{reason}'*.\n\nஇதை இப்போது உறுதிப்படுத்த விரும்புகிறீர்களா?",
        "disambiguation_parent": "உங்களுக்கு {count} குழந்தைகள் பதிவு செய்யப்பட்டுள்ளனர்: {children}. எந்த குழந்தையின் விவரங்களை பார்க்க விரும்புகிறீர்கள்?",
        "disambiguation_teacher": "வகுப்பு {class_name}-{section} இல் எந்த மாணவருக்கு {status} என வருகை பதிவு செய்ய வேண்டும்? பெயர் அல்லது ரோல் எண்ணை குறிப்பிடவும்.",
        "attendance_marked": "வருகை பதிவு செய்யப்பட்டது: மாணவர் **{name}** ({date}) **{status}** என குறிக்கப்பட்டார்.",
        "rate_limited": "குறைந்த நேரத்தில் அதிக கோரிக்கைகள் அனுப்பப்பட்டுள்ளன. சற்று பொறுத்திருக்கவும்.",
        "security_refusal": "பாதுகாப்பு அறிவிப்பு: உங்கள் செய்தி அனுமதிக்கப்படாத கட்டளைகளை கொண்டுள்ளது."
    },
    "bn": {
        "greeting_student": "নমস্কার {name}! আমি ভালো আছি, জিজ্ঞাসা করার জন্য ধন্যবাদ। আজ আপনি কেমন আছেন? আমি কীভাবে আপনাকে সাহায্য করতে পারি?",
        "greeting_parent": "নমস্কার {name}। স্বাগতম! আপনার সন্তানের স্কুলের উপস্থিতি বা তথ্যের ব্যাপারে আমি কীভাবে সাহায্য করতে পারি?",
        "greeting_teacher": "নমস্কার {name}। ক্লাসের উপস্থিতি রেকর্ড ও তালিকা পর্যালোচনায় সাহায্য করতে আমি প্রস্তুত।",
        "greeting_principal": "নমস্কার {name} মহাশয়া। স্কুলের অ্যানালিটিক্স ও প্রশাসনিক রিপোর্টে সাহায্য করতে আমি প্রস্তুত।",
        "homework_help": "আপনার হোমওয়ার্ক এবং পড়াশোনায় সাহায্য করতে আমি আনন্দিত! আপনি কোন বিষয়ের উপর কাজ করছেন?",
        "escalation_offer": "দুঃখিত, এটা সহায়ক ছিল না। আপনি কি আপনার শিক্ষকের সাথে যোগাযোগ করতে চান, নাকি স্কুল ম্যানেজমেন্টের সাথে? 'teacher' বা 'management' লিখুন।",
        "attendance_student": "{name}, আপনার উপস্থিতির বিবরণ: মোট {tot} দিনের মধ্যে সার্বিক উপস্থিতি **{pct}%** ({pres} দিন উপস্থিত, {abs_cnt} দিন অনুপস্থিত, {late} দিন বিলম্ব)।",
        "attendance_parent": "**{name}** (ক্লাস {class_name}-{section}) এর উপস্থিতির বিবরণ:\n• সার্বিক উপস্থিতি: **{pct}%**\n• উপস্থিত: {pres} / {tot} দিন\n• অনুপস্থিত: {abs_cnt} দিন\n• বিলম্ব: {late} দিন",
        "attendance_generic": "**{name}** এর উপস্থিতির বিবরণ: মোট {tot} দিনের মধ্যে সার্বিক উপস্থিতি **{pct}%**।",
        "confirm_escalation": "আপনার অনুরোধ টিকিট (#{ticket_id}) নিশ্চিত করা হয়েছে এবং {target} কে পাঠানো হয়েছে।",
        "pending_escalation": "**{target}** এর সাথে যোগাযোগের জন্য একটি টিকিট (#{ticket_id}) তৈরি করা হয়েছে। কারণ: *'{reason}'*।\n\nআপনি কি এটি এখনই নিশ্চিত করতে চান?",
        "disambiguation_parent": "আপনার {count} জন সন্তান নিবন্ধিত রয়েছে: {children}। আপনি কার বিবরণ দেখতে চান?",
        "disambiguation_teacher": "ক্লাস {class_name}-{section} এর কোন ছাত্র/ছাত্রীকে {status} হিসেবে চিহ্নিত করতে চান? নাম বা রোল নম্বর প্রদান করুন।",
        "attendance_marked": "উপস্থিতি নিশ্চিত করা হয়েছে: শিক্ষার্থী **{name}** কে {date} এর জন্য **{status}** হিসেবে চিহ্নিত করা হয়েছে।",
        "rate_limited": "আপনি খুব অল্প সময়ে অনেক অনুরোধ পাঠিয়েছেন। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।",
        "security_refusal": "নিরাপত্তা বিজ্ঞপ্তি: আপনার বার্তায় নিষিদ্ধ কমান্ড পাওয়া গেছে।"
    },
    "te": {
        "greeting_student": "నమస్కారం {name}! నేను బాగున్నాను, అడిగినందుకు ధన్యవాదాలు. మీకు హాజరు, చదువు చిట్కాలు లేదా ఉపాధ్యాయులతో అనుసంధానంలో సహాయం చేయగలను.",
        "greeting_parent": "నమస్కారం {name} గారు. స్వాగతం! మీ పిల్లల పాఠశాల హాజరు లేదా కార్యకలాపాల గురించి ఈరోజు నేను మీకు ఎలా సహాయపడగలను?",
        "greeting_teacher": "నమస్కారం {name} గారు. హాజరు నమోదు చేయడం మరియు తరగతి జాబితాలు సమీక్షించడంలో సహాయం చేయడానికి నేను సిద్ధంగా ఉన్నాను.",
        "greeting_principal": "శుభోదయం {name} గారు. పాఠశాల విశ్లేషణలు మరియు నివేదికలలో సహాయం చేయడానికి నేను సిద్ధంగా ఉన్నాను.",
        "homework_help": "మీ గృహపాఠంలో మరియు భావాలను అర్థం చేసుకోవడంలో సహాయం చేయడానికి నేను సంతోషంగా ఉంటాను! మీరు ఏ విషయంపై పని చేస్తున్నారు?",
        "escalation_offer": "అది సహాయకరంగా లేదని నాకు చాలా విచారంగా ఉంది. మీ ఉపాధ్యాయులతో కనెక్ట్ చేయాలా, లేదా పాఠశాల నిర్వహణతో? 'teacher' లేదా 'management' అని జవాబివ్వండి.",
        "attendance_student": "{name}, మీ హాజరు వివరాలు: {tot} పాఠశాల రోజులలో మొత్తం హాజరు **{pct}%** ({pres} రోజులు హాజరు, {abs_cnt} రోజులు గైర్హాజరు, {late} రోజులు ఆలస్యం).",
        "attendance_parent": "**{name}** (తరగతి {class_name}-{section}) హాజరు నివేదిక:\n• మొత్తం హాజరు: **{pct}%**\n• హాజరు: {pres} / {tot} రోజులు\n• గైర్హాజరు: {abs_cnt} రోజులు\n• ఆలస్యం: {late} రోజులు",
        "attendance_generic": "**{name}** హాజరు నివేదిక: {tot} రోజులలో మొత్తం హాజరు **{pct}%**.",
        "confirm_escalation": "మీ ఎస్కలేషన్ టికెట్ (#{ticket_id}) అధికారికంగా నిర్ధారించబడి {target} కు పంపబడింది.",
        "pending_escalation": "**{target}** ను సంప్రదించడానికి అభ్యర్థన టికెట్ (#{ticket_id}) సృష్టించబడింది. విషయం: *'{reason}'*.\n\nమీరు ఇప్పుడు ఈ అభ్యర్థనను నిర్ధారించాలనుకుంటున్నారా?",
        "disambiguation_parent": "XYZ పాఠశాలలో మీకు {count} మంది పిల్లలు నమోదు చేయబడ్డారు: {children}. ఏ పిల్లల వివరాలు చూడాలనుకుంటున్నారు?",
        "disambiguation_teacher": "తరగతి {class_name}-{section} లో ఏ విద్యార్థిని {status} గా నమోదు చేయాలనుకుంటున్నారు? విద్యార్థి పేరు లేదా రోల్ నంబర్ ఇవ్వండి.",
        "attendance_marked": "హాజరు నిర్ధారించబడింది: విద్యార్థి **{name}** ను {date} కి **{status}** గా నమోదు చేయబడింది.",
        "rate_limited": "మీరు చాలా తక్కువ సమయంలో చాలా అభ్యర్థనలు పంపారు. దయచేసి కొంత సేపు వేచి ఉండండి.",
        "security_refusal": "భద్రతా నోటీసు: మీ సందేశంలో నిషేధిత ఆదేశాలు ఉన్నాయి."
    },
    "mr": {
        "greeting_student": "नमस्कार {name}! मी ठीक आहे, विचारल्याबद्दल धन्यवाद. मी तुमची उपस्थिती, अभ्यासाच्या टिप्स किंवा शिक्षकांशी संपर्क करण्यात मदत करू शकतो.",
        "greeting_parent": "नमस्कार {name}. स्वागत आहे! आज मी तुमच्या मुलाची शाळेतील उपस्थिती किंवा क्रियाकलापांबाबत कशी मदत करू?",
        "greeting_teacher": "नमस्कार {name}. उपस्थिती नोंदवणे आणि वर्गाची यादी तपासण्यात मदत करण्यासाठी मी तयार आहे.",
        "greeting_principal": "शुभ दिवस {name}. शाळेचे विश्लेषण आणि अहवालांमध्ये मदत करण्यासाठी मी तयार आहे.",
        "homework_help": "तुमच्या गृहपाठात आणि संकल्पना समजून घेण्यात मदत करण्यास मला आनंद होईल! तुम्ही कोणत्या विषयावर काम करत आहात?",
        "escalation_offer": "मला माफ करा ते उपयुक्त नव्हते. तुम्हाला तुमच्या शिक्षकांशी किंवा शाळा व्यवस्थापनाशी जोडायचे आहे का? 'teacher' किंवा 'management' उत्तर द्या.",
        "attendance_student": "{name}, तुमची उपस्थितीची माहिती: {tot} शाळेच्या दिवसांमध्ये एकूण उपस्थिती **{pct}%** ({pres} दिवस उपस्थित, {abs_cnt} दिवस अनुपस्थित, {late} दिवस उशीर).",
        "attendance_parent": "**{name}** (वर्ग {class_name}-{section}) उपस्थिती अहवाल:\n• एकूण उपस्थिती: **{pct}%**\n• उपस्थित: {pres} / {tot} दिवस\n• अनुपस्थित: {abs_cnt} दिवस\n• उशीर: {late} दिवस",
        "attendance_generic": "**{name}** उपस्थिती अहवाल: {tot} दिवसांमध्ये एकूण उपस्थिती **{pct}%**.",
        "confirm_escalation": "तुमची तक्रार तिकीट (#{ticket_id}) अधिकृतपणे पुष्टी केली गेली आहे आणि {target} ला पाठवली गेली आहे.",
        "pending_escalation": "**{target}** शी संपर्क साधण्यासाठी विनंती तिकीट (#{ticket_id}) तयार केली आहे. कारण: *'{reason}'*.\n\nतुम्हाला ही विनंती आत्ता पाठवायची आहे का?",
        "disambiguation_parent": "XYZ शाळेत तुमची {count} मुले नोंदणीकृत आहेत: {children}. तुम्हाला कोणाची माहिती पाहायची आहे?",
        "disambiguation_teacher": "वर्ग {class_name}-{section} मधील कोणत्या विद्यार्थ्याला {status} म्हणून नोंदवायचे आहे? कृपया विद्यार्थ्याचे नाव किंवा रोल नंबर द्या.",
        "attendance_marked": "उपस्थिती नोंदवली: विद्यार्थी **{name}** ला {date} साठी **{status}** म्हणून नोंदवले आहे.",
        "rate_limited": "तुम्ही थोड्या वेळात खूप जास्त विनंत्या पाठवल्या आहेत. कृपया थोडा वेळ थांबा.",
        "security_refusal": "सुरक्षा सूचना: तुमच्या संदेशात अनधिकृत आदेश आहेत."
    },
    "gu": {
        "greeting_student": "નમસ્તે {name}! હું ઠીક છું, પૂછ્યા બદલ ધન્યવાદ. આજે હું તમારી હાજરી, અભ્યાસ ટિપ્સ અથવા શિક્ષક સાથે જોડાવામાં મદદ કરી શકું છું.",
        "greeting_parent": "નમસ્તે {name}. સ્વાગત છે! આજે હું તમારા બાળકની શાળાની હાજરી અથવા પ્રવૃત્તિઓ વિશે કેવી રીતે મદદ કરી શકું?",
        "greeting_teacher": "નમસ્તે {name}. હાજરી નોંધવા અને વર્ગ સૂચિ સમીક્ષા કરવામાં સહાય કરવા હું તૈયાર છું.",
        "greeting_principal": "શુભ દિવસ {name}. શાળાના વિશ્લેષણ અને અહેવાલોમાં સહાય કરવા હું તૈયાર છું.",
        "homework_help": "ગૃહકાર્ય અને વિભાવનાઓ સમજવામાં સહાય કરવા હું ખુશ છું! તમે કયા વિષય પર કામ કરી રહ્યા છો?",
        "escalation_offer": "મને ખેદ છે કે તે ઉપયોગી ન હતું. શું તમે તમારા શિક્ષક સાથે અથવા શાળા વ્યવસ્થાપન સાથે જોડાવા ઇચ્છો? 'teacher' અથવા 'management' જવાબ આપો.",
        "attendance_student": "{name}, તમારી હાજરીની વિગત: {tot} શાળાના દિવસોમાં કુલ હાજરી **{pct}%** ({pres} દિવસ હાજર, {abs_cnt} દિવસ ગેરહાજર, {late} દિવસ મોડું).",
        "attendance_parent": "**{name}** (વર્ગ {class_name}-{section}) હાજરી અહેવાલ:\n• કુલ હાજરી: **{pct}%**\n• હાજર: {pres} / {tot} દિવસ\n• ગેરહાજર: {abs_cnt} દિવસ\n• મોડું: {late} દિવસ",
        "attendance_generic": "**{name}** હાજરી અહેવાલ: {tot} દિવસોમાં કુલ હાજરી **{pct}%**.",
        "confirm_escalation": "તમારી વિનંતી ટિકિટ (#{ticket_id}) ત્ $(target}ने মোকলা ची Confirmed {target} ને sent.",
        "pending_escalation": "**{target}** ने संपर्क करण्यासाठी विनंती टिकिट (#{ticket_id}) बनावl है. कारण: *'{reason}'*.\n\nशुं तम आ विनंती अत्यारे मोकलाय छो?",
        "disambiguation_parent": "XYZ शाले मां तमारा {count} बाल नोंधायेला छे: {children}. तमने कोनी माहिती जोवी छे?",
        "disambiguation_teacher": "वर्ग {class_name}-{section} मां कयो विद्यार्थी {status} तरीके नोंधवो छे? कृपया नाम या रोल नंबर आपो.",
        "attendance_marked": "हाजरी नोंधवाई: विद्यार्थी **{name}** ने {date} माटे **{status}** तरीके नोंधवाया छे.",
        "rate_limited": "तमे थोडा समय मां घणी वधारे विनंतियो मोकली छे. कृपया थोडी राह जुओ.",
        "security_refusal": "सुरक्षा सूचना: तमारा संदेश मां अनाधिकृत आदेशो छे."
    },
    "kn": {
        "greeting_student": "ನಮಸ್ಕಾರ {name}! ನಾನು ಚೆನ್ನಾಗಿದ್ದೇನೆ, ಕೇಳಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದ. ಇಂದು ನಿಮ್ಮ ಹಾಜರಾತಿ, ಅಧ್ಯಯನ ಸಲಹೆ ಅಥವಾ ಶಿಕ್ಷಕರ ಸಂಪರ್ಕದಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.",
        "greeting_parent": "ನಮಸ್ಕಾರ {name}. ಸ್ವಾಗತ! ಇಂದು ನಿಮ್ಮ ಮಗುವಿನ ಶಾಲೆಯ ಹಾಜರಾತಿ ಅಥವಾ ಚಟುವಟಿಕೆಗಳ ಬಗ್ಗೆ ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "greeting_teacher": "ನಮಸ್ಕಾರ {name}. ಹಾಜರಾತಿ ದಾಖಲಿಸಲು ಮತ್ತು ತರಗತಿ ಪಟ್ಟಿ ಪರಿಶೀಲಿಸಲು ನಾನು ಸಿದ್ಧವಾಗಿದ್ದೇನೆ.",
        "greeting_principal": "ಶುಭ ದಿನ {name}. ಶಾಲಾ ವಿಶ್ಲೇಷಣ ಮತ್ತು ವರದಿಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಲು ನಾನು ಸಿದ್ಧ.",
        "homework_help": "ನಿಮ್ಮ ಗೃಹಕಾರ್ಯ ಮತ್ತು ಪರಿಕಲ್ಪನೆಗಳನ್ನು ಅರ್ಥ ಮಾಡಿಕೊಳ್ಳಲು ಸಹಾಯ ಮಾಡಲು ನನಗೆ ಸಂತೋಷ! ನೀವು ಯಾವ ವಿಷಯದ ಮೇಲೆ ಕೆಲಸ ಮಾಡುತ್ತಿದ್ದೀರಾ?",
        "escalation_offer": "ಅದು ಸಹಾಯಕಾರಿಯಾಗಲಿಲ್ಲ ಎಂದು ವಿಷಾದ. ನಿಮ್ಮ ಶಿಕ್ಷಕರೊಂದಿಗೆ ಸಂಪರ್ಕಿಸಲೇ ಅಥವಾ ಶಾಲಾ ನಿರ್ವಹಣೆಯೊಂದಿಗೆ? 'teacher' ಅಥವಾ 'management' ಎಂದು ಉತ್ತರಿಸಿ.",
        "attendance_student": "{name}, ನಿಮ್ಮ ಹಾಜರಾತಿ ವಿವರ: {tot} ಶಾಲಾ ದಿನಗಳಲ್ಲಿ ಒಟ್ಟು ಹಾಜರಾತಿ **{pct}%** ({pres} ದಿನ ಹಾಜರು, {abs_cnt} ದಿನ ಗೈರು, {late} ದಿನ ತಡ).",
        "attendance_parent": "**{name}** (ತರಗತಿ {class_name}-{section}) ಹಾಜರಾತಿ ವರದಿ:\n• ಒಟ್ಟು ಹಾಜರಾತಿ: **{pct}%**\n• ಹಾಜರು: {pres} / {tot} ದಿನಗಳು\n• ಗೈರು: {abs_cnt} ದಿನಗಳು\n• ತಡ: {late} ದಿನಗಳು",
        "attendance_generic": "**{name}** ಹಾಜರಾತಿ ವರದಿ: {tot} ದಿನಗಳಲ್ಲಿ ಒಟ್ಟು ಹಾಜರಾತಿ **{pct}%**.",
        "confirm_escalation": "ನಿಮ್ಮ ದೂರು ಟಿಕೆಟ್ (#{ticket_id}) ಅಧಿಕೃತವಾಗಿ ದೃಢೀಕರಿಸಲ್ಪಟ್ಟಿದ್ದು {target} ಗೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
        "pending_escalation": "**{target}** ಗೆ ಸಂಪರ್ಕಿಸಲು ವಿನಂತಿ ಟಿಕೆಟ್ (#{ticket_id}) ರಚಿಸಲಾಗಿದೆ. ಕಾರಣ: *'{reason}'*.\n\nನೀವು ಈಗ ಈ ವಿನಂತಿಯನ್ನು ದೃಢೀಕರಿಸಲು ಬಯಸುವಿರಾ?",
        "disambiguation_parent": "XYZ ಶಾಲೆಯಲ್ಲಿ ನಿಮ್ಮ {count} ಮಕ್ಕಳು ನೋಂದಾಯಿಸಲ್ಪಟ್ಟಿದ್ದಾರೆ: {children}. ನೀವು ಯಾರ ಮಾಹಿತಿ ನೋಡಲು ಬಯಸುವಿರಿ?",
        "disambiguation_teacher": "ತರಗತಿ {class_name}-{section} ರಲ್ಲಿ ಯಾವ ವಿದ್ಯಾರ್ಥಿಯನ್ನು {status} ಎಂದು ದಾಖಲಿಸಬೇಕು? ದಯವಿಟ್ಟು ಹೆಸರು ಅಥವಾ ರೋಲ್ ನಂಬರ್ ನೀಡಿ.",
        "attendance_marked": "ಹಾಜರಾತಿ ದಾಖಲಾಯಿತು: ವಿದ್ಯಾರ್ಥಿ **{name}** ಅನ್ನು {date} ಗಾಗಿ **{status}** ಎಂದು ದಾಖಲಿಸಲಾಗಿದೆ.",
        "rate_limited": "ನೀವು ಕಡಿಮೆ ಸಮಯದಲ್ಲಿ ತುಂಬಾ ಹೆಚ್ಚು ವಿನಂತಿಗಳನ್ನು ಕಳುಹಿಸಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಕಾಯಿರಿ.",
        "security_refusal": "ಭದ್ರತಾ ಸೂಚನೆ: ನಿಮ್ಮ ಸಂದೇಶದಲ್ಲಿ ನಿಷೇಧಿತ ಆದೇಶಗಳಿವೆ."
    },
    "ml": {
        "greeting_student": "നമസ്കാരം {name}! ഞാൻ ഭേദമില്ല, ചോദിച്ചതിന് നന്ദി. ഇന്ന് ഹാജർ, പഠന നുറുങ്ങുകൾ അല്ലെങ്കിൽ ടീച്ചറുമായി ബന്ധിപ്പിക്കാൻ ഞാൻ സഹായിക്കാം.",
        "greeting_parent": "നമസ്കാരം {name}. സ്വാഗതം! ഇന്ന് നിങ്ങളുടെ കുട്ടിയുടെ സ്കൂൾ ഹാജർ അല്ലെങ്കിൽ പ്രവർത്തനങ്ങളെ കുറിച്ച് ഞാൻ എങ്ങനെ സഹായിക്കാം?",
        "greeting_teacher": "നമസ്കാരം {name}. ഹാജർ രേഖപ്പെടുത്തുന്നതിനും ക്ലാസ് ലിസ്റ്റ് അവലോകനം ചെയ്യുന്നതിനും ഞാൻ തയ്യാറാണ്.",
        "greeting_principal": "ശുഭ ദിനം {name}. സ്കൂൾ വിശകലനവും റിപ്പോർട്ടുകളും സഹായിക്കാൻ ഞാൻ തയ്യാറാണ്.",
        "homework_help": "നിങ്ങളുടെ ഹോംവർക്കും ആശയങ്ങൾ മനസ്സിലാക്കുന്നതിനും ഞാൻ സഹായിക്കാൻ സന്തോഷം! ഏത് വിഷയത്തിലാണ് നിങ്ങൾ പ്രവർത്തിക്കുന്നത്?",
        "escalation_offer": "അത് സഹായകരമല്ലായിരുന്നതിൽ ക്ഷമ ചോദിക്കുന്നു. നിങ്ങളുടെ ടീച്ചറോ അതോ സ്കൂൾ മാനേജ്മെന്റോ ആരുമായി ബന്ധിപ്പിക്കണം? 'teacher' അല്ലെങ്കിൽ 'management' ഉത്തരം നൽകൂ.",
        "attendance_student": "{name}, നിങ്ങളുടെ ഹാജർ വിവരങ്ങൾ: {tot} സ്കൂൾ ദിവസങ്ങളിൽ ആകെ ഹാജർ **{pct}%** ({pres} ദിവസം ഹാജർ, {abs_cnt} ദിവസം ഇല്ലായ്മ, {late} ദിവസം വൈകി).",
        "attendance_parent": "**{name}** (ക്ലാസ് {class_name}-{section}) ഹാജർ റിപ്പോർട്ട്:\n• ആകെ ഹാജർ: **{pct}%**\n• ഹാജർ: {pres} / {tot} ദിവസം\n• ഇല്ലായ്മ: {abs_cnt} ദിവസം\n• വൈകി: {late} ദിവസം",
        "attendance_generic": "**{name}** ഹാജർ റിപ്പോർട്ട്: {tot} ദിവസങ്ങളിൽ ആകെ ഹാജർ **{pct}%**.",
        "confirm_escalation": "നിങ്ങളുടെ പരാതി ടിക്കറ്റ് (#{ticket_id}) ഔദ്യോഗികമായി സ്ഥിരീകരിച്ച് {target} ക്ക് അയച്ചു.",
        "pending_escalation": "**{target}** ൽ ബന്ധപ്പെടാൻ അഭ്യർത്ഥന ടിക്കറ്റ് (#{ticket_id}) സൃഷ്ടിച്ചിട്ടുണ്ട്. കാരണം: *'{reason}'*.\n\nഈ അഭ്യർത്ഥന ഇപ്പോൾ സ്ഥിരീകരിക്കണമോ?",
        "disambiguation_parent": "XYZ സ്കൂളിൽ നിങ്ങളുടെ {count} കുട്ടികൾ ഉൾപ്പെടുത്തിയിട്ടുണ്ട്: {children}. ആരുടെ വിവരങ്ങൾ കാണണം?",
        "disambiguation_teacher": "ക്ലാസ് {class_name}-{section} ൽ ഏത് വിദ്യാർത്ഥിയെ {status} ആയി രേഖപ്പെടുത്തണം? ദയവായി പേര് അല്ലെങ്കിൽ റോൾ നമ്പർ നൽകൂ.",
        "attendance_marked": "ഹാജർ സ്ഥിരീകരിച്ചു: വിദ്യാർത്ഥി **{name}** ക്ക് {date} ന് **{status}** ആയി രേഖപ്പെടുത്തി.",
        "rate_limited": "നിങ്ങൾ കുറഞ്ഞ സമയത്തിൽ ധാരാളം അഭ്യർത്ഥനകൾ അയച്ചു. ദയവായി കുറച്ച് കാത്തിരിക്കൂ.",
        "security_refusal": "സുരക്ഷാ അറിയിപ്പ്: നിങ്ങളുടെ സന്ദേശത്തിൽ നിഷിദ്ധ നിർദ്ദേശങ്ങൾ ഉൾക്കൊള്ളുന്നു."
    },
    "pa": {
        "greeting_student": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}! ਮੈਂ ਠੀਕ ਹਾਂ, ਪੁੱਛਣ ਲਈ ਧੰਨਵਾਦ। ਮੈਂ ਤੁਹਾਡੀ ਹਾਜ਼ਰੀ, ਪੜ੍ਹਾਈ ਦੇ ਸੁਝਾਅ ਜਾਂ ਅਧਿਆਪਕ ਨਾਲ ਜੋੜਨ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ।",
        "greeting_parent": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਜੀ ਆਇਆਂ ਨੂੰ! ਅੱਜ ਮੈਂ ਤੁਹਾਡੇ ਬੱਚੇ ਦੀ ਸਕੂਲ ਹਾਜ਼ਰੀ ਜਾਂ ਗਤੀਵਿਧੀਆਂ ਬਾਰੇ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        "greeting_teacher": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {name}। ਹਾਜ਼ਰੀ ਦਰਜ਼ ਕਰਨ ਅਤੇ ਕਲਾਸ ਸੂਚੀ ਜਾਂਚਣ ਵਿੱਚ ਮਦਦ ਕਰਨ ਲਈ ਮੈਂ ਤਿਆਰ ਹਾਂ।",
        "greeting_principal": "ਸ਼ੁਭ ਦਿਨ {name}। ਸਕੂਲ ਵਿਸ਼ਲੇਸ਼ਣ ਅਤੇ ਰਿਪੋਰਟਾਂ ਵਿੱਚ ਮਦਦ ਕਰਨ ਲਈ ਮੈਂ ਤਿਆਰ ਹਾਂ।",
        "homework_help": "ਤੁਹਾਡੇ ਘਰੇਲੂ ਕੰਮ ਅਤੇ ਧਾਰਨਾਵਾਂ ਸਮਝਣ ਵਿੱਚ ਮਦਦ ਕਰਕੇ ਮੈਨੂੰ ਖੁਸ਼ੀ ਹੋਵੇਗੀ! ਤੁਸੀਂ ਕਿਸ ਵਿਸ਼ੇ 'ਤੇ ਕੰਮ ਕਰ ਰਹੇ ਹੋ?",
        "escalation_offer": "ਮਾਫ਼ ਕਰਨਾ ਕਿ ਇਹ ਮਦਦਗਾਰ ਨਹੀਂ ਸੀ। ਕੀ ਤੁਸੀਂ ਆਪਣੇ ਅਧਿਆਪਕ ਨਾਲ ਜਾਂ ਸਕੂਲ ਪ੍ਰਬੰਧਨ ਨਾਲ ਜੁੜਨਾ ਚਾਹੋਗੇ? 'teacher' ਜਾਂ 'management' ਦਾ ਜਵਾਬ ਦਿਓ।",
        "attendance_student": "{name}, ਤੁਹਾਡੀ ਹਾਜ਼ਰੀ ਦਾ ਵੇਰਵਾ: {tot} ਸਕੂਲ ਦਿਨਾਂ ਵਿੱਚ ਕੁੱਲ ਹਾਜ਼ਰੀ **{pct}%** ({pres} ਦਿਨ ਹਾਜ਼ਰ, {abs_cnt} ਦਿਨ ਗੈਰਹਾਜ਼ਰ, {late} ਦਿਨ ਦੇਰੀ).",
        "attendance_parent": "**{name}** (ਕਲਾਸ {class_name}-{section}) ਹਾਜ਼ਰੀ ਰਿਪੋਰਟ:\n• ਕੁੱਲ ਹਾਜ਼ਰੀ: **{pct}%**\n• ਹਾਜ਼ਰ: {pres} / {tot} ਦਿਨ\n• ਗੈਰਹਾਜ਼ਰ: {abs_cnt} ਦਿਨ\n• ਦੇਰੀ: {late} ਦਿਨ",
        "attendance_generic": "**{name}** ਹਾਜ਼ਰੀ ਰਿਪੋਰਟ: {tot} ਦਿਨਾਂ ਵਿੱਚ ਕੁੱਲ ਹਾਜ਼ਰੀ **{pct}%**.",
        "confirm_escalation": "ਤੁਹਾਡੀ ਸ਼ਿਕਾਇਤ ਟਿਕਟ (#{ticket_id}) ਅਧਿਕਾਰਤ ਤੌਰ 'ਤੇ ਪੁਸ਼ਟੀ ਕੀਤੀ ਗਈ ਹੈ ਅਤੇ {target} ਨੂੰ ਭੇਜੀ ਗਈ ਹੈ।",
        "pending_escalation": "**{target}** ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਬੇਨਤੀ ਟਿਕਟ (#{ticket_id}) ਬਣਾਈ ਗਈ ਹੈ। ਕਾਰਨ: *'{reason}'*.\n\nਕੀ ਤੁਸੀਂ ਇਸ ਬੇਨਤੀ ਨੂੰ ਹੁਣੇ ਭੇਜਣਾ ਚਾਹੁੰਦੇ ਹੋ?",
        "disambiguation_parent": "XYZ ਸਕੂਲ ਵਿੱਚ ਤੁਹਾਡੇ {count} ਬੱਚੇ ਦਾਖਲ ਹਨ: {children}. ਤੁਸੀਂ ਕਿਸ ਦੀ ਜਾਣਕਾਰੀ ਦੇਖਣੀ ਚਾਹੁੰਦੇ ਹੋ?",
        "disambiguation_teacher": "ਕਲਾਸ {class_name}-{section} ਵਿੱਚ ਕਿਹੜੇ ਵਿਦਿਆਰਥੀ ਨੂੰ {status} ਵਜੋਂ ਦਰਜ਼ ਕਰਨਾ ਹੈ? ਕਿਰਪਾ ਕਰਕੇ ਨਾਮ ਜਾਂ ਰੋਲ ਨੰਬਰ ਦਿਓ।",
        "attendance_marked": "ਹਾਜ਼ਰੀ ਦਰਜ਼ ਕੀਤੀ: ਵਿਦਿਆਰਥੀ **{name}** ਨੂੰ {date} ਲਈ **{status}** ਵਜੋਂ ਦਰਜ਼ ਕੀਤਾ ਗਿਆ ਹੈ।",
        "rate_limited": "ਤੁਸੀਂ ਥੋੜੇ ਸਮੇਂ ਵਿੱਚ ਬਹੁਤ ਜ਼ਿਆਦਾ ਬੇਨਤੀਆਂ ਭੇਜੀਆਂ ਹਨ। ਕਿਰਪਾ ਕਰਕੇ ਕੁਝ ਦੇਰ ਉਡੀਕ ਕਰੋ।",
        "security_refusal": "ਸੁਰੱਖਿਆ ਸੂਚਨਾ: ਤੁਹਾਡੇ ਸੁਨੇਹੇ ਵਿੱਚ ਵਰਜਿਤ ਹੁਕਮ ਹਨ।"
    },
    "ur": {
        "greeting_student": "السلام علیکم {name}! میں ٹھیک ہوں، پوچھنے کا شکریہ۔ میں آپ کی حاضری، تعلیمی مشورے یا استاد سے رابطے میں مدد کر سکتا ہوں۔",
        "greeting_parent": "السلام علیکم {name} صاحب۔ خوش آمدید! آج میں آپ کے بچے کی اسکول حاضری یا سرگرمیوں کے بارے میں کیسے مدد کر سکتا ہوں؟",
        "greeting_teacher": "السلام علیکم {name} صاحب۔ حاضری درج کرنے اور کلاس فہرست جانچنے میں مدد کے لیے میں تیار ہوں۔",
        "greeting_principal": "خیر مقدم {name} صاحب۔ اسکول تجزیات اور رپورٹس میں مدد کے لیے میں تیار ہوں۔",
        "homework_help": "آپ کے گھریلو کام اور تصورات سمجھنے میں مدد کرکے مجھے خوشی ہوگی! آپ کس موضوع پر کام کر رہے ہیں؟",
        "escalation_offer": "معذرت کہ یہ مددگار نہیں تھا۔ کیا آپ اپنے استاد سے یا اسکول انتظامیہ سے رابطہ کرنا چاہتے ہیں؟ 'teacher' یا 'management' لکھیں۔",
        "attendance_student": "{name}، آپ کی حاضری کی تفصیل: {tot} اسکول کے دنوں میں کل حاضری **{pct}%** ({pres} دن حاضر، {abs_cnt} دن غیر حاضر، {late} دن دیر).",
        "attendance_parent": "**{name}** (کلاس {class_name}-{section}) حاضری رپورٹ:\n• کل حاضری: **{pct}%**\n• حاضر: {pres} / {tot} دن\n• غیر حاضر: {abs_cnt} دن\n• دیر: {late} دن",
        "attendance_generic": "**{name}** حاضری رپورٹ: {tot} دنوں میں کل حاضری **{pct}%**.",
        "confirm_escalation": "آپ کی شکایت ٹکٹ (#{ticket_id}) باضابطہ تصدیق ہو گئی اور {target} کو بھیج دی گئی۔",
        "pending_escalation": "**{target}** سے رابطے کے لیے درخواست ٹکٹ (#{ticket_id}) بنائی گئی ہے۔ موضوع: *'{reason}'*.\n\nکیا آپ یہ درخواست ابھی بھیجنا چاہتے ہیں؟",
        "disambiguation_parent": "XYZ اسکول میں آپ کے {count} بچے درج ہیں: {children}. آپ کس کی معلومات دیکھنا چاہتے ہیں؟",
        "disambiguation_teacher": "کلاس {class_name}-{section} میں کس طالب علم کو {status} کے طور پر درج کرنا ہے؟ براہ کرم نام یا رول نمبر دیں۔",
        "attendance_marked": "حاضری درج: طالب علم **{name}** کو {date} کے لیے **{status}** کے طور پر درج کر دیا گیا۔",
        "rate_limited": "آپ نے تھوڑے وقت میں بہت زیادہ درخواستیں بھیجی ہیں۔ براہ کرم تھوڑا انتظار کریں۔",
        "security_refusal": "سیکیورٹی نوٹس: آپ کے پیغام میں ممنوعہ احکامات ہیں۔"
    }
}


class MultilingualService:
    """Multilingual pipeline providing native localization for all responses across 11 Indian languages."""

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
