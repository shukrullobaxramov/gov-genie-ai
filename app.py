import streamlit as st
import psycopg2
import google.generativeai as genai

# Саҳифа созламалари
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Secrets текшируви
if "GENAI_API_KEY" not in st.secrets or "DB_URL" not in st.secrets:
    st.error("Secrets топилмади! Streamlit Settings > Secrets бўлимига калитларни киритинг.")
    st.stop()

# AI-ни созлаш (Энг барқарор модел: gemini-pro)
genai.configure(api_key=st.secrets["GENAI_API_KEY"])
model = genai.GenerativeModel("gemini-pro")

# Базага уланиш
def run_query(query, params=None):
    try:
        conn = psycopg2.connect(st.secrets["DB_URL"])
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                res = cur.fetchall()
            else:
                conn.commit()
                res = None
        conn.close()
        return res
    except Exception as e:
        st.error(f"База хатолиги: {e}")
        return None

# ИНТЕРФЕЙС
st.title("🧞 Gov Genie AI")

orgs = run_query("SELECT id, name FROM organizations")

if orgs:
    org_dict = {name: id for id, name in orgs}
    org_name = st.selectbox("🏢 Ташкилотни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    
    if roles:
        role_dict = {name: id for id, name in roles}
        role_name = st.selectbox("👨‍💼 Лавозимни танланг", list(role_dict.keys()))
        role_id = role_dict[role_name]

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        user_input = st.chat_input("Саволингизни ёзинг...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Контекст
            laws = run_query("SELECT title, simple FROM laws JOIN role_laws ON laws.id = role_laws.law_id WHERE role_id=%s", (role_id,))
            tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

            prompt = f"Сен давлат хизматчиси ёрдамчисисан. Лавозим: {role_name}. Қонунлар: {laws}. Вазифалар: {tasks}. Савол: {user_input}"

            try:
                # Бу ерда эски кутубхоналарда ҳам ишлайдиган усул ишлатилди
                response = model.generate_content(prompt)
                st.chat_message("assistant").write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as ai_err:
                st.error(f"AI жавоб беришда хатолик: {ai_err}")
