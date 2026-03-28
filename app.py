import streamlit as st
import psycopg2
import requests
import json
from bs4 import BeautifulSoup

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide", page_icon="🧞")

# --- БАЗАГА УЛАНИШ ---
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
def get_ai_response(prompt):
    api_key = st.secrets["GENAI_API_KEY"]
    # Тўғридан-тўғри Google API манзили
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        result = response.json()
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI хатолиги: {result.get('error', {}).get('message', 'Номаълум хатолик')}"
    except Exception as e:
        return f"Тармоқ хатолиги: {str(e)}"

# --- LEX.UZ ҚИДИРУВИ ---
def fetch_lex_uz(term):
    try:
        search_url = f"https://lex.uz/search/nat?query={term}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.select('.lex_list_title a')[:2]
        if links:
            return "\n".join([f"{l.text.strip()} (https://lex.uz{l.get('href')})" for l in links])
        return "Янги ҳужжатлар топилмади."
    except:
        return "Lex.uz билан алоқа боғлаб бўлмади."

# --- ИНТЕРФЕЙС ---
st.title("🧞 Gov Genie AI")

orgs = run_query("SELECT id, name FROM organizations")
if orgs:
    org_dict = {n: i for i, n in orgs}
    c1, c2 = st.columns(2)
    with c1:
        org_name = st.selectbox("🏢 Ташкилотни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    if roles:
        role_dict = {n: i for i, n in roles}
        with c2:
            role_name = st.selectbox("👨‍💼 Лавозимни танланг", list(role_dict.keys()))
        
        role_id = role_dict[role_name]

        # Lex.uz таҳлил тугмаси
        if st.button("🔄 Lex.uz дан янги қонунларни таҳлил қилиш"):
            with st.spinner("Lex.uz дан маълумот олинмоқда ва таҳлил қилинмоқда..."):
                lex_data = fetch_lex_uz(role_name)
                # AI-га вазифа бериш
                prompt = f"""Сен давлат хизматчиси ёрдамчисисан. 
                Лавозим: {role_name}. 
                Lex.uz дан топилган ҳужжатлар: {lex_data}. 
                Ушбу ҳужжатлар ичидан айнан мана шу лавозим эгаси учун энг муҳим бўлган 2 та ўзгаришни қисқача тушунтириб бер."""
                
                response_text = get_ai_response(prompt)
                st.success("✨ Янги таҳлил натижаси:")
                st.write(response_text)

        st.markdown("---")
        # Базадан доимий маълумотларни чиқариш
        laws = run_query("SELECT title FROM laws l JOIN role_laws rl ON l.id = rl.law_id WHERE rl.role_id=%s", (role_id,))
        tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

        col_left, col_right = st.columns(2)
        with col_left:
            st.info("📜 Базадаги асосий қонунлар:")
            if laws:
                for l in laws: st.write(f"• {l[0]}")
            else: st.write("Маълумот йўқ.")
            
        with col_right:
            st.success("✅ Сизнинг асосий вазифаларингиз:")
            if tasks:
                for t in tasks: st.write(f"• {t[0]}")
            else: st.write("Маълумот йўқ.")
