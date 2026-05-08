"""
🎙️ مساعد صوتي طبي - يشتغل على Streamlit Cloud
بدون pyaudio أو pygame - الصوت بيشتغل في المتصفح
"""

import os
import sys
import tempfile
import base64
import streamlit as st
import google.generativeai as genai
import requests

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")

# ── إعداد الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="مساعد طبي صوتي",
    page_icon="🩺",
    layout="centered"
)

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
    font-size: 15px; line-height: 1.6;
}
.chat-ai {
    background: linear-gradient(135deg, #1a3a5c, #2980b9);
    color: white; padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px 0; max-width: 85%;
    float: left; clear: both;
    box-shadow: 0 4px 15px rgba(41,128,185,0.25);
    font-size: 15px; line-height: 1.6;
}
.clearfix { clear: both; margin-bottom: 4px; }

.status-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px; padding: 14px 20px;
    text-align: center; color: #90caf9;
    font-size: 16px; margin: 12px 0;
}

.info-box {
    background: rgba(52, 152, 219, 0.12);
    border-right: 4px solid #3498db;
    border-radius: 8px; padding: 12px 16px;
    color: #a8d8f0; font-size: 14px; margin: 8px 0;
}

div[data-testid="stButton"] button {
    border-radius: 50px !important;
    font-size: 17px !important; font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    padding: 12px 28px !important;
    transition: all 0.3s !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ── مفاتيح API (من Secrets فقط - لا تُكتب في الكود) ──────
# ══════════════════════════════════════════════════════════
def get_gemini_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")

def get_elevenlabs_key() -> str:
    try:
        return st.secrets["ELEVENLABS_API_KEY"]
    except Exception:
        return os.getenv("ELEVENLABS_API_KEY", "")


# ══════════════════════════════════════════════════════════
# ── System Prompt الطبي ───────────────────────────────────
# ══════════════════════════════════════════════════════════
SYSTEM_PROMPT = (
    "أنت مساعد طبي ذكي يتحدث العربية الفصحى.\n"
    "مهمتك: تقديم معلومات طبية عامة وتوعوية.\n"
    "⚠️ قواعد صارمة:\n"
    "1. لست بديلاً عن الطبيب - دائماً انصح بمراجعة طبيب مختص\n"
    "2. لا تشخّص الأمراض بشكل قاطع\n"
    "3. لا تصف أدوية بجرعات محددة\n"
    "4. في حالات الطوارئ، انصح بالاتصال بالإسعاف فوراً\n"
    "5. استخدم لغة عربية واضحة ومبسطة\n"
    "6. اطلب توضيحات إذا كانت الأعراض غير واضحة"
)

# ── قائمة موديلات Gemini بالأولوية (fallback تلقائي) ──────
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
]


# ══════════════════════════════════════════════════════════
# ── رد Gemini مع fallback تلقائي للموديلات ───────────────
# ══════════════════════════════════════════════════════════
def get_response(text: str, history: list) -> str:
    api_key = get_gemini_key()
    if not api_key:
        return "⚠️ لم يتم تعيين GEMINI_API_KEY في إعدادات Streamlit Secrets."

    last_error = ""
    for model_name in GEMINI_MODELS:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)
            chat = model.start_chat(history=history)
            resp = chat.send_message(text)
            reply = resp.text.strip()
            history.append({"role": "user",  "parts": [text]})
            history.append({"role": "model", "parts": [reply]})
            st.session_state["active_model"] = model_name   # نحفظ الموديل النشط
            return reply
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "quota", "rate", "RESOURCE_EXHAUSTED"]):
                last_error = f"{model_name}: وصل الحد المسموح"
                continue   # جرّب الموديل التالي
            else:
                return f"❌ خطأ: {e}"

    return f"⚠️ كل الموديلات وصلت الحد المسموح. انتظر دقيقة وحاول تاني.\n({last_error})"


# ══════════════════════════════════════════════════════════
# ── تحويل نص → صوت (ElevenLabs أو gTTS كـ fallback) ──────
# ══════════════════════════════════════════════════════════
def _gtts_fallback(text: str) -> str:
    """يستخدم gTTS لو مفيش ElevenLabs key أو فيه خطأ."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ar", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            audio_bytes = open(f.name, "rb").read()
        os.remove(f.name)
        b64 = base64.b64encode(audio_bytes).decode()
        return (
            '<audio autoplay style="width:100%;margin-top:8px;border-radius:8px;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
            '</audio>'
        )
    except Exception as e:
        return f"<p style='color:orange'>⚠️ مشكلة في الصوت: {e}</p>"


def text_to_audio_html(text: str) -> str:
    xi_key = get_elevenlabs_key()
    if not xi_key:
        return _gtts_fallback(text)

    voice_id = st.session_state.get("el_voice_id", "cgSgspJ2msm6clMCkdW9")
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": xi_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                    "use_speaker_boost": True
                }
            },
            timeout=20
        )
        if resp.status_code == 200:
            b64 = base64.b64encode(resp.content).decode()
            return (
                '<audio autoplay style="width:100%;margin-top:8px;border-radius:8px;">'
                f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
                '</audio>'
            )
        else:
            err_detail = resp.json().get("detail", resp.text)
            st.warning(f"⚠️ ElevenLabs ({resp.status_code}): {err_detail} — بستخدم الصوت الاحتياطي")
            return _gtts_fallback(text)
    except Exception as e:
        return f"<p style='color:orange'>⚠️ مشكلة في الصوت: {e}</p>"


# ══════════════════════════════════════════════════════════
# الواجهة
# ══════════════════════════════════════════════════════════
st.markdown("<h1 style='text-align:center;color:white;margin-bottom:2px'>🩺 مساعد طبي صوتي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#78909c;font-size:14px'>اسأل بصوتك أو اكتب سؤالك الطبي</p>", unsafe_allow_html=True)

# تهيئة الحالة
for key, default in [
    ("messages",       []),
    ("gemini_history", []),
    ("last_audio",     ""),
    ("status",         "جاهز ✅"),
    ("active_model",   GEMINI_MODELS[0]),
    ("el_voice_id",    "cgSgspJ2msm6clMCkdW9"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── مؤشر الموديل النشط ────────────────────────────────────
st.markdown(
    f"<p style='text-align:center;color:#546e7a;font-size:12px;margin:0'>⚡ {st.session_state['active_model']}</p>",
    unsafe_allow_html=True
)

# ── عرض المحادثة ───────────────────────────────────────────
st.markdown("<div style='min-height:50px'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">🧑 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai">🩺 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── آخر رد صوتي ───────────────────────────────────────────
if st.session_state.last_audio:
    st.markdown(st.session_state.last_audio, unsafe_allow_html=True)

# ── الحالة ─────────────────────────────────────────────────
st.markdown(f'<div class="status-card">{st.session_state.status}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# الإدخال الصوتي (Web Speech API)
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="info-box">
💡 <b>الإدخال الصوتي:</b> اضغط الزرار الأخضر، تكلم، وبعدين اضغط "إرسال"
</div>
""", unsafe_allow_html=True)

st.components.v1.html("""
<div style="text-align:center; margin: 16px 0;">
    <button id="startBtn" onclick="startListening()"
        style="background:linear-gradient(135deg,#1a6b4a,#27ae60);color:white;
               border:none;border-radius:50px;padding:14px 32px;font-size:17px;
               font-family:'Cairo',sans-serif;font-weight:700;cursor:pointer;
               box-shadow:0 4px 20px rgba(39,174,96,0.35);margin:4px;">
        🎤 ابدأ الكلام
    </button>
    <button id="stopBtn" onclick="stopListening()" disabled
        style="background:linear-gradient(135deg,#922b21,#e74c3c);color:white;
               border:none;border-radius:50px;padding:14px 32px;font-size:17px;
               font-family:'Cairo',sans-serif;font-weight:700;cursor:pointer;
               box-shadow:0 4px 20px rgba(231,76,60,0.35);margin:4px;opacity:0.5;">
        ⏹ وقف
    </button>
    <p id="statusTxt" style="color:#90caf9;font-family:'Cairo',sans-serif;
       font-size:15px;margin-top:10px;">اضغط "ابدأ الكلام"</p>
    <div id="resultBox" style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.15);
         border-radius:12px;padding:14px;margin-top:12px;min-height:48px;
         color:white;font-family:'Cairo',sans-serif;font-size:16px;
         text-align:right;direction:rtl;display:none;">
    </div>
</div>
<script>
let recognition = null;
let finalText = "";

function startListening() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        document.getElementById('statusTxt').textContent = '❌ استخدم Chrome';
        return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = 'ar-EG';
    recognition.continuous = false;
    recognition.interimResults = true;

    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').style.opacity = '0.5';
    document.getElementById('stopBtn').disabled = false;
    document.getElementById('stopBtn').style.opacity = '1';
    document.getElementById('statusTxt').textContent = '🎤 بسمعك... اتكلم!';
    document.getElementById('statusTxt').style.color = '#2ecc71';
    document.getElementById('resultBox').style.display = 'block';
    document.getElementById('resultBox').textContent = '...';
    finalText = "";

    recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
            else interim += event.results[i][0].transcript;
        }
        document.getElementById('resultBox').textContent = finalText || interim;
    };

    recognition.onend = () => {
        resetButtons();
        if (finalText.trim()) {
            document.getElementById('statusTxt').textContent = '✅ اتسجل! اضغط "إرسال"';
            document.getElementById('statusTxt').style.color = '#f39c12';
            const inp = window.parent.document.querySelector('input[aria-label="speech_result"]');
            if (inp) {
                inp.value = finalText;
                inp.dispatchEvent(new Event('input', { bubbles: true }));
            }
        } else {
            document.getElementById('statusTxt').textContent = '❌ مفيش كلام، جرب تاني';
            document.getElementById('statusTxt').style.color = '#e74c3c';
        }
    };

    recognition.onerror = (e) => {
        resetButtons();
        document.getElementById('statusTxt').textContent = '❌ خطأ: ' + e.error;
        document.getElementById('statusTxt').style.color = '#e74c3c';
    };

    recognition.start();
}

function stopListening() { if (recognition) recognition.stop(); }

function resetButtons() {
    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').style.opacity = '1';
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('stopBtn').style.opacity = '0.5';
}
</script>
""", height=220)

# ── إدخال نصي + إرسال ─────────────────────────────────────
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "speech_result",
            placeholder="اكتب سؤالك هنا أو الصق النص من الميكروفون...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("📤 إرسال", use_container_width=True)

if submitted and user_input.strip():
    st.session_state.status = "🔄 بيفكر في الرد..."
    st.session_state.messages.append({"role": "user", "text": user_input.strip()})

    with st.spinner("🩺 جاري الرد..."):
        reply = get_response(user_input.strip(), st.session_state.gemini_history)

    st.session_state.messages.append({"role": "ai", "text": reply})
    st.session_state.last_audio = text_to_audio_html(reply)
    st.session_state.status = "🔊 بيتكلم..."
    st.rerun()

# ── أزرار أسفل ─────────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages       = []
        st.session_state.gemini_history = []
        st.session_state.last_audio     = ""
        st.session_state.status         = "جاهز ✅"
        st.rerun()
with col2:
    if st.button("🔕 إيقاف الصوت", use_container_width=True):
        st.session_state.last_audio = ""
        st.rerun()

# ── إعدادات ────────────────────────────────────────────────
with st.expander("⚙️ إعدادات"):
    st.markdown("#### 🔑 API Keys — أضفها في Streamlit Secrets")
    st.code(
        'GEMINI_API_KEY = "مفتاحك_هنا"\nELEVENLABS_API_KEY = "مفتاحك_هنا"',
        language="toml"
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("[🔑 Gemini Key مجاني](https://aistudio.google.com/app/apikey)")
        gemini_ok = "✅ متصل" if get_gemini_key() else "❌ مش متصل"
        st.info(f"Gemini: {gemini_ok}")
    with col_b:
        st.markdown("[🎙️ ElevenLabs Key](https://elevenlabs.io/app/settings/api-keys)")
        xi_ok = "✅ متصل" if get_elevenlabs_key() else "⚠️ gTTS (احتياطي)"
        st.info(f"ElevenLabs: {xi_ok}")

    st.markdown("---")
    st.markdown("#### 🎙️ اختار صوت ElevenLabs")
    voices = {
        "Arabic Male (cgSgspJ2)": "cgSgspJ2msm6clMCkdW9",
        "Adam":                   "pNInz6obpgDQGcFmaJgB",
        "Aria":                   "9BWtsMINqrJLrRacOk9x",
        "Custom Voice ID":        "custom"
    }
    selected_voice = st.selectbox("الصوت", list(voices.keys()))
    if selected_voice == "Custom Voice ID":
        custom_id = st.text_input("أدخل Voice ID")
        if custom_id:
            st.session_state["el_voice_id"] = custom_id
    else:
        st.session_state["el_voice_id"] = voices[selected_voice]

    st.markdown("---")
    st.markdown("#### 🤖 الموديلات المتاحة (fallback تلقائي)")
    for m in GEMINI_MODELS:
        active = "← **نشط الآن**" if m == st.session_state.get("active_model") else ""
        st.markdown(f"- `{m}` {active}")
