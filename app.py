import streamlit as st
import psycopg2
import google.generativeai as genai

# ======================
# CONFIG & SECRETS
# ======================
st.set_page_config(page_title="Gov Genie AI", layout="wide")

# Secrets-дан маълумотларни олиш
try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    DB_URL = st.secrets["DB_URL"]
except Exception as e:
    st.error("Secrets созланмаган. Streamlit Settings > Secrets бўлимини текширинг.")
    st.stop()

# ======================
# AI CONFIG (МАҲ ИЖРО ТАЛҚИНИ)
# ======================
genai.configure(api_key=GENAI_API_KEY)
# Модель номини энг барқарор версияга ўзгартирдик
model = genai.GenerativeModel("gemini-1.5-flash")

# ======================
# DB FUNCTIONS
# ======================
def run_query(query, params=None):
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute(query, params)
            # SELECT бўлса маълумотни қайтаради, бўлмаса None
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

# ======================
# UI - ИНТЕРФЕЙС
# ======================
st.title("🧞 Gov Genie AI")
st.subheader("Давлат хизматчиси учун интеллектуаль ёрдамчи")

# Маълумотларни базадан юклаш
orgs = run_query("SELECT id, name FROM organizations")

if orgs:
    org_dict = {name: id for id, name in orgs}
    org_name = st.selectbox("🏢 Ташкилотни танланг", list(org_dict.keys()))
    
    roles = run_query("SELECT id, name FROM roles WHERE org_id=%s", (org_dict[org_name],))
    
    if roles:
        role_dict = {name: id for id, name in roles}
        role_name = st.selectbox("👨‍💼 Лавозимни танланг", list(role_dict.keys()))
        role_id = role_dict[role_name]

        # Чат тарихи
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # Фойдаланувчи сўрови
        user_input = st.chat_input("Саволингизни ёзинг (масалан: ПФ-84 бўйича вазифам нима?)...")

        if user_input:
            st.chat_message("user").write(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Контекстни олиш (Қонунлар ва Вазифалар)
            laws = run_query("""
                SELECT l.title, l.simple FROM laws l 
                JOIN role_laws rl ON l.id = rl.law_id 
                WHERE rl.role_id=%s""", (role_id,))
            
            tasks = run_query("SELECT task FROM tasks WHERE role_id=%s", (role_id,))

            # AI учун Промпт (Кечаги мантиқ асосида)
            prompt = f"""
            Сен давлат хизматчиси учун содиқ ёрдамчисан. 
            Фойдаланувчи лавозими: {role_name}
            Ушбу лавозимга тегишли қонунлар: {laws}
            Асосий вазифалар: {tasks}
            
            Савол: {user_input}
            
            Жавобни жуда содда, аниқ ва фақат ўзбек тилида бер. 
            Агар савол қонунчиликка боғлиқ бўлмаса, хушмуомалалик билан фақат соҳавий ёрдам беришингни айт.
            """

            try:
                response = model.generate_content(prompt)
                answer = response.text
                
                st.chat_message("assistant").write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as ai_err:
                st.error(f"AI жавоб беришда хатолик: {ai_err}")
    else:
        st.warning("Ушбу ташкилот учун лавозимлар киритилмаган.")
else:
    st.info("Маълумотлар базаси бўш ёки уланишда муаммо бор. SQL Editor'да маълумот киритганингизни текширинг.")
