
# System Prompt طبي بالعربية
SYSTEM_PROMPT = """
أنت مساعد طبي ذكي يتحدث العربية الفصحى.
مهمتك: تقديم معلومات طبية عامة وتوعوية.

⚠️ قواعد صارمة:
1. لست بديلاً عن الطبيب - دائماً انصح بمراجعة طبيب مختص
2. لا تشخّص الأمراض بشكل قاطع
3. لا تصف أدوية بجرعات محددة
4. في حالات الطوارئ، انصح بالاتصال بالإسعاف فوراً
5. استخدم لغة عربية واضحة ومبسطة
6. اطلب توضيحات إذا كانت الأعراض غير واضحة
"""
"""
🎙️ واجهة Streamlit للمساعد الصوتي العربي
تشغيل: streamlit run app_streamlit.py
"""

import os
import sys
import time
import tempfile
import threading
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai
import base64

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")

# ── إعداد الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="مساعد صوتي عربي",
    page_icon="🎙️",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

* { font-family: 'Cairo', sans-serif !important; }

body { direction: rtl; }

.main { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }

.chat-bubble-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0;
    text-align: right;
    max-width: 80%;
    float: right;
    clear: both;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3);
}

.chat-bubble-ai {
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    text-align: right;
    max-width: 80%;
    float: left;
    clear: both;
    box-shadow: 0 4px 15px rgba(42,82,152,0.3);
}

.clearfix { clear: both; }

.status-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    color: #a0aec0;
    margin: 16px 0;
}

.stButton button {
    width: 100%;
    border-radius: 50px !important;
    padding: 14px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(102,126,234,0.4) !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(102,126,234,0.5) !important;
}
</style>
""", unsafe_allow_html=True)


# ── إعداد Gemini ───────────────────────────────────────────
@st.cache_resource
def load_model():
    api_key = os.getenv("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
    if not api_key or api_key == "":
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


# ── الوظائف ────────────────────────────────────────────────
def recognize_speech_once() -> str:
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 1.5

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            return ""

    try:
        return recognizer.recognize_google(audio, language="ar-EG")
    except (sr.UnknownValueError, sr.RequestError):
        return ""


def get_ai_response(model, user_text: str, history: list) -> str:
    if model is None:
        return "⚠️ محتاج تضيف GEMINI_API_KEY في الإعدادات أو في ملف .env"
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(
            f"أجب بالعربية المصرية بشكل طبيعي ومختصر (مش أكتر من 3 جمل):\n{user_text}"
        )
        reply = response.text.strip()
        history.append({"role": "user", "parts": [user_text]})
        history.append({"role": "model", "parts": [reply]})
        return reply
    except Exception as e:
        return f"❌ خطأ: {str(e)}"


def text_to_speech_autoplay(text: str) -> str:
    """يحول النص لصوت ويرجع HTML يشغله تلقائياً."""
    try:
        tts = gTTS(text=text, lang="ar", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tts.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_bytes = f.read()
        os.remove(tmp.name)
        b64 = base64.b64encode(audio_bytes).decode()
        return f"""
        <audio autoplay style="display:none">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    except Exception as e:
        return ""


# ── الواجهة الرئيسية ───────────────────────────────────────
st.markdown("<h1 style='text-align:center; color:white; margin-bottom:0'>🎙️ مساعد صوتي عربي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#a0aec0; margin-top:4px'>بيسمعك وبيفهمك وبيرد بصوت</p>", unsafe_allow_html=True)
st.divider()

# تهيئة الحالة
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_history" not in st.session_state:
    st.session_state.gemini_history = []
if "status" not in st.session_state:
    st.session_state.status = "جاهز ✅"
if "listening" not in st.session_state:
    st.session_state.listening = False

model = load_model()

# عرض المحادثة
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">🧑 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-ai">🤖 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)

# Status
st.markdown(f'<div class="status-box">الحالة: {st.session_state.status}</div>', unsafe_allow_html=True)

# زرار الميكروفون
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🎤 اضغط وتكلم", disabled=st.session_state.listening):
        st.session_state.listening = True
        st.session_state.status = "🎤 بسمعك... اتكلم!"
        st.rerun()

# لو ضغط الزرار
if st.session_state.listening:
    with st.spinner("🎤 بستنى كلامك..."):
        user_text = recognize_speech_once()

    if user_text:
        st.session_state.status = "🔄 بيفكر في الرد..."
        st.session_state.chat_history.append({"role": "user", "text": user_text})

        with st.spinner("🤖 بيجهز الرد..."):
            reply = get_ai_response(model, user_text, st.session_state.gemini_history)

        st.session_state.chat_history.append({"role": "ai", "text": reply})
        st.session_state.status = "🔊 بيتكلم..."

        # نشغل الصوت
        audio_html = text_to_speech_autoplay(reply)
        if audio_html:
            st.markdown(audio_html, unsafe_allow_html=True)

        st.session_state.status = "جاهز ✅"
    else:
        st.session_state.status = "❌ مسمعتش حاجة، جرب تاني"

    st.session_state.listening = False
    st.rerun()

# زرار مسح المحادثة
st.divider()
if st.button("🗑️ مسح المحادثة"):
    st.session_state.chat_history = []
    st.session_state.gemini_history = []
    st.session_state.status = "جاهز ✅"
    st.rerun()

# إعداد API Key
with st.expander("⚙️ الإعدادات"):
    api_key_input = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    if st.button("حفظ المفتاح") and api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("✅ تم الحفظ! أعد تشغيل الصفحة")
    st.markdown("[احصل على مفتاح مجاني من Google AI Studio](https://aistudio.google.com/app/apikey)")