"""
🎙️ مساعد طبي صوتي - نسخة مستقرة لـ Python 3.14
"""

import os
import sys
import tempfile
import streamlit as st
import requests

# ── إعداد الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="مساعد طبي صوتي",
    page_icon="🩺",
    layout="centered"
)

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl; }
.stApp { background: linear-gradient(160deg, #0d1b2a 0%, #1b2838 60%, #0d2137 100%); }
.chat-user { background: linear-gradient(135deg, #1a6b4a, #2ecc71); color: white; padding: 12px 18px; border-radius: 18px 18px 4px 18px; margin: 6px 0; max-width: 80%; float: right; clear: both; }
.chat-ai { background: linear-gradient(135deg, #1a3a5c, #2980b9); color: white; padding: 12px 18px; border-radius: 18px 18px 18px 4px; margin: 6px 0; max-width: 85%; float: left; clear: both; }
.clearfix { clear: both; margin-bottom: 4px; }
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

# ── الموديلات ──────────────────────────────────────────────
OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
    "openrouter/free"
]

SYSTEM_PROMPT = "أنت مساعد طبي ذكي. قدم نصائح عامة بالعربية وانصح بمراجعة الطبيب."

def get_response(text: str, history: list) -> str:
    api_key = get_openrouter_key()
    if not api_key: return "⚠️ يرجى إضافة مفتاح OpenRouter في الإعدادات."
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history: messages.append(msg)
    messages.append({"role": "user", "content": text})

    for model_name in OPENROUTER_MODELS:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model_name, "messages": messages, "max_tokens": 500},
                timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content")
                    if content and len(content.strip()) > 5:
                        reply = content.strip()
                        history.append({"role": "user", "content": text})
                        history.append({"role": "assistant", "content": reply})
                        st.session_state["active_model"] = model_name
                        return reply
        except: continue
    return "❌ عذراً، جميع الموديلات مشغولة حالياً."

def generate_audio_bytes(text: str):
    xi_key = get_elevenlabs_key()
    # ElevenLabs
    if xi_key:
        try:
            resp = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/IES4nrmZdUBHByLBde0P",
                headers={"xi-api-key": xi_key, "Content-Type": "application/json"},
                json={"text": text, "model_id": "eleven_turbo_v2_5"},
                timeout=10
            )
            if resp.status_code == 200: return resp.content
        except: pass
    
    # gTTS Fallback
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ar")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            with open(f.name, "rb") as audio_file:
                data = audio_file.read()
        os.remove(f.name)
        return data
    except: return None

# ── تهيئة الحالة ───────────────────────────────────────────
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "active_model" not in st.session_state: st.session_state.active_model = OPENROUTER_MODELS[0]

# ── الواجهة ────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;color:white;'>🩺 مساعد طبي صوتي</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:#90caf9;font-size:14px;'>🤖 الموديل: {st.session_state.active_model}</p>", unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">🧑 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai">🩺 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
        if msg.get("audio_data"):
            st.audio(msg["audio_data"], format="audio/mp3", key=f"audio_{i}")

with st.form("input_form", clear_on_submit=True):
    user_input = st.text_input("اكتب سؤالك هنا...", label_visibility="collapsed")
    submitted = st.form_submit_button("📤 إرسال")

if submitted and user_input.strip():
    st.session_state.messages.append({"role": "user", "text": user_input.strip()})
    with st.spinner("جاري الرد..."):
        reply = get_response(user_input.strip(), st.session_state.chat_history)
        audio_data = generate_audio_bytes(reply)
        st.session_state.messages.append({"role": "ai", "text": reply, "audio_data": audio_data})
    st.rerun()

with st.expander("⚙️ الإعدادات"):
    st.session_state["manual_openrouter_key"] = st.text_input("OpenRouter Key", value=st.session_state.get("manual_openrouter_key", ""), type="password")
    st.session_state["manual_elevenlabs_key"] = st.text_input("ElevenLabs Key", value=st.session_state.get("manual_elevenlabs_key", ""), type="password")
    if st.button("🗑️ مسح"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
