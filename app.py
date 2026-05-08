"""
🎙️ مساعد طبي صوتي - نسخة مصلحة وشاملة
"""

import os
import sys
import tempfile
import base64
import streamlit as st
import requests

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")

# ── إعداد الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="مساعد طبي صوتي",
    page_icon="🩺",
    layout="centered"
)

# ── CSS محسن ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl; }

.stApp { background: linear-gradient(160deg, #0d1b2a 0%, #1b2838 60%, #0d2137 100%); }

.chat-user {
    background: linear-gradient(135deg, #1a6b4a, #2ecc71);
    color: white; padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 6px 0; max-width: 80%;
    float: right; clear: both;
    box-shadow: 0 4px 15px rgba(46,204,113,0.25);
}
.chat-ai {
    background: linear-gradient(135deg, #1a3a5c, #2980b9);
    color: white; padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px 0; max-width: 85%;
    float: left; clear: both;
    box-shadow: 0 4px 15px rgba(41,128,185,0.25);
}
.clearfix { clear: both; margin-bottom: 4px; }

.status-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px; padding: 14px 20px;
    text-align: center; color: #90caf9;
    font-size: 16px; margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ── إدارة المفاتيح ──────────────────────────────────────────
def get_openrouter_key() -> str:
    if st.session_state.get("manual_openrouter_key"):
        return st.session_state["manual_openrouter_key"]
    try: return st.secrets["OPENROUTER_API_KEY"]
    except: return os.getenv("OPENROUTER_API_KEY", "")

def get_elevenlabs_key() -> str:
    if st.session_state.get("manual_elevenlabs_key"):
        return st.session_state["manual_elevenlabs_key"]
    try: return st.secrets["ELEVENLABS_API_KEY"]
    except: return os.getenv("ELEVENLABS_API_KEY", "")

# ── قائمة الموديلات ────────────────────────────────────────
OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
    "mistralai/mistral-7b-instruct-v0.1:free",
    "openrouter/free"
]

SYSTEM_PROMPT = "أنت مساعد طبي ذكي يتحدث العربية. قدم نصائح عامة وانصح دائماً بمراجعة الطبيب."

# ── وظيفة جلب الرد ──────────────────────────────────────────
def get_response(text: str, history: list) -> str:
    api_key = get_openrouter_key()
    if not api_key:
        return "⚠️ يرجى إضافة OPENROUTER_API_KEY في الإعدادات."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": text})

    last_error = ""
    for model_name in OPENROUTER_MODELS:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model_name, "messages": messages, "max_tokens": 800},
                timeout=25
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    content = choices[0].get("message", {}).get("content")
                    if content:
                        reply = content.strip()
                        history.append({"role": "user", "content": text})
                        history.append({"role": "assistant", "content": reply})
                        st.session_state["active_model"] = model_name
                        return reply
                last_error = f"رد فارغ من {model_name}"
            else:
                last_error = f"خطأ {resp.status_code} من {model_name}"
        except Exception as e:
            last_error = str(e)
            continue
    
    return f"❌ فشل في الحصول على رد: {last_error}"

# ── وظيفة الصوت ────────────────────────────────────────────
def generate_audio_base64(text: str) -> str:
    xi_key = get_elevenlabs_key()
    audio_content = None
    
    # محاولة ElevenLabs أولاً
    if xi_key:
        voice_id = st.session_state.get("el_voice_id", "IES4nrmZdUBHByLBde0P")
        try:
            resp = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key": xi_key, "Content-Type": "application/json"},
                json={"text": text, "model_id": "eleven_turbo_v2_5"},
                timeout=15
            )
            if resp.status_code == 200:
                audio_content = resp.content
            else:
                st.warning(f"ElevenLabs Error: {resp.status_code}")
        except: pass

    # Fallback لـ gTTS
    if not audio_content:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="ar")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts.save(f.name)
                audio_content = open(f.name, "rb").read()
            os.remove(f.name)
        except Exception as e:
            return ""

    if audio_content:
        return base64.b64encode(audio_content).decode()
    return ""

# ── تهيئة الحالة ───────────────────────────────────────────
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "active_model" not in st.session_state: st.session_state.active_model = OPENROUTER_MODELS[0]

# ── الواجهة ────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;color:white;'>🩺 مساعد طبي صوتي</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#90caf9;font-size:14px;'>🤖 الموديل النشط: {st.session_state.active_model}</p>", unsafe_allow_html=True)

# عرض المحادثة
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">🧑 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai">🩺 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
        if msg.get("audio"):
            # استخدام مكون الصوت الرسمي من Streamlit لضمان التوافق
            st.audio(f"data:audio/mp3;base64,{msg['audio']}", format="audio/mp3", autoplay=(i == len(st.session_state.messages)-1))
            # إضافة زر إعادة تشغيل يدوي إذا لزم الأمر
            if st.button(f"▶️ إعادة تشغيل الصوت", key=f"play_{i}"):
                st.audio(f"data:audio/mp3;base64,{msg['audio']}", format="audio/mp3", autoplay=True)

# الإدخال
with st.form("input_form", clear_on_submit=True):
    user_input = st.text_input("اكتب سؤالك هنا...", label_visibility="collapsed")
    submitted = st.form_submit_button("📤 إرسال")

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "text": user_input.strip()})
    with st.spinner("جاري التفكير..."):
        reply = get_response(user_input.strip(), st.session_state.chat_history)
        audio_b64 = generate_audio_base64(reply)
        st.session_state.messages.append({"role": "ai", "text": reply, "audio": audio_b64})
    st.rerun()

# الإعدادات
with st.expander("⚙️ الإعدادات"):
    st.session_state["manual_openrouter_key"] = st.text_input("OpenRouter API Key", value=st.session_state.get("manual_openrouter_key", ""), type="password")
    st.session_state["manual_elevenlabs_key"] = st.text_input("ElevenLabs API Key", value=st.session_state.get("manual_elevenlabs_key", ""), type="password")
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
