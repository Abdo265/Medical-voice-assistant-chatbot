"""
🎙️ مساعد طبي صوتي - ثيم أخضر تيل (Mazzbot Style)
"""

import os, sys, asyncio, tempfile, base64
import streamlit as st
import requests

if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8")

st.set_page_config(
    page_title="مساعد طبي صوتي",
    page_icon="🩺",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
}

.stApp {
    background: #f0faf6;
    direction: rtl;
}

/* ─── Header ─── */
.app-header {
    text-align: center;
    padding: 28px 16px 12px;
}
.app-header .icon {
    font-size: 52px;
    line-height: 1;
    display: block;
    margin-bottom: 8px;
}
.app-header h1 {
    font-size: clamp(22px, 5vw, 32px);
    font-weight: 700;
    color: #065f46;
    margin: 0 0 4px;
}
.app-header p {
    font-size: 14px;
    color: #6b7280;
    margin: 0;
}

/* ─── Chat container ─── */
.chat-container {
    background: white;
    border-radius: 20px;
    padding: clamp(12px, 3vw, 24px);
    margin: 12px 0;
    border: 1px solid #d1fae5;
    min-height: 120px;
    max-height: 55vh;
    overflow-y: auto;
    box-shadow: 0 2px 12px rgba(27,155,117,0.06);
    scroll-behavior: smooth;
}

.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #9ca3af;
    font-size: 14px;
}
.empty-state .empty-icon { font-size: 36px; margin-bottom: 8px; display: block; }

/* ─── Messages ─── */
.msg-row {
    display: flex;
    margin: 10px 0;
    align-items: flex-end;
    gap: 8px;
}
.msg-row.user  { flex-direction: row-reverse; }
.msg-row.ai    { flex-direction: row; }

.msg-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}
.msg-row.user  .msg-avatar { background: #d1fae5; }
.msg-row.ai    .msg-avatar { background: #E1F5EE; }

.msg-bubble {
    padding: 10px 16px;
    border-radius: 18px;
    max-width: min(75%, 460px);
    font-size: clamp(13px, 3.5vw, 15px);
    line-height: 1.7;
    word-break: break-word;
}
.msg-row.user .msg-bubble {
    background: linear-gradient(135deg, #1B9B75, #16856A);
    color: white;
    border-bottom-right-radius: 4px;
}
.msg-row.ai .msg-bubble {
    background: #f0faf6;
    color: #1f2937;
    border: 1px solid #d1fae5;
    border-bottom-left-radius: 4px;
}

/* ─── Status bar ─── */
.status-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 18px;
    background: white;
    border: 1px solid #d1fae5;
    border-radius: 50px;
    font-size: 14px;
    color: #065f46;
    margin: 10px auto;
    width: fit-content;
    max-width: 100%;
    box-shadow: 0 1px 4px rgba(27,155,117,0.08);
}

/* ─── Voice panel ─── */
.voice-panel {
    background: white;
    border: 1px solid #d1fae5;
    border-radius: 16px;
    padding: 16px;
    margin: 12px 0;
    text-align: center;
    box-shadow: 0 1px 6px rgba(27,155,117,0.05);
}

/* ─── Input row ─── */
.stForm > div { gap: 8px !important; }

div[data-testid="stTextInput"] input {
    border-radius: 50px !important;
    border: 1.5px solid #6ee7b7 !important;
    padding: 10px 20px !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 15px !important;
    direction: rtl !important;
    background: white !important;
    color: #1f2937 !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #1B9B75 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(27,155,117,0.12) !important;
}

div[data-testid="stButton"] button {
    border-radius: 50px !important;
    font-family: 'Cairo', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
    border: 1.5px solid #d1fae5 !important;
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(27,155,117,0.15) !important;
}

/* ─── Audio player ─── */
audio {
    width: 100%;
    border-radius: 12px;
    margin-top: 8px;
    height: 44px;
}

/* ─── Expander ─── */
.streamlit-expanderHeader {
    font-family: 'Cairo', sans-serif !important;
    font-weight: 600 !important;
    color: #065f46 !important;
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #d1fae5 !important;
}

/* ─── Footer ─── */
.app-footer {
    text-align: center;
    color: #9ca3af;
    font-size: 12px;
    padding: 16px 0 24px;
    border-top: 1px solid #d1fae5;
    margin-top: 8px;
}

/* ─── Model badge ─── */
.model-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #E1F5EE;
    border: 1px solid #6ee7b7;
    border-radius: 50px;
    padding: 3px 12px;
    font-size: 11px;
    color: #065f46;
    margin: 4px auto 12px;
    font-family: monospace;
}

/* ─── Scrollbar ─── */
.chat-container::-webkit-scrollbar { width: 4px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb {
    background: #6ee7b7;
    border-radius: 4px;
}
.chat-container::-webkit-scrollbar-thumb:hover { background: #34d399; }

/* ─── Divider ─── */
hr {
    border-color: #d1fae5 !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# API Keys
# ══════════════════════════════════════════
def get_openrouter_key() -> str:
    if st.session_state.get("manual_openrouter_key"):
        return st.session_state["manual_openrouter_key"]
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        return os.getenv("OPENROUTER_API_KEY", "")


# ══════════════════════════════════════════
# Models
# ══════════════════════════════════════════
OPENROUTER_MODELS = [
    "openrouter/free",
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-8b:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

SYSTEM_PROMPT = (
    "أنت مساعد طبي ذكي تتكلم عربي مصري بسيط وواضح.\n"
    "مهمتك: تساعد المريض وتطمنه وتنصحه بأدوية معروفة لو محتاج.\n"
    "قواعد مهمة:\n"
    "1. اتكلم بشكل طبيعي زي دكتور بيكلم مريض.\n"
    "2. اذكر أسماء أدوية تجارية مصرية معروفة زي بانادول أو برونيفين أو غيرها.\n"
    "3. متشخصش بشكل قاطع، وانصح دايماً بزيارة الدكتور لو الأعراض مستمرة.\n"
    "4. في الطوارئ، قول للمريض يتصل بالإسعاف فوراً.\n"
    "5. ردودك تكون قصيرة وعملية من 2 لـ 4 جمل بس.\n"
    "6. لا تستخدم نجوم ** أو شرطات أو أي رموز أو تنسيق من أي نوع.\n"
    "7. اكتب الأرقام بالكلام مش بالأرقام، مثلاً اكتب 'حبة واحدة' مش '1'، و'خمسمية ملليجرام' مش '500mg'.\n"
    "8. لا تكتب أي اختصارات أو رموز طبية، اكتب كل حاجة بالكلام الكامل عشان تتقرأ بصوت طبيعي.\n"
    "9. الجمل تكون متوسطة الطول وواضحة، مش قصيرة متقطعة ومش طويلة جداً."
)

# ══════════════════════════════════════════
# LLM
# ══════════════════════════════════════════
def get_response(text: str, history: list) -> str:
    api_key = get_openrouter_key()
    if not api_key:
        return "⚠️ لم يتم تعيين OPENROUTER_API_KEY."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
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
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    reply = content.strip()
                    history.append({"role": "user", "content": text})
                    history.append({"role": "assistant", "content": reply})
                    st.session_state["active_model"] = model_name
                    return reply
            elif resp.status_code in [401, 403]:
                return "❌ خطأ في مفتاح API. تأكد من صحته."
            last_error = f"{model_name}: {resp.status_code}"
        except Exception as e:
            last_error = str(e)
    return f"⚠️ كل الموديلات فشلت.\n({last_error})"


# ══════════════════════════════════════════
# TTS - Edge TTS
# ══════════════════════════════════════════
async def _edge_tts_async(text: str, voice: str) -> bytes:
    import edge_tts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp_path = f.name
    await edge_tts.Communicate(text, voice).save(tmp_path)
    data = open(tmp_path, "rb").read()
    os.remove(tmp_path)
    return data


def text_to_audio_html(text: str) -> str:
    voice = st.session_state.get("tts_voice", "ar-EG-ShakirNeural")
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed(): raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_edge_tts_async(text, voice))
        b64 = base64.b64encode(audio_bytes).decode()
        return (
            '<audio autoplay controls style="width:100%;margin-top:10px;border-radius:12px;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        )
    except ImportError:
        return _gtts_fallback(text)
    except Exception as e:
        st.warning(f"⚠️ Edge TTS: {e}")
        return _gtts_fallback(text)


def _gtts_fallback(text: str) -> str:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="ar", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            data = open(f.name, "rb").read()
        os.remove(f.name)
        b64 = base64.b64encode(data).decode()
        return (
            '<audio autoplay controls style="width:100%;margin-top:10px;border-radius:12px;">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        )
    except Exception as e:
        return f"<p style='color:red'>⚠️ خطأ في الصوت: {e}</p>"


# ══════════════════════════════════════════
# Session init
# ══════════════════════════════════════════
for k, v in [
    ("messages",     []),
    ("chat_history", []),
    ("last_audio",   ""),
    ("status",       "جاهز ✅"),
    ("active_model", OPENROUTER_MODELS[0]),
    ("tts_voice",    "ar-EG-ShakirNeural"),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════
# UI — Header
# ══════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <span class="icon">🩺</span>
  <h1>مساعد طبي صوتي</h1>
  <p>اسأل بصوتك أو اكتب سؤالك الطبي</p>
</div>
""", unsafe_allow_html=True)

mdl = st.session_state["active_model"].split("/")[-1].replace(":free", "")
st.markdown(
    f'<div style="text-align:center"><span class="model-badge">⚡ {mdl}</span></div>',
    unsafe_allow_html=True
)

# ── Chat ──────────────────────────────────
st.markdown('<div class="chat-container" id="chat-box">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
      <span class="empty-icon">💬</span>
      ابدأ بسؤالك الطبي وسأرد عليك فوراً
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-row user">
          <div class="msg-avatar">🧑</div>
          <div class="msg-bubble">{msg["text"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-row ai">
          <div class="msg-avatar">🩺</div>
          <div class="msg-bubble">{msg["text"]}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Audio ─────────────────────────────────
if st.session_state.last_audio:
    st.markdown(st.session_state.last_audio, unsafe_allow_html=True)

# ── Status ────────────────────────────────
st.markdown(
    f'<div class="status-bar">{st.session_state.status}</div>',
    unsafe_allow_html=True
)

# ── Voice input panel ─────────────────────
st.components.v1.html("""
<div style="background:white;border:1px solid #d1fae5;border-radius:16px;
            padding:16px;text-align:center;font-family:'Cairo',sans-serif;
            box-shadow:0 1px 6px rgba(27,155,117,0.05);">

  <p style="margin:0 0 12px;font-size:13px;color:#6b7280;direction:rtl">
    🎤 اضغط الزر، اتكلم، ثم اضغط إرسال
  </p>

  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
    <button id="startBtn" onclick="startListening()"
      style="background:#1B9B75;color:white;border:none;border-radius:50px;
             padding:11px 26px;font-size:15px;font-family:'Cairo',sans-serif;
             font-weight:600;cursor:pointer;transition:all .2s;min-width:130px">
      🎤 ابدأ الكلام
    </button>
    <button id="stopBtn" onclick="stopListening()" disabled
      style="background:#dc2626;color:white;border:none;border-radius:50px;
             padding:11px 26px;font-size:15px;font-family:'Cairo',sans-serif;
             font-weight:600;cursor:pointer;transition:all .2s;min-width:130px;opacity:.4">
      ⏹ وقف
    </button>
  </div>

  <p id="statusTxt"
     style="color:#6b7280;font-size:13px;margin:10px 0 4px;font-family:'Cairo',sans-serif;">
    اضغط ابدأ الكلام
  </p>

  <div id="resultBox"
    style="display:none;background:#f0faf6;border:1px solid #d1fae5;border-radius:12px;
           padding:10px 14px;margin-top:8px;font-size:14px;color:#1f2937;
           text-align:right;direction:rtl;min-height:40px;font-family:'Cairo',sans-serif">
  </div>
</div>

<script>
let rec=null, finalText="";

function startListening(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){document.getElementById('statusTxt').textContent='❌ استخدم Chrome أو Edge';return;}
  rec=new SR(); rec.lang='ar-EG'; rec.continuous=false; rec.interimResults=true;
  setUI(true); finalText="";
  document.getElementById('resultBox').style.display='block';
  document.getElementById('resultBox').textContent='...';
  document.getElementById('statusTxt').textContent='🎤 بسمعك، اتكلم!';
  document.getElementById('statusTxt').style.color='#1B9B75';

  rec.onresult=e=>{
    let interim="";
    for(let i=e.resultIndex;i<e.results.length;i++){
      if(e.results[i].isFinal) finalText+=e.results[i][0].transcript;
      else interim+=e.results[i][0].transcript;
    }
    document.getElementById('resultBox').textContent=finalText||interim;
  };
  rec.onend=()=>{
    setUI(false);
    if(finalText.trim()){
      document.getElementById('statusTxt').textContent='✅ اتسجل! اضغط إرسال';
      document.getElementById('statusTxt').style.color='#F4A621';
      const inp=window.parent.document.querySelector('input[aria-label="speech_result"]');
      if(inp){
        const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
        setter.call(inp,finalText);
        inp.dispatchEvent(new Event('input',{bubbles:true}));
      }
    } else {
      document.getElementById('statusTxt').textContent='❌ مفيش كلام، جرب تاني';
      document.getElementById('statusTxt').style.color='#dc2626';
    }
  };
  rec.onerror=e=>{
    setUI(false);
    document.getElementById('statusTxt').textContent='❌ خطأ: '+e.error;
    document.getElementById('statusTxt').style.color='#dc2626';
  };
  rec.start();
}

function stopListening(){if(rec)rec.stop();}
function setUI(on){
  const s=document.getElementById('startBtn'),p=document.getElementById('stopBtn');
  s.disabled=on; s.style.opacity=on?'.4':'1';
  p.disabled=!on; p.style.opacity=on?'1':'.4';
}
</script>
""", height=200)

# ── Text input ────────────────────────────
with st.form("input_form", clear_on_submit=True):
    c1, c2 = st.columns([5, 1])
    with c1:
        user_input = st.text_input(
            "speech_result",
            placeholder="اكتب سؤالك أو استخدم الميكروفون...",
            label_visibility="collapsed"
        )
    with c2:
        submitted = st.form_submit_button("📤", use_container_width=True)

if submitted and user_input.strip():
    st.session_state.status = "🔄 جاري التفكير..."
    st.session_state.messages.append({"role": "user", "text": user_input.strip()})
    with st.spinner("🩺 جاري الرد..."):
        reply = get_response(user_input.strip(), st.session_state.chat_history)
    st.session_state.messages.append({"role": "ai", "text": reply})
    st.session_state.last_audio = text_to_audio_html(reply)
    st.session_state.status = "🔊 يتكلم..."
    st.rerun()

# ── Action buttons ────────────────────────
st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages     = []
        st.session_state.chat_history = []
        st.session_state.last_audio   = ""
        st.session_state.status       = "جاهز ✅"
        st.rerun()
with c2:
    if st.button("🔕 إيقاف الصوت", use_container_width=True):
        st.session_state.last_audio = ""
        st.rerun()

# ── Settings ──────────────────────────────
with st.expander("⚙️ الإعدادات"):
    st.markdown("#### 🔑 مفاتيح API")
    manual_or = st.text_input(
        "OpenRouter API Key",
        value=st.session_state.get("manual_openrouter_key", ""),
        type="password"
    )
    if manual_or:
        st.session_state["manual_openrouter_key"] = manual_or

    ok = "✅ متصل" if get_openrouter_key() else "❌ غير متصل"
    st.info(f"OpenRouter: {ok}")
    st.markdown("[🔑 احصل على مفتاح مجاني](https://openrouter.ai/keys)")

    st.markdown("---")
    st.markdown("#### 🎙️ اختيار الصوت")
    voice_options = {
        "🇪🇬 مصري - شاكر (رجالي)":    "ar-EG-ShakirNeural",
        "🇪🇬 مصري - سلمى (نسائي)":    "ar-EG-SalmaNeural",
        "🇸🇦 سعودي - حامد (رجالي)":   "ar-SA-HamedNeural",
        "🇸🇦 سعودية - ضارية (نسائي)": "ar-SA-ZariyahNeural",
    }
    sel = st.selectbox("الصوت", list(voice_options.keys()))
    st.session_state["tts_voice"] = voice_options[sel]
    st.success(f"✅ الصوت الحالي: {sel}")

    st.markdown("---")
    st.markdown("#### 🤖 الموديلات")
    for m in OPENROUTER_MODELS:
        active = " ← **نشط**" if m == st.session_state.get("active_model") else ""
        st.markdown(f"- `{m}`{active}")

# ── Footer ────────────────────────────────
st.markdown("""
<div class="app-footer">
  ⚕️ هذا المساعد للمعلومات العامة فقط &nbsp;•&nbsp; يُنصح دائماً بمراجعة الطبيب المختص
</div>
""", unsafe_allow_html=True)
