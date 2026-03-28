import streamlit as st
import psycopg2
import requests
import json
from bs4 import BeautifulSoup

# 1. САҲИФА СОЗЛАМАЛАРИ
st.set_page_config(
    page_title="Gov Genie AI", 
    layout="wide", 
    page_icon="🧞",
    initial_sidebar_state="expanded"
)

# Визуал услублар (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #007bff; 
        color: white;
        font-weight: bold;
    }
    .stAlert { border-radius: 10px; }
    h1 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 2. МАЪЛУМОТЛАР БАЗАСИ БИЛАН ИШЛАШ
@st.cache_resource
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
        except Exception:
            return []
    return []

# 3. AI БИЛАН БОҒЛАНИШ (ДИАГНОСТИКА БИЛАН)
def get_ai_response(prompt):
    try:
        if "GENAI_API_KEY" not in st.secrets:
            return "❌ Хато: Streamlit secrets ичида 'GENAI_API_KEY' топилмади."
            
        api_key = st.secrets["GENAI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3} # Аниқроқ жавоб учун
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        # API хатоликларини тутиш
        if response.status_code != 200:
            error_msg = result.get('error', {}).get('message', 'Номаълум хатолик')
            return f"❌ API Хатолиги (Status {response.status_code}): {error_msg}"
            
        if 'candidates' in result and len(result['candidates']) > 0:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "⚠️ AI жавоб қайтара олмади. Жавоб тузилиши кутилганидек эмас."
            
    except Exception as e:
        return f"❌ Уланишда техник хатолик: {str(e)}"

# 4. LEX.UZ ПАРСЕР
def fetch_lex_uz(term):
    try:
        search_url = f"https://lex.uz/search/nat?query={term}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(search_url, headers=headers, timeout=15)
        
        if r.status_code != 200:
            return "Lex.uz сайтига боғланишда хатолик."

        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('.lex_list_title a')
        
        if not links:
            return "Янги ҳужжатлар топилмади."
            
        formatted_links = []
        for l in links[:3]: # Энг янги 3 тасини оламиз
            title = l.text.strip()
            url = "https://lex.uz" + l.get('href')
            formatted_links.append(f"- {title} ({url})")
            
        return "\n".join(formatted_links)
    except Exception:
        return "Lex.uz маълумотларини олишда техник узилиш."

# 5. АСОСИЙ ИНТЕРФЕЙС
st.title("🧞 Gov Genie AI")
st.write("Давлат хизматчилари учун ҳуқуқий ва функционал ёрдамчи")

# Ташкилотларни юклаш
orgs = run_query("SELECT id, name FROM organizations")

if orgs:
    org_dict = {n: i for i, n in orgs}
    col1, col2 = st.columns(2)
    
    with col1:
        org_name = st.selectbox("🏢 Ташкилотни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    
    if roles:
        role_dict = {n: i for i, n in roles}
        with col2:
            role_name = st.selectbox("👨‍💼 Лавозимни танланг", list(role_dict.keys()))
        
        role_id = role_dict[role_name]

        # ТАҲЛИЛ ТУГМАСИ
        if st.button("🔄 Lex.uz дан янги қонунларни таҳлил қилиш"):
            with st.spinner("Lex.uz базаси ва СИ таҳлил қилмоқда..."):
                lex_data = fetch_lex_uz(role_name)
                
                # Агар маълумот бўлса, СИга юбориш
                if "топилмади" in lex_data:
                    st.warning(f"'{role_name}' бўйича Lex.uz сайтида янги ҳужжатлар топилмади. Лекин мен умумий тавсия беришим мумкин.")
                    lex_data = "Янги ҳужжатлар йўқ, умумий соҳавий тавсия бер."

                prompt = f"""Сен Ўзбекистон давлат бошқаруви экспертисан. 
                Лавозим: {role_name}. 
                Манба (Lex.uz): {lex_data}. 
                Вазифа: Ушбу лавозим эгаси учун энг муҳим 2-3 та янгилик ёки амалий маслаҳатни пунктлар билан ёзиб бер. Содда ва профессионал ўзбек тилида бўлсин."""
                
                analysis = get_ai_response(prompt)
                st.markdown("### ✨ AI Таҳлили ва Тавсиялар:")
                st.info(analysis)

        st.markdown("---")

        # БАЗАДАГИ МАЪЛУМОТЛАР (КЎРИНИШИ ЯХШИЛАНГАН)
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.markdown("#### 📜 Асосий қонунчилик базаси")
            laws = run_query("SELECT title FROM laws l JOIN role_laws rl ON l.id = rl.law_id WHERE rl.role_id=%s", (role_id,))
            if laws:
                for l in laws: st.markdown(f"✅ {l[0]}")
            else:
                st.write("Маълумот мавжуд эмас.")
            
        with c_right:
            st.markdown("#### ✅ Функционал вазифаларингиз")
            tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))
            if tasks:
                for t in tasks: st.markdown(f"🔹 {t[0]}")
            else:
                st.write("Вазифалар киритилмаган.")
else:
    st.error("❌ Маълумотлар базасига уланиб бўлмади. Streamlit Secrets ичидаги DB_URL ни текширинг.")

# Footer
st.markdown("<br><hr><center>Gov Genie AI © 2026</center>", unsafe_allow_html=True)
