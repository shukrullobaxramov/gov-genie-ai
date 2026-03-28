import streamlit as st
import psycopg2
import requests
import json
from bs4 import BeautifulSoup
import time

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide", page_icon="🧞")

# --- CUSTOM CSS (Интерфейсни чиройли қилиш учун) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2e7d32; color: white; }
    .stSelectbox { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- БАЗАГА УЛАНИШ ---
@st.cache_resource # Базага уланишни кэшлаш (тезлик учун)
def get_connection():
    try:
        return psycopg2.connect(st.secrets["DB_URL"])
    except Exception as e:
        st.error(f"Базага уланишда хатолик: {e}")
        return None

def run_query(query, params=None):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                res = cur.fetchall() if cur.description else None
                conn.commit()
                return res
        except Exception as e:
            return []
    return []

# --- AI БИЛАН ТЎҒРИДАН-ТЎҒРИ (DIRECT) БОҒЛАНИШ ---
def get_ai_response(prompt):
    api_key = st.secrets["GENAI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.8,
            "topK": 40
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "⚠️ AI ҳозирда жавоб бера олмайди. Кейинроқ қайта уриниб кўринг."
    except Exception:
        return "❌ Тармоқ билан боғланишда хатолик юз берди."

# --- LEX.UZ SCRAPER (МУСТАҲКАМЛАНГАН) ---
def fetch_lex_uz(term):
    try:
        search_url = f"https://lex.uz/search/nat?query={term}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(search_url, headers=headers, timeout=15)
        r.raise_for_status() # Хатолик бўлса истисно кўтаради
        
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('.lex_list_title a')
        
        if not links:
            return "Ҳозирда ушбу лавозимга оид янги қонунчилик ҳужжатлари топилмади."
            
        results = []
        for l in links[:3]: # Энг муҳим 3 тасини оламиз
            title = l.text.strip()
            href = f"https://lex.uz{l.get('href')}"
            results.append(f"🔹 {title}\nМанба: {href}")
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Lex.uz маълумотларини олишда техник узилиш: {str(e)}"

# --- ИНТЕРФЕЙС ---
st.title("🧞 Gov Genie AI")
st.subheader("Давлат хизматчилари учун интеллектуаль ёрдамчи")

orgs = run_query("SELECT id, name FROM organizations")

if orgs:
    org_dict = {n: i for i, n in orgs}
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        org_name = st.selectbox("🏢 Ташкилот / Тизимни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    
    if roles:
        role_dict = {n: i for i, n in roles}
        with col_sel2:
            role_name = st.selectbox("👨‍💼 Лавозимингизни танланг", list(role_dict.keys()))
        
        role_id = role_dict[role_name]

        # Lex.uz таҳлил тугмаси
        if st.button("🔄 Lex.uz дан янги қонунларни таҳлил қилиш"):
            with st.spinner("Lex.uz базаси сканерланмоқда..."):
                lex_data = fetch_lex_uz(role_name)
                
                prompt = f"""Сен Ўзбекистон давлат бошқаруви бўйича экспертсан. 
                Лавозим: {role_name}. 
                Манба: {lex_data}. 
                Вазифа: Юқоридаги маълумотларни таҳлил қилиб, ушбу лавозим эгаси учун энг муҳим 2-3 та ўзгаришни пунктлар билан, содда тилда тушунтириб бер. 
                Агар маълумот топилмаган бўлса, умумий тавсия бер."""
                
                response_text = get_ai_response(prompt)
                st.markdown("### ✨ AI Таҳлили ва Тавсиялар:")
                st.info(response_text)

        st.divider()

        # Маълумотларни иккита блокка ажратиш
        c_left, c_right = st.columns(2)
        
        with c_left:
            with st.expander("📜 Ҳуқуқий асослар (Базадан)", expanded=True):
                laws = run_query("SELECT title FROM laws l JOIN role_laws rl ON l.id = rl.law_id WHERE rl.role_id=%s", (role_id,))
                if laws:
                    for l in laws: st.write(f"📍 {l[0]}")
                else:
                    st.write("Тизимда ҳужжатлар ҳали бириктирилмаган.")
            
        with c_right:
            with st.expander("✅ Функционал вазифалар", expanded=True):
                tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))
                if tasks:
                    for t in tasks: st.write(f"✔️ {t[0]}")
                else:
                    st.write("Вазифалар рўйхати шакллантирилмаган.")
                    
else:
    st.error("❌ Маълумотлар базаси билан алоқа йўқ. Созламаларни текширинг.")

# --- FOOTER ---
st.markdown("---")
st.caption("© 2026 Gov Genie AI - Давлат хизмати самарадорлигини ошириш лойиҳаси")
