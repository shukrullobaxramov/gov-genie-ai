import streamlit as st
import psycopg2
import requests
import json

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Базага уланиш
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

# --- AI БИЛАН ТЎҒРИДАН-ТЎҒРИ БОҒЛАНИШ (ХАТОСИЗ УСУЛ) ---
def get_ai_response_direct(prompt):
    api_key = st.secrets["GENAI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI таҳлил қилишда хатолик юз берди. Илтимос, API калитингизни текширинг."

# Lex.uz қидируви
def fetch_lex_uz(term):
    try:
        from bs4 import BeautifulSoup
        url = f"https://lex.uz/search/nat?query={term}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('.lex_list_title a')[:2]
        return "\n".join([f"{l.text.strip()} (https://lex.uz{l.get('href')})" for l in links])
    except:
        return "Янги ҳужжатларни олиш имконсиз."

# ИНТЕРФЕЙС
st.title("🧞 Gov Genie AI")

orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {n: i for i, n in orgs}
    c1, c2 = st.columns(2)
    org_name = c1.selectbox("🏢 Ташкилотни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    if roles:
        role_dict = {n: i for i, n in roles}
        role_name = c2.selectbox("👨‍💼 Лавозимни танланг", list(role_dict.keys()))
        role_id = role_dict[role_name]

        if st.button("🔄 Lex.uz дан янги қонунларни таҳлил қилиш"):
            with st.spinner("AI таҳлил қилмоқда..."):
                lex_data = fetch_lex_uz(role_name)
                prompt = f"Лавозим: {role_name}. Lex.uz маълумоти: {lex_data}. Муҳим жойларини тушунтир."
                ai_res = get_ai_response_direct(prompt)
                st.success(ai_res)

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
