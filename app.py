"""
🎙️ مساعد طبي صوتي - نسخة محسّنة
✅ Edge TTS  → صوت عربي طبيعي مجاني (Microsoft)
✅ OpenRouter → ردود ذكية مجانية
✅ UI فاتح وأنيق
"""

import os, sys, asyncio, tempfile, base64
import streamlit as st
import requests

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")

# ── إعداد الصفحة ────────────────────────────────────────────
st.set_page_config(
    page_title="مساعد طبي صوتي",
    page_icon="🩺",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

* { font-family: 'Cairo', sans-serif !important; direction: rtl; }

/* خلفية فاتحة */
.stApp {
    background: linear-gradient(160deg, #f0f4f8 0%, #e8f0fe 60%, #f5f5f5 100%);
}

/* بطاقة المحادثة */
.chat-wrap {
    background: white;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    margin-bottom: 16px;
    min-height: 80px;
}

/* رسالة المستخدم */
.chat-user {
    background: linear-gradient(135deg, #1a73e8, #4285f4);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px auto;
    max-width: 78%;
    width: fit-content;
    box-shadow: 0 3px 12px rgba(26,115,232,0.25);
    font-size: 15px;
    line-height: 1.7;
    float: right;
    clear: both;
}

/* رسالة الذكاء الاصطناعي */
.chat-ai {
    background: linear-gradient(135deg, #f8f9fa, #ffffff);
    color: #1a1a2e;
    border: 1.5px solid #e0e7ff;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px auto 8px 0;
    max-width: 82%;
    width: fit-content;
    box-shadow: 0 3px 12px rgba(0,0,0,0.06);
    font-size: 15px;
    line-height: 1.7;
    float: left;
    clear: both;
}

.clearfix { clear: both; margin-bottom: 2px; }

/* بطاقة الحالة */
.status-card {
    background: white;
    border: 1.5px solid #e0e7ff;
    border-radius: 14px;
    padding: 12px 20px;
    text-align: center;
    color: #1a73e8;
    font-size: 15px;
    margin: 10px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* معلومة */
.info-box {
    background: #e8f0fe;
    border-right: 4px solid #1a73e8;
    border-radius: 8px;
    padding: 10px 14px;
    color: #1a3c6e;
    font-size: 14px;
    margin: 8px 0;
}

/* الأزرار */
div[data-testid="stButton"] button {
    border-radius: 50px !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    padding: 10px 24px !important;
    transition: all 0.25s !important;
}

/* عنوان */
h1 { color: #1a1a2e !important; }
p, label { color: #444 !important; }

/* input */
input[type="text"] {
    border-radius: 12px !important;
    border: 1.5px solid #c5cae9 !important;
    font-family: 'Cairo', sans-serif !important;
}

/* divider */
hr { border-color: #e0e0e0 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ── مفاتيح API ───────────────────────────────────────────
# ══════════════════════════════════════════════════════════
def get_openrouter_key() -> str:
    if st.session_state.get("manual_openrouter_key"):
        return st.session_state["manual_openrouter_key"]
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.getenv("OPENROUTER_API_KEY", "")


# ══════════════════════════════════════════════════════════
# ── الموديلات ─────────────────────────────────────────────
# ══════════════════════════════════════════════════════════
OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
    "mistralai/mistral-7b-instruct-v0.1:free",
]

SYSTEM_PROMPT = (
    "أنت مساعد طبي ذكي يتحدث العربية الفصحى البسيطة.\n"
    "مهمتك: تقديم معلومات طبية عامة وتوعوية بأسلوب واضح ومطمئن.\n"
    "⚠️ قواعد صارمة:\n"
    "1. لست بديلاً عن الطبيب - دائماً انصح بمراجعة طبيب مختص.\n"
    "2. لا تشخّص الأمراض بشكل قاطع.\n"
    "3. لا تصف أدوية بجرعات محددة.\n"
    "4. في حالات الطوارئ، انصح بالاتصال بالإسعاف فوراً.\n"
    "5. استخدم لغة عربية واضحة ومبسطة.\n"
    "6. اجعل ردودك موجزة (3-5 جمل) ما لم يطلب المستخدم التفصيل."
)


# ══════════════════════════════════════════════════════════
# ── ردود OpenRouter ───────────────────────────────────────
# ══════════════════════════════════════════════════════════
def get_response(text: str, history: list) -> str:
    api_key = get_openrouter_key()
    if not api_key:
        return "⚠️ لم يتم تعيين OPENROUTER_API_KEY."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # آخر 10 رسائل بس (لتجنب تجاوز token limit)
    messages += history[-10:]
    messages.append({"role": "user", "content": text})

    last_error = ""
    for model_name in OPENROUTER_MODELS:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://medical-assistant.streamlit.app",
                    "X-Title": "Medical Assistant"
                },
                json={"model": model_name, "messages": messages, "max_tokens": 600},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    reply = content.strip()
                    history.append({"role": "user",      "content": text})
                    history.append({"role": "assistant",  "content": reply})
                    st.session_state["active_model"] = model_name
                    return reply
            elif resp.status_code in [401, 403]:
                return "❌ خطأ في مفتاح API. تأكد من صحته."
            last_error = f"{model_name}: {resp.status_code}"
        except Exception as e:
            last_error = str(e)
    return f"⚠️ كل الموديلات وصلت الحد المسموح.\n({last_error})"


# ══════════════════════════════════════════════════════════
# ── Edge TTS (Microsoft) - مجاني وصوت عربي طبيعي ─────────
# ══════════════════════════════════════════════════════════
# الأصوات العربية المتاحة في Edge TTS:
# ar-EG-ShakirNeural   → مصري رجالي ✅
# ar-EG-SalmaNeural    → مصري نسائي
# ar-SA-HamedNeural    → سعودي رجالي
# ar-SA-ZariyahNeural  → سعودي نسائي

async def _edge_tts_async(text: str, voice: str) -> bytes:
    import edge_tts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp_path = f.name
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(tmp_path)
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    os.remove(tmp_path)
    return audio_bytes


def text_to_audio_html(text: str) -> str:
    voice = st.session_state.get("tts_voice", "ar-EG-ShakirNeural")
    try:
        # تشغيل asyncio بشكل آمن في Streamlit
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        audio_bytes = loop.run_until_complete(_edge_tts_async(text, voice))
        b64 = base64.b64encode(audio_bytes).decode()
        return (
            '<audio autoplay controls style="width:100%;margin-top:10px;border-radius:10px;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
            '</audio>'
        )
    except ImportError:
        st.warning("📦 edge-tts مش متنصب. شغّل: pip install edge-tts", icon="⚠️")
        return _gtts_fallback(text)
    except Exception as e:
        st.warning(f"⚠️ Edge TTS: {e} — تم التحويل لـ gTTS")
        return _gtts_fallback(text)


def _gtts_fallback(text: str) -> str:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ar", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            audio_bytes = open(f.name, "rb").read()
        os.remove(f.name)
        b64 = base64.b64encode(audio_bytes).decode()
        return (
            '<audio autoplay controls style="width:100%;margin-top:10px;border-radius:10px;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3">'
            '</audio>'
        )
    except Exception as e:
        return f"<p style='color:red'>⚠️ مشكلة في الصوت: {e}</p>"


# ══════════════════════════════════════════════════════════
# ── الواجهة ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; padding: 10px 0 4px 0'>
  <span style='font-size:48px'>🩺</span>
  <h1 style='margin:4px 0 0 0; font-size:28px; color:#1a1a2e'>مساعد طبي صوتي</h1>
  <p style='color:#666; font-size:14px; margin:4px 0 0 0'>اسأل بصوتك أو اكتب سؤالك الطبي</p>
</div>
""", unsafe_allow_html=True)

# ── تهيئة الحالة ────────────────────────────────────────────
for key, default in [
    ("messages",      []),
    ("chat_history",  []),
    ("last_audio",    ""),
    ("status",        "جاهز ✅"),
    ("active_model",  OPENROUTER_MODELS[0]),
    ("tts_voice",     "ar-EG-ShakirNeural"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── مؤشر الموديل ────────────────────────────────────────────
st.markdown(
    f"<p style='text-align:center;color:#888;font-size:12px;margin:0'>⚡ {st.session_state['active_model']}</p>",
    unsafe_allow_html=True
)

# ── المحادثة ─────────────────────────────────────────────────
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
if not st.session_state.messages:
    st.markdown(
        "<p style='text-align:center;color:#aaa;font-size:14px;padding:20px 0'>ابدأ بسؤالك الطبي 👋</p>",
        unsafe_allow_html=True
    )
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">🧑 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-ai">🩺 {msg["text"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── آخر رد صوتي ─────────────────────────────────────────────
if st.session_state.last_audio:
    st.markdown(st.session_state.last_audio, unsafe_allow_html=True)

# ── الحالة ───────────────────────────────────────────────────
st.markdown(f'<div class="status-card">{st.session_state.status}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# ── الإدخال الصوتي (Web Speech API) ──────────────────────
# ══════════════════════════════════════════════════════════
st.markdown('<div class="info-box">💡 <b>الإدخال الصوتي:</b> اضغط ابدأ الكلام، اتكلم، وبعدين اضغط إرسال</div>', unsafe_allow_html=True)

st.components.v1.html("""
<div style="text-align:center; margin:14px 0; font-family:'Cairo',sans-serif;">
  <button id="startBtn" onclick="startListening()"
    style="background:linear-gradient(135deg,#1a73e8,#4285f4);color:white;
           border:none;border-radius:50px;padding:13px 30px;font-size:16px;
           font-family:'Cairo',sans-serif;font-weight:700;cursor:pointer;
           box-shadow:0 4px 16px rgba(26,115,232,0.35);margin:4px;">
    🎤 ابدأ الكلام
  </button>
  <button id="stopBtn" onclick="stopListening()" disabled
    style="background:linear-gradient(135deg,#c62828,#e53935);color:white;
           border:none;border-radius:50px;padding:13px 30px;font-size:16px;
           font-family:'Cairo',sans-serif;font-weight:700;cursor:pointer;
           box-shadow:0 4px 16px rgba(229,57,53,0.3);margin:4px;opacity:0.45;">
    ⏹ وقف
  </button>
  <p id="statusTxt" style="color:#1a73e8;font-family:'Cairo',sans-serif;font-size:15px;margin-top:10px;">
    اضغط "ابدأ الكلام"
  </p>
  <div id="resultBox"
    style="background:#f8f9fa;border:1.5px solid #c5cae9;border-radius:12px;
           padding:12px;margin-top:10px;min-height:44px;color:#1a1a2e;
           font-family:'Cairo',sans-serif;font-size:16px;text-align:right;
           direction:rtl;display:none;">
  </div>
</div>
<script>
let recognition = null, finalText = "";

function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { document.getElementById('statusTxt').textContent = '❌ استخدم Chrome أو Edge'; return; }
    recognition = new SR();
    recognition.lang = 'ar-EG';
    recognition.continuous = false;
    recognition.interimResults = true;

    setButtons(true);
    document.getElementById('statusTxt').textContent = '🎤 بسمعك... اتكلم!';
    document.getElementById('statusTxt').style.color = '#2e7d32';
    document.getElementById('resultBox').style.display = 'block';
    document.getElementById('resultBox').textContent = '...';
    finalText = "";

    recognition.onresult = (e) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
            else interim += e.results[i][0].transcript;
        }
        document.getElementById('resultBox').textContent = finalText || interim;
    };

    recognition.onend = () => {
        setButtons(false);
        if (finalText.trim()) {
            document.getElementById('statusTxt').textContent = '✅ اتسجل! اضغط إرسال';
            document.getElementById('statusTxt').style.color = '#e65100';
            const inp = window.parent.document.querySelector('input[aria-label="speech_result"]');
            if (inp) {
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(inp, finalText);
                inp.dispatchEvent(new Event('input', { bubbles: true }));
            }
        } else {
            document.getElementById('statusTxt').textContent = '❌ مفيش كلام، جرب تاني';
            document.getElementById('statusTxt').style.color = '#c62828';
        }
    };

    recognition.onerror = (e) => {
        setButtons(false);
        document.getElementById('statusTxt').textContent = '❌ خطأ: ' + e.error;
        document.getElementById('statusTxt').style.color = '#c62828';
    };

    recognition.start();
}

function stopListening() { if (recognition) recognition.stop(); }

function setButtons(recording) {
    document.getElementById('startBtn').disabled = recording;
    document.getElementById('startBtn').style.opacity = recording ? '0.45' : '1';
    document.getElementById('stopBtn').disabled = !recording;
    document.getElementById('stopBtn').style.opacity = recording ? '1' : '0.45';
}
</script>
""", height=210)

# ── إدخال نصي + إرسال ──────────────────────────────────────
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "speech_result",
            placeholder="اكتب سؤالك هنا أو استخدم الميكروفون...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("📤 إرسال", use_container_width=True)

if submitted and user_input.strip():
    st.session_state.status = "🔄 جاري التفكير..."
    st.session_state.messages.append({"role": "user", "text": user_input.strip()})
    with st.spinner("🩺 جاري الرد..."):
        reply = get_response(user_input.strip(), st.session_state.chat_history)
    st.session_state.messages.append({"role": "ai", "text": reply})
    st.session_state.last_audio = text_to_audio_html(reply)
    st.session_state.status = "🔊 يتكلم..."
    st.rerun()

# ── أزرار التحكم ────────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        for k in ["messages", "chat_history", "last_audio"]:
            st.session_state[k] = [] if k != "last_audio" else ""
        st.session_state.status = "جاهز ✅"
        st.rerun()
with col2:
    if st.button("🔕 إيقاف الصوت", use_container_width=True):
        st.session_state.last_audio = ""
        st.rerun()

# ── الإعدادات ───────────────────────────────────────────────
with st.expander("⚙️ الإعدادات"):
    st.markdown("#### 🔑 مفاتيح API")
    manual_or = st.text_input("OpenRouter API Key", value=st.session_state.get("manual_openrouter_key", ""), type="password")
    if manual_or:
        st.session_state["manual_openrouter_key"] = manual_or

    ok = "✅ متصل" if get_openrouter_key() else "❌ مش متصل"
    st.info(f"OpenRouter: {ok}")
    st.markdown("[🔑 احصل على مفتاح مجاني](https://openrouter.ai/keys)")

    st.markdown("---")
    st.markdown("#### 🎙️ الصوت (Edge TTS - مجاني)")

    voice_options = {
        "🇪🇬 مصري - شاكر (رجالي)":     "ar-EG-ShakirNeural",
        "🇪🇬 مصري - سلمى (نسائي)":     "ar-EG-SalmaNeural",
        "🇸🇦 سعودي - حامد (رجالي)":    "ar-SA-HamedNeural",
        "🇸🇦 سعودية - ضارية (نسائي)":  "ar-SA-ZariyahNeural",
    }

    selected = st.selectbox(
        "اختار الصوت",
        list(voice_options.keys()),
        index=0
    )
    st.session_state["tts_voice"] = voice_options[selected]
    st.success(f"✅ الصوت الحالي: {selected}")

    st.markdown("---")
    st.markdown("#### 🤖 الموديلات")
    for m in OPENROUTER_MODELS:
        active = " ← **نشط الآن**" if m == st.session_state.get("active_model") else ""
        st.markdown(f"- `{m}`{active}")

st.markdown("""
<div style='text-align:center;color:#aaa;font-size:12px;margin-top:16px'>
⚕️ هذا المساعد للمعلومات العامة فقط • يُنصح دائماً بمراجعة الطبيب
</div>
""", unsafe_allow_html=True)
