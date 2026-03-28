import streamlit as st
import psycopg2
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Базага уланиш
def run_query(query, params=None):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return None
    except Exception as e:
        return []

# Lex.uz қидируви
def fetch_lex_uz(search_term):
    try:
        search_url = f"https://lex.uz/search/nat?query={search_term}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select('.lex_list_title a')[:3]
            res = [f"{l.text.strip()} (https://lex.uz{l.get('href')})" for l in links]
            return "\n".join(res) if res else "Янги ҳужжат топилмади."
        return "Уланиш хатоси."
    except:
        return "Қидирувда хатолик."

# ИНТЕРФЕЙС
st.title("🧞 Gov Genie AI")

orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {name: id for id, name in orgs}
    col1, col2 = st.columns(2)
    with col1:
        org_name = st.selectbox("🏢 Ташкилот", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    if roles:
        role_dict = {name: id for id, name in roles}
        with col2:
            role_name = st.selectbox("👨‍💼 Лавозим", list(role_dict.keys()))
        
        role_id = role_dict[role_name]

        if st.button("🔄 Lex.uz дан янги қонунларни текшириш"):
            with st.spinner("Таҳлил қилинмоқда..."):
                raw_data = fetch_lex_uz(role_name)
                genai.configure(api_key=st.secrets["GENAI_API_KEY"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"Лавозим: {role_name}. Lex.uz маълумоти: {raw_data}. Энг муҳим 3 та янгиликни тушунтир."
                ai_res = model.generate_content(prompt)
                st.success("✨ Янги таҳлил:")
                st.write(ai_res.text)

        st.markdown("---")
        laws = run_query("SELECT title, simple FROM laws l JOIN role_laws rl ON l.id = rl.law_id WHERE rl.role_id=%s", (role_id,))
        tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

        c_l, c_t = st.columns(2)
        with c_l:
            st.info("📜 Қонунчилик:")
            for law in laws: st.write(f"✅ {law[0]}")
        with c_t:
            st.success("✅ Вазифалар:")
            for task in tasks: st.write(f"🔹 {task[0]}")
