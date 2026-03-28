import streamlit as st
import psycopg2
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- CONFIG ---
st.set_page_config(page_title="Gov Genie AI", layout="wide")

def run_query(query, params=None):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        with conn.cursor() as cur:
            cur.execute(query, params)
            res = cur.fetchall() if cur.description else None
            conn.commit()
            return res
    except Exception as e:
        return []

# --- AI СОЗЛАМАЛАРИ (ХАТОЛИККА ЧИДАМЛИ) ---
def get_ai_response(prompt):
    genai.configure(api_key=st.secrets["GENAI_API_KEY"])
    # Биринчи 1.5-flash-ни синаб кўрамиз, бўлмаса pro-га ўтамиз
    for model_name in ["gemini-1.5-flash", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except:
            continue
    return "AI билан боғланишда муаммо юз берди. Илтимос, API калитингизни текширинг."

# --- LEX.UZ SCRAPER ---
def fetch_lex_uz(term):
    try:
        url = f"https://lex.uz/search/nat?query={term}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('.lex_list_title a')[:2]
        return "\n".join([f"{l.text.strip()} (https://lex.uz{l.get('href')})" for l in links])
    except:
        return "Янги ҳужжатларни олиш имконсиз."

# --- UI ---
st.title("🧞 Gov Genie AI")

orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {n: i for i, n in orgs}
    c1, c2 = st.columns(2)
    org_name = c1.selectbox("🏢 Ташкилот", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    if roles:
        role_dict = {n: i for i, n in roles}
        role_name = c2.selectbox("👨‍💼 Лавозим", list(role_dict.keys()))
        role_id = role_dict[role_name]

        if st.button("🔄 Lex.uz дан янги қонунларни таҳлил қилиш"):
            with st.spinner("Таҳлил қилинмоқда..."):
                lex_data = fetch_lex_uz(role_name)
                prompt = f"Лавозим: {role_name}. Lex.uz янгиликлари: {lex_data}. Муҳим 2 тасини тушунтир."
                st.success(get_ai_response(prompt))

        st.markdown("---")
        laws = run_query("SELECT title FROM laws l JOIN role_laws rl ON l.id = rl.law_id WHERE rl.role_id=%s", (role_id,))
        tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

        col_a, col_b = st.columns(2)
        with col_a:
            st.info("📜 Базадаги қонунлар:")
            for l in laws: st.write(f"• {l[0]}")
        with col_b:
            st.success("✅ Асосий вазифалар:")
            for t in tasks: st.write(f"• {t[0]}")
