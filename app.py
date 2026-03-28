import streamlit as st
import psycopg2
import google.generativeai as genai

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Streamlit Secrets-дан маълумотларни олиш
GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
DB_URL = st.secrets["DB_URL"]

# AI-ни созлаш
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Базага уланиш функцияси
def run_query(query, params=None):
    conn = psycopg2.connect(DB_URL)
    with conn.cursor() as cur:
        cur.execute(query, params)
        res = cur.fetchall()
        conn.close()
        return res

# ИНТЕРФЕЙС
st.title("🧞 Gov Genie AI")

# Ташкилот ва Лавозимни танлаш
try:
    orgs = run_query("SELECT id, name FROM organizations")
    org_dict = {name: id for id, name in orgs}
    org_name = st.selectbox("🏢 Tashkilot", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    role_dict = {name: id for id, name in roles}
    role_name = st.selectbox("👨‍💼 Lavozim", list(role_dict.keys()))
    role_id = role_dict[role_name]

    # Чат тарихи
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Savolingizни ёзинг...")

    if user_input:
        st.chat_message("user").write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Базадан контекстни олиш
        laws = run_query("SELECT title, simple FROM laws JOIN role_laws ON laws.id = role_laws.law_id WHERE role_id=%s", (role_id,))
        tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

        context = f"Lavozim: {role_name}\nQonunlar: {laws}\nVazifalar: {tasks}\nSavol: {user_input}"
        response = model.generate_content(context)
        
        st.chat_message("assistant").write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
except Exception as e:
    st.error(f"База билан боғланишда хатолик: {e}")
