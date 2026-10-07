# 🎙️ Voice Medical Assistant

<div align="center">

**An Arabic voice-powered medical assistant** — a web app built with **Streamlit**

Type your medical question or dictate it by voice, and get an intelligent response — with audio playback in Arabic 🩺

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-6366F1?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

> ⚠️ **Medical Disclaimer**
> This app is for **general informational purposes only** and is **not a substitute for a doctor**, professional diagnosis, or treatment.
> Do not rely on its responses to make medical decisions or delay urgent care. In an emergency, contact your local emergency services immediately.

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🧩 Requirements](#-requirements)
- [🚀 Installation & Launch](#-installation--launch)
- [🔑 Configuring the OpenRouter API Key](#-configuring-the-openrouter-api-key)
- [📖 How to Use](#-how-to-use)
- [🤖 AI Models](#-ai-models)
- [🔊 Voice & Browser Compatibility](#-voice--browser-compatibility)
- [🔒 Security & Privacy](#-security--privacy)
- [🗂️ Project Structure](#️-project-structure)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌍 **Arabic RTL Interface** | Responsive design with full right-to-left support |
| ⌨️🎤 **Dual Input** | Type your question or dictate it in Egyptian Arabic |
| 🤖 **Smart Responses** | Via the **OpenRouter** API with **automatic fallback** across several free models if one fails |
| 🔊 **Arabic TTS** | Converts responses to speech with **Egyptian** or **Saudi** voice options |
| 💬 **Conversation History** | Retained for the current session, with controls to clear it or stop audio |
| ⚙️ **In-App Settings** | Enter your API key and select the voice directly from the app |

---

## 🧩 Requirements

- 🐍 **Python 3.9** or later
- 🌐 Internet access
- 🔑 An API key from [OpenRouter](https://openrouter.ai/keys)
- 🎙️ A browser that supports the **Web Speech API** for voice dictation — **Chrome** or **Edge** recommended

### 📦 Packages Used

```
streamlit    requests    edge-tts    gTTS
```

---

## 🚀 Installation & Launch

Save the app code in a file named `app.py`, then from the project directory create and activate a virtual environment:

**1️⃣ Create the virtual environment**

```bash
python -m venv .venv
```

**2️⃣ Activate it**

```bash
# Linux or macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

**3️⃣ Install dependencies and launch the app**

```bash
pip install streamlit requests edge-tts gTTS
streamlit run app.py
```

> 💡 Streamlit will usually make the app available at `http://localhost:8501`

---

## 🔑 Configuring the OpenRouter API Key

You can provide the key using one of the following methods:

### Option A: Environment Variable

**Linux / macOS:**

```bash
export OPENROUTER_API_KEY="your_api_key_here"
streamlit run app.py
```

**Windows PowerShell:**

```powershell
$env:OPENROUTER_API_KEY="your_api_key_here"
streamlit run app.py
```

### Option B: Streamlit Secrets File

Create `.streamlit/secrets.toml` in the project directory and add:

```toml
OPENROUTER_API_KEY = "your_api_key_here"
```

> 🔒 **Note:** Do not commit this file or your API key to a public repository — add `.streamlit/secrets.toml` to `.gitignore`.

### Option C: From Within the App

You can also enter the key in the app's **Settings** panel. A key entered this way is stored in the current session state only, not in any persistent configuration file.

---

## 📖 How to Use

1. ▶️ Launch the app and open it in your browser
2. ⚙️ Open **Settings** and confirm OpenRouter is connected, or enter your API key there
3. ✍️ Type your question in the input field, or press the 🎤 microphone button and grant the browser microphone access
4. 👀 Review the recognized text after dictation, then press the send button
5. 💬 The response appears as text and an audio player is generated — you can select a different voice in Settings
6. 🧹 Use **Clear conversation** to reset the session, or **Stop audio** to remove the current response player

---

## 🤖 AI Models

The app tries the following models **in sequence** until it obtains a response:

| # | Model |
|---|---|
| 1 | `openrouter/free` |
| 2 | `deepseek/deepseek-chat-v3-0324:free` |
| 3 | `meta-llama/llama-3.3-70b-instruct:free` |
| 4 | `qwen/qwen3-8b:free` |
| 5 | `mistralai/mistral-small-3.1-24b-instruct:free` |

> 📌 Model availability and terms of use on OpenRouter may change over time.

---

## 🔊 Voice & Browser Compatibility

- 🎤 **Voice input** relies on browser support for `SpeechRecognition` / `webkitSpeechRecognition`, using the `ar-EG` locale
- 🔈 **Voice output** uses `edge-tts` first and falls back to `gTTS`
- 🌐 Internet access is required for speech recognition, AI services, and text-to-speech
- 🛠️ If the microphone doesn't work, try **Chrome** or **Edge** and check that the site has microphone permission

---

## 🔒 Security & Privacy

- 🔓 Questions and conversation context are sent to **OpenRouter** to generate responses — avoid entering personally identifying or highly sensitive health information
- 💾 Conversation data is kept in **session state** while the session is active; the code does not define its own persistent storage
- ⚠️ Before making the app publicly available, review how messages are rendered: the code uses `unsafe_allow_html=True` when inserting message text into HTML — **sanitize the text or render it safely** to reduce the risk of HTML/JavaScript injection
- 🗝️ Do not expose your API key in source code or a repository; review secrets and access settings before sharing the app publicly

---

## 🗂️ Project Structure

```
project/
├── app.py                 # Main application code
└── .streamlit/
    └── secrets.toml       # Optional and local only — do not commit to Git ⚠️
```

> 💡 The names above are just an example — use your actual Python filename when running `streamlit run`.

---

<div align="center">

Made with ❤️ to make general medical guidance accessible to everyone

</div>
