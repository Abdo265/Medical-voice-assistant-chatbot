# app.py — شغّله بـ: streamlit run app.py
import streamlit as st
import json
import re
from sentence_transformers import SentenceTransformer
import chromadb
from deep_translator import GoogleTranslator

# ─── إعدادات الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="Drug Search Assistant",
    page_icon="💊",
    layout="centered"
)

st.title("💊 Drug Search Assistant")
st.caption("اسأل عن أي دواء بالعربي أو الإنجليزي")

# ─── تحميل الموديلات (مرة واحدة بس) ──────────────────────────
@st.cache_resource
def load_resources():
    model = SentenceTransformer("aleynahukmet/bge-medical-small-en-v1.5")
    chroma_client = chromadb.PersistentClient(path="./drug_db")
    collection = chroma_client.get_collection("drugs")
    return model, collection

model, collection = load_resources()

# ─── Helper functions ─────────────────────────────────────────
def is_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_to_english(text: str) -> str:
    if is_arabic(text):
        return GoogleTranslator(source='ar', target='en').translate(text)
    return text

def get_dynamic_n_results(query: str) -> int:
    q = query.lower()
    if any(k in q for k in ["list", "all drugs", "compare", "alternatives", "قائمة", "بدائل", "كل الأدوية"]):
        return 5
    elif any(k in q for k in ["what is", "how does", "dose", "جرعة", "ما هو", "كيف يعمل"]):
        return 2
    return 3

def generate_answer(retrieved_docs: list, retrieved_metas: list) -> list:
    results = []
    for doc, meta in zip(retrieved_docs, retrieved_metas):
        name = meta.get('active_ingredient', meta.get('drug_name', 'Unknown'))
        results.append({"name": name, "doc": doc})
    return results

def search_drugs(query: str):
    original_query = query
    english_query = translate_to_english(query)
    n_results = get_dynamic_n_results(english_query)

    query_embedding = model.encode([english_query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if not docs:
        return None, [], []

    answer = generate_answer(docs, metas)
    return answer, docs, metas

# ─── واجهة المستخدم ────────────────────────────────────────────
query = st.text_input(
    "🔍 اكتب سؤالك هنا:",
    placeholder="e.g. drug for diabetes   أو   ما دواء لعلاج الصرع؟"
)

if st.button("ابحث", type="primary") and query.strip():
    with st.spinner("جاري البحث..."):
        answer, docs, metas = search_drugs(query)

    if not answer:
        st.error("❌ لم يتم العثور على أي دواء مناسب.")
    else:
        st.markdown("### 💊 النتائج")
        for i, item in enumerate(answer, 1):
            with st.expander(f"**{i}. {item['name']}**", expanded=True):
                st.text(item['doc'])
